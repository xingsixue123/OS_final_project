"""PeakBaleen: the one replaceable block (SCOPE.md §1) -- a single `Policy` subclass.

Runs inside the unmodified Baleen harness (Baleen env). Per residency list it
  1. rl.init(**rl_init_kwargs); rl.recompute()                       (as every harness policy)
  2. computes Baleen's own order: score = service_time_saved / chunks_written, order = argsort[::-1]
     (identical code path to PolicyUtilityServiceTimeSize2)
  3. mode 'baleen': order = Baleen order (skeleton / R0 reference)
     mode 'solver': builds the peak instance from the harness's episodes (D sparse = d(e,w),
     C_w, s_e = rl.chunks_written, budget B in the harness's own units), dumps it to an .npz,
     calls the solver CLI in the solver env (subprocess), reads back the selected set S in a nested
     order, and emits order = S (nested) + remaining episodes in Baleen order.
  4. rl.apply_policy(order, scores=<Baleen's scores>, policy=name)
  5. asserts that the prefix rule `threshold < target_wr` reproduces S exactly.

d(e,w) (filter_=prefetch episode model, identical to the harness's service_time_saved__prefetch):
  admitted episode e = whole chunk range fetched at its first access (1 IO, num_chunks chunks),
  every later access a hit;  not admitted = every access a miss costing service_time(1, chunks(a)).
  d(e, w(a_1)) += service_time(1, c(a_1)) - service_time(1, N_e);  d(e, w(a_k)) += service_time(1, c(a_k)), k>=2
  where w(a) = floor((a.ts - trace_start_ts) / 600), service_time = the artifact's own function
  (episodic_analysis.episodes.service_time). Sum_w d(e,w) == rl.service_time_saved[e] is asserted.
  C_w = sum over all GET accesses in w of service_time(1, c(a))  (== simulator service_time_nocache).
The class never modifies episodes / residency lists except through rl.apply_policy.
"""
import json
import os
import subprocess
import sys
import time

import numpy as np

from BCacheSim.episodic_analysis import policies
from BCacheSim.episodic_analysis.episodes import service_time

WIN = 600.0


def _cfg():
    p = os.environ.get("HE_POLICY_CONFIG")
    if not p:
        return {"mode": "baleen", "name": "peakbaleen_skeleton"}
    with open(p) as f:
        return json.load(f)


def ep_ident(ep):
    return (str(ep.key), float(ep.ts_physical[0]))


def budget_chunks(th, target_wr):
    """Largest integer chunk count c with th.upsample(c/8)/th.duration < target_wr (the label rule)."""
    c = int(np.floor(target_wr * th.duration / th.upsample(1.0) * 8))
    while th.upsample((c + 1) / 8) / th.duration < target_wr:
        c += 1
    while c > 0 and not (th.upsample(c / 8) / th.duration < target_wr):
        c -= 1
    return c


