"""WP5 step 2: rolling re-solve variant (models periodic re-labeling under a hard per-solve latency budget).

  taskset -c 0-7 python p2roll.py --insts ... --solver pt --budget 3 --cfg '{...}' --seed 0 --tag ...

Design (fixed before any rolling result was used; documented in RESULTS_dev.md):
  * receding horizon: windows of 6 h (36 ten-minute slots) starting every 3 h (step 18 slots), aligned at the trace
    start; an episode belongs to the slot of its first access (= its admission decision);
  * window k (start s_k) is solved over the episodes whose first access is in [s_k, s_k + 6 h) and the objective
    windows in [s_k, s_k + 6 h) (after day 1); the loads already include the savings of every episode committed
    earlier (spill-over): L_w = C_w - sum_{committed} d(e,w) - sum_{e in window} d(e,w) x_e;
    only the decisions of the FIRST 3 h are committed (the second half is look-ahead and is re-decided by the next
    window, which then sees the spill-over of the committed half); the last window commits everything;
  * budget = cumulative write-rate cap: window k may use B * end_k / duration - (chunks already committed), i.e. by any
    time t the committed writes never exceed the target rate x t (sum over the trace <= B);
  * day-1 windows (no objective windows) commit Baleen's own order (first-half episodes, within the cap at the half's
    end), identical for every method and untimed; every other window = ONE single-level F1 solve
    (min max_w L_w, s.x <= B_k) with the method's tuned configuration under the wall-clock budget T (clock starts
    after the window sub-instance is built), followed by the shared repair (phase-1 q2core, unchanged);
  * no solver state is carried between windows (warm start = the committed loads/budget, identical for all methods);
  * the stitched selection is evaluated on the TRUE full-trace objective (max over all objective windows after day 1
    of L_w, util %); per-window objectives (6-h window peak at solve time) and final per-3-h-segment peaks are logged.
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import scipy.sparse as sp

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)
import q2core as C  # noqa: E402
from q2run import FAMILY, cfg_hash, make_level_solver, warmup  # noqa: E402
from p2run import CoresLock, append_rows, row_key  # noqa: E402

AREA = os.path.dirname(SRC)
BLOCK_WIN = 36            # 6 h of 10-min windows
WIN = 600.0
COLS = ["key", "ts", "phase", "instance", "solver", "family", "cfg_hash", "cfg", "budget", "seed", "block_h",
        "step_h", "n_blocks", "full_peak_util", "full_use", "B", "block_peaks", "block_walls", "block_n", "block_B",
        "block_start", "seg_peaks", "n_over_budget", "max_block_wall", "status", "tag"]


class Mini:
    """instance-like view of one block (interface used by q2core.Sub / nested_solve / the solver modules)."""
    def __init__(self, Da, Ca, s, sts, rank, B, name):
        self.Da = Da.tocsr()
        self.Da.sort_indices()
        self.Ca = np.asarray(Ca, float)
        self.ma = self.Da.shape[1]
        self.s = np.asarray(s, float)
        self.sts = np.asarray(sts, float)
        self.n = self.Da.shape[0]
        self.B = float(B)
        self.rank = np.asarray(rank, np.int64)
        self.name = name
        self.active = np.ones(self.ma, bool)

    def loads(self, x):
        return self.Ca - self.Da.T @ x


def rolling(I, form_spec, solver, cfg, budget, seed, block_win=BLOCK_WIN, step_win=None, log=None):
    z = I.z
    D = I.D.tocsr()                                  # all windows (n x m)
    t0 = float(z["t0"])
    dur = float(z["duration"])
    step_win = step_win or block_win // 2
    w0 = np.floor((z["ts0"] - t0) / WIN).astype(np.int64)
    last_w = int(w0.max())
    act = I.active
    x = np.zeros(I.n)
    committed = np.zeros(I.m)                        # sum of d(e,w) of committed episodes, all windows
    used = 0.0
    rate = I.B / dur
    lsolver = make_level_solver(solver, cfg, seed)
    peaks, walls, ns, Bs, starts = [], [], [], [], []
    form = C.make_form(I, form_spec)
    sk = 0
    while sk <= last_w:
        final = sk + step_win > last_w
        in_win = (w0 >= sk) & (w0 < sk + block_win)
        E = np.flatnonzero(in_win)
        commit_mask = (w0[E] < sk + step_win) if not final else np.ones(len(E), bool)
        end_t = min((sk + block_win) * WIN, dur)
        Bk = max(min(rate * end_t, I.B) - used, 0.0)
        wins = np.arange(sk, min(sk + block_win, I.m))
        wins = wins[act[wins]]
        if len(E) == 0:
            sk += step_win
            continue
        if len(wins) == 0:                           # day 1: Baleen's own order, first-half episodes
            Eh = E[commit_mask]
            Bh = max(min(rate * min((sk + step_win) * WIN, dur), I.B) - used, 0.0)
            order = Eh[np.argsort(I.rank[Eh], kind="stable")]
            cs = np.cumsum(I.s[order])
            kk = int(np.searchsorted(cs, Bh + 1e-9, side="right"))
            sel = order[:kk]
        else:
            Dk = D[E][:, wins]
            Ck = I.C[wins] - committed[wins]
            M = Mini(Dk, Ck, I.s[E], I.sts[E], I.rank[E], Bk, f"{I.name}_w{sk}")
            t = time.time()
            xs, lvl, per = C.nested_solve(M, form, lsolver, float(budget), levels=[1.0], t_start=t, weights=[1.0])
            wall = time.time() - t
            Lk = M.loads(xs)
            peaks.append(float(Lk.max() * C.US))
            walls.append(round(wall, 3))
            ns.append(int(len(E)))
            Bs.append(round(Bk, 1))
            starts.append(int(sk))
            sel = E[(xs > 0.5) & commit_mask]
            if log:
                log(f"  window {sk}: n={len(E)} B={Bk:.0f} peak={peaks[-1]:.3f} wall={wall:.2f}s")
        x[sel] = 1.0
        committed += np.asarray(D[sel].sum(0)).ravel()
        used += float(I.s[sel].sum())
        assert used <= I.B + 1e-6, (sk, used, I.B)
        if final:
            break
        sk += step_win
    L = I.Ca - I.Da.T @ x
    Lfull = I.C - committed
    seg = [float(Lfull[a:a + step_win][act[a:a + step_win]].max() * C.US)
           for a in range(0, I.m, step_win) if act[a:a + step_win].any()]
    return x, dict(full_peak_util=float(L.max() * C.US), full_use=float(I.s @ x), B=I.B, block_peaks=peaks,
                   block_walls=walls, block_n=ns, block_B=Bs, block_start=starts, seg_peaks=seg,
                   n_blocks=len(peaks), n_over_budget=int(sum(w > 1.05 * budget + 0.5 for w in walls)),
                   max_block_wall=float(max(walls) if walls else 0.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insts", nargs="+", required=True)
    ap.add_argument("--solver", required=True)
    ap.add_argument("--budget", type=float, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cfg", default="{}")
    ap.add_argument("--phase", default="roll")
    ap.add_argument("--tag", default="")
    ap.add_argument("--block-win", type=int, default=BLOCK_WIN)
    ap.add_argument("--step-win", type=int, default=BLOCK_WIN // 2)
    ap.add_argument("--out", default=os.path.join(AREA, "results", "rolling.csv"))
    ap.add_argument("--sols", default=os.path.join(AREA, "sols_roll"))
    o = ap.parse_args()
    cfg = json.loads(o.cfg)
    import numba
    numba.set_num_threads(int(cfg.get("threads", 8)))
    form_spec = {"name": "F1"}
    with CoresLock():
        for inst in o.insts:
            I = C.Instance(inst)
            form = C.make_form(I, form_spec)
            warmup(I, form, o.solver, cfg)
            h = cfg_hash(cfg)
            status = "ok"
            try:
                x, info = rolling(I, form_spec, o.solver, cfg, o.budget, o.seed, o.block_win, o.step_win)
            except Exception as ex:  # report failures too
                import traceback
                traceback.print_exc()
                status, x, info = f"error: {ex!r}"[:200], None, {}
            row = dict(key=row_key(o.phase, I.name, o.solver, h, o.budget, o.seed, o.tag + f"_bw{o.block_win}_st{o.step_win}"),
                       ts=time.strftime("%Y-%m-%dT%H:%M:%S"), phase=o.phase, instance=I.name, solver=o.solver,
                       family=FAMILY[o.solver], cfg_hash=h, cfg=json.dumps(cfg, sort_keys=True), budget=o.budget,
                       seed=o.seed, block_h=o.block_win * WIN / 3600, step_h=o.step_win * WIN / 3600, status=status,
                       tag=o.tag)
            for kk, v in info.items():
                row[kk] = json.dumps(v) if isinstance(v, list) else v
            import csv
            import fcntl
            os.makedirs(os.path.dirname(o.out), exist_ok=True)
            with open(o.out + ".lock", "w") as lk:
                fcntl.flock(lk, fcntl.LOCK_EX)
                new = not os.path.exists(o.out) or os.path.getsize(o.out) == 0
                with open(o.out, "a", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=COLS)
                    if new:
                        w.writeheader()
                    w.writerow({c: row.get(c, "") for c in COLS})
            if x is not None and o.sols:
                os.makedirs(o.sols, exist_ok=True)
                np.savez_compressed(os.path.join(o.sols, f"{o.phase}_{I.name}_{o.solver}_{h}_b{o.budget:g}_s{o.seed}"
                                                 f"_bw{o.block_win}.npz"), sel=np.flatnonzero(x > 0.5))
            print("RESULT", json.dumps({k: row.get(k) for k in ["instance", "solver", "budget", "full_peak_util",
                                                              "n_over_budget", "max_block_wall", "status"]}),
                  flush=True)


if __name__ == "__main__":
    main()