def build_instance(rl, t0, skip_windows):
    import scipy.sparse as sp
    eps = rl.residencies
    n = len(eps)
    th = rl.th
    m = int((th.end_ts - t0) // WIN) + 1
    rows, cols, vals = [], [], []
    C = np.zeros(m)
    for i, ep in enumerate(eps):
        accs = ep.accesses
        for k, a in enumerate(accs):
            w = int((a.ts - t0) // WIN)
            c = a.num_chunks()
            st = service_time(1, c)
            C[w] += st
            v = st - service_time(1, ep.num_chunks) if k == 0 else st
            rows.append(i)
            cols.append(w)
            vals.append(v)
    D = sp.csr_matrix((np.asarray(vals), (np.asarray(rows), np.asarray(cols))), shape=(n, m))
    D.sum_duplicates()
    sts = np.asarray(rl.service_time_saved, float)
    dsum = np.asarray(D.sum(1)).ravel()
    err = np.abs(dsum - sts).max()
    assert err < 1e-6 * max(1.0, np.abs(sts).max()), f"d(e,w) does not sum to service_time_saved: {err}"
    active = np.zeros(m, bool)
    active[skip_windows:] = True
    return D, C, active


class PolicyPeakBaleen(policies.Policy):
    def __init__(self, **kwargs):
        self.cfg = _cfg()
        super().__init__(self.cfg.get("name", "peakbaleen"), **kwargs)
        self._sel = None          # selected episode identities in nested order (cached across calls)
        self._calls = 0

    # Baleen's own score and order (PolicyUtilityServiceTimeSize2 / score_service_time_size_fixed)
    @staticmethod
    def _baleen(rl):
        score = policies.score_service_time_size_fixed(rl)
        order = score.argsort()[::-1]
        return score, order

    def _solve(self, rl, base_order, base_score):
        cfg = self.cfg
        target = float(cfg.get("target_wr", self.train_target_wr or 35.599))
        th = rl.th
        B = budget_chunks(th, target)
        t0 = th.start_ts if cfg.get("t0") is None else float(cfg["t0"])
        D, C, active = build_instance(rl, t0, int(cfg.get("skip_windows", 0)))
        s = np.asarray(rl.chunks_written, float)
        idents = [ep_ident(ep) for ep in rl.residencies]
        inst_path = cfg["inst_path"]
        os.makedirs(os.path.dirname(inst_path), exist_ok=True)
        np.savez_compressed(inst_path, D_data=D.data, D_indices=D.indices, D_indptr=D.indptr,
                            D_shape=np.asarray(D.shape), C=C, s=s, B=B, active=active,
                            base_order=np.asarray(base_order), base_score=np.asarray(base_score, float),
                            keys=np.asarray([x[0] for x in idents]), ts0=np.asarray([x[1] for x in idents]),
                            ts_end=np.asarray([float(ep.ts_physical[1]) for ep in rl.residencies]),
                            nchunks=np.asarray([ep.num_chunks for ep in rl.residencies], float),
                            ea=float(rl.eviction_age_physical),
                            t0=t0, duration=th.duration, target_wr=target,
                            upsample1=th.upsample(1.0))
        if cfg.get("mode") == "dump":
            return None
        sol_path = cfg["sol_path"]
        cmd = [cfg["solver_py"], "-B", cfg["solver_cli"], "--inst", inst_path, "--out", sol_path,
               "--cand", cfg["candidate"], "--args", json.dumps(cfg.get("solver_args", {}))]
        print("[PeakBaleen] solver:", " ".join(cmd), flush=True)
        t = time.time()
        subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)
        print(f"[PeakBaleen] solver done in {time.time() - t:.1f}s", flush=True)
        res = np.load(sol_path)
        sel_idx = [int(i) for i in res["order_sel"]]
        sel = [idents[i] for i in sel_idx]
        return sel

    def sort_residencies(self, residency_lists):
        for rl in residency_lists.values():
            rl.init(**self.rl_init_kwargs)
            rl.recompute()
            base_score, base_order = self._baleen(rl)
            mode = self.cfg.get("mode", "baleen")
            if mode in ("baleen",):
                order = base_order
                if self.cfg.get("inst_path") and self._calls == 0:
                    self.cfg_dump(rl, base_order, base_score)
            else:
                pos = {ep_ident(ep): i for i, ep in enumerate(rl.residencies)}
                if self._sel is None:
                    self._sel = self._solve(rl, base_order, base_score)
                    if self._sel is not None:
                        # Fix the complete order (S nested, then the rest in Baleen's order of THIS call) by
                        # episode identity, so that later sort calls (train.py re-sorts up to 3x; numpy's
                        # argsort breaks score ties by input position) emit exactly the same order.
                        sel_idx = [pos[x] for x in self._sel]
                        in_sel = np.zeros(len(rl.residencies), bool)
                        in_sel[sel_idx] = True
                        order0 = np.r_[np.asarray(sel_idx, dtype=np.int64), base_order[~in_sel[base_order]]]
                        self._order_ids = [ep_ident(rl.residencies[i]) for i in order0]
                if self._sel is None:   # dump-only
                    order = base_order
                else:
                    order = np.asarray([pos[x] for x in self._order_ids], dtype=np.int64)
            self._calls += 1
            rl.apply_policy(order, scores=base_score, policy=self.name)
            if mode not in ("baleen",) and self._sel is not None:
                target = float(self.cfg.get("target_wr", self.train_target_wr or 35.599))
                lab = {ep_ident(ep) for ep in rl.residencies if ep.threshold < target}
                assert lab == set(self._sel), (f"prefix rule does not reproduce the selected set: "
                                               f"|lab|={len(lab)} |sel|={len(self._sel)} "
                                               f"sym={len(lab ^ set(self._sel))}")
                print(f"[PeakBaleen] call {self._calls}: prefix rule reproduces |S|={len(lab)} exactly", flush=True)
        return residency_lists

    def cfg_dump(self, rl, base_order, base_score):
        """Dump the instance (for gate-0 / analytic evaluation) without changing the order."""
        cfg = dict(self.cfg)
        cfg["mode"] = "dump"
        old = self.cfg
        self.cfg = cfg
        try:
            self._solve(rl, base_order, base_score)
        finally:
            self.cfg = old


def register():
    policies.PolicyPeakBaleen = PolicyPeakBaleen
    return PolicyPeakBaleen
