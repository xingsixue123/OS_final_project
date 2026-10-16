"""PeakBaleen (Track A): the one replaceable block (SCOPE.md §1) -- a single `Policy` subclass.

Copied from harness_eval/src/peakbaleen_policy.py (unchanged semantics) and extended so the dumped instance also
carries, per access, what Baleen's admission GBM sees (read-only computation, nothing is changed in the harness):
  acc_ep/acc_k/acc_ts/acc_w/acc_nch  access -> episode index, index in episode, physical ts, 10-min window, #chunks
  acc_meta (n_acc x 6)               ac.features.toList(with_size=True) = op, namespace, user, offset, offset+size, size
  acc_dyn  (n_acc x 12)              block counts b0..b5 + combined chunk counts c0..c5, computed exactly as
                                     train_ap.BaseAdmissionTrainer.generate_data (per block, per-block hourly buckets,
                                     hrs=6, 3600 s, counts before the access; its chunk-update quirk reproduced);
                                     rows with k >= acc_cutoff (15) are the ones the trainer skips (flag acc_row=0).
Per residency list it
  1. rl.init(**rl_init_kwargs); rl.recompute()                       (as every harness policy)
  2. computes Baleen's own order: score = policies.score_service_time_size_fixed(rl), argsort desc
  3. mode 'baleen': Baleen order (skeleton / baseline); if inst_path is set, dumps the instance on the first call
     mode 'dump'  : dumps the instance, Baleen order
     mode 'solver': dumps the instance, calls the solver CLI (subprocess, solver env), reads back the selected set S
                    (nested order) and emits order = S + remaining episodes in Baleen's order
  4. rl.apply_policy(order, scores=<Baleen's scores>, policy=name)
  5. asserts that the prefix rule `threshold < target_wr` reproduces S exactly (every sort call).
d(e,w), C_w, s_e, B exactly as harness_eval (asserted: sum_w d(e,w) == rl.service_time_saved[e]).
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
HRS = 6
HR = 3600.0


def _cfg():
    p = os.environ.get("HE_POLICY_CONFIG")
    if not p:
        return {"mode": "baleen", "name": "pb3_skeleton"}
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


class _Dyn:
    """Same bucket logic as cachesim.dynamic_features.DynamicFeatures (re-implemented read-only, per block)."""
    __slots__ = ("hist", "tss")

    def __init__(self):
        self.hist = []   # newest first: list of dicts
        self.tss = []

    def update(self, key, ts, weight=1):
        if len(self.hist) == 0 or ts > self.tss[0] + HR:
            self.hist.insert(0, {})
            self.tss.insert(0, ts)
        if len(self.hist) > HRS:
            self.hist.pop()
            self.tss.pop()
        self.hist[0][key] = self.hist[0].get(key, 0) + weight

    def get(self, key):
        f = [h.get(key, 0) for h in self.hist]
        return f + [0] * max(0, HRS - len(self.hist))


def access_arrays(rl, t0, acc_cutoff=15):
    """Per-access arrays incl. the admission trainer's features (train_ap.generate_data logic, 1:1)."""
    eps = rl.residencies
    idx_of = {id(ep): i for i, ep in enumerate(eps)}
    by_block = {}
    for ep in eps:
        by_block.setdefault(ep.key, []).append(ep)
    n_acc = sum(len(ep.accesses) for ep in eps)
    acc_ep = np.zeros(n_acc, np.int32)
    acc_k = np.zeros(n_acc, np.int32)
    acc_ts = np.zeros(n_acc, np.float64)
    acc_nch = np.zeros(n_acc, np.int32)
    acc_c0 = np.zeros(n_acc, np.int32)
    acc_meta = np.zeros((n_acc, 6), np.int64)
    acc_dyn = np.full((n_acc, 12), -1, np.int32)
    acc_row = np.zeros(n_acc, np.int8)
    # position of each episode's accesses in the flat arrays: episodes in rl order, accesses in order
    start = np.zeros(len(eps) + 1, np.int64)
    for i, ep in enumerate(eps):
        start[i + 1] = start[i] + len(ep.accesses)
    for i, ep in enumerate(eps):
        for k, a in enumerate(ep.accesses):
            p = start[i] + k
            acc_ep[p] = i
            acc_k[p] = k
            acc_ts[p] = a.ts
            ch = a.chunks()
            acc_nch[p] = len(ch)
            acc_c0[p] = ch[0] if len(ch) else -1
            acc_meta[p] = a.features.toList(with_size=True)
    for block_id, epses in by_block.items():
        dc, db = _Dyn(), _Dyn()
        last_ts = 0
        epses = sorted(epses, key=lambda x: x.ts_logical[0])
        for eps_ in epses:
            i = idx_of[id(eps_)]
            cts = eps_.accesses[0].ts
            tts = last_ts + 1 + HR
            while tts < min(cts, tts + HR * (HRS + 1)) and last_ts != 0:
                dc.update(-1, tts)
                db.update(-1, tts)
                tts += HR
            dc.update(-1, cts)
            db.update(-1, cts)
            for k, ac in enumerate(eps_.accesses):
                cts = ac.ts
                if acc_cutoff is not None and k >= acc_cutoff:
                    continue
                p = start[i] + k
                b = db.get(block_id if not (type(block_id) != int and len(block_id) == 2) else block_id[0])
                comb = np.zeros(HRS, dtype=int)
                key = None
                for chunk_id in ac.chunks():
                    key = (block_id, chunk_id)
                    comb += np.asarray(dc.get(key))
                acc_dyn[p, :6] = b
                acc_dyn[p, 6:] = comb
                acc_row[p] = 1
                for chunk_id in ac.chunks():
                    dc.update(key, cts)          # frozen trainer updates the last chunk key (reproduced as is)
                db.update(block_id if not (type(block_id) != int and len(block_id) == 2) else block_id[0], cts)
                last_ts = cts
    acc_w = ((acc_ts - t0) // WIN).astype(np.int32)
    return dict(acc_ep=acc_ep, acc_k=acc_k, acc_ts=acc_ts, acc_w=acc_w, acc_nch=acc_nch, acc_c0=acc_c0,
                acc_meta=acc_meta, acc_dyn=acc_dyn, acc_row=acc_row, acc_start=start)


class PolicyPeakBaleen3(policies.Policy):
    def __init__(self, **kwargs):
        self.cfg = _cfg()
        super().__init__(self.cfg.get("name", "pb3"), **kwargs)
        self._sel = None
        self._calls = 0

    @staticmethod
    def _baleen(rl):
        score = policies.score_service_time_size_fixed(rl)
        order = score.argsort()[::-1]
        return score, order

    def _dump(self, rl, base_order, base_score):
        cfg = self.cfg
        target = float(cfg.get("target_wr", self.train_target_wr or 35.599))
        th = rl.th
        B = budget_chunks(th, target)
        t0 = th.start_ts if cfg.get("t0") is None else float(cfg["t0"])
        D, C, active = build_instance(rl, t0, int(cfg.get("skip_windows", 0)))
        s = np.asarray(rl.chunks_written, float)
        idents = [ep_ident(ep) for ep in rl.residencies]
        extra = access_arrays(rl, t0) if cfg.get("dump_access", True) else {}
        inst_path = cfg["inst_path"]
        os.makedirs(os.path.dirname(inst_path), exist_ok=True)
        tmp = inst_path + ".part.npz"
        np.savez_compressed(tmp, D_data=D.data, D_indices=D.indices, D_indptr=D.indptr,
                            D_shape=np.asarray(D.shape), C=C, s=s, B=B, active=active,
                            base_order=np.asarray(base_order), base_score=np.asarray(base_score, float),
                            keys=np.asarray([x[0] for x in idents]), ts0=np.asarray([x[1] for x in idents]),
                            ts_end=np.asarray([float(ep.ts_physical[1]) for ep in rl.residencies]),
                            nchunks=np.asarray([ep.num_chunks for ep in rl.residencies], float),
                            chunk_lo=np.asarray([ep.chunk_range[0] for ep in rl.residencies], np.int32),
                            num_accesses=np.asarray([ep.num_accesses for ep in rl.residencies], np.int32),
                            sts=np.asarray(rl.service_time_saved, float),
                            ea=float(rl.eviction_age_physical),
                            t0=t0, duration=th.duration, target_wr=target, upsample1=th.upsample(1.0),
                            trace_start_ts=float(th.start_ts), trace_end_ts=float(th.end_ts),
                            **extra)
        os.replace(tmp, inst_path)
        return idents

    def _solve(self, rl, base_order, base_score):
        cfg = self.cfg
        idents = self._dump(rl, base_order, base_score)
        if cfg.get("mode") == "dump":
            return None
        sol_path = cfg["sol_path"]
        cmd = [cfg["solver_py"], "-B", cfg["solver_cli"], "--inst", cfg["inst_path"], "--out", sol_path,
               "--cand", cfg["candidate"], "--args", json.dumps(cfg.get("solver_args", {}))]
        print("[PB3] solver:", " ".join(cmd), flush=True)
        t = time.time()
        subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)
        print(f"[PB3] solver done in {time.time() - t:.1f}s", flush=True)
        res = np.load(sol_path)
        return [idents[int(i)] for i in res["order_sel"]]

    def sort_residencies(self, residency_lists):
        for rl in residency_lists.values():
            rl.init(**self.rl_init_kwargs)
            rl.recompute()
            base_score, base_order = self._baleen(rl)
            mode = self.cfg.get("mode", "baleen")
            if mode == "baleen":
                order = base_order
                if self.cfg.get("inst_path") and self._calls == 0:
                    self._dump(rl, base_order, base_score)
            else:
                pos = {ep_ident(ep): i for i, ep in enumerate(rl.residencies)}
                if self._calls == 0:
                    self._sel = self._solve(rl, base_order, base_score)
                    if self._sel is not None:
                        sel_idx = [pos[x] for x in self._sel]
                        in_sel = np.zeros(len(rl.residencies), bool)
                        in_sel[sel_idx] = True
                        order0 = np.r_[np.asarray(sel_idx, dtype=np.int64), base_order[~in_sel[base_order]]]
                        self._order_ids = [ep_ident(rl.residencies[i]) for i in order0]
                if self._sel is None:
                    order = base_order
                else:
                    order = np.asarray([pos[x] for x in self._order_ids], dtype=np.int64)
            self._calls += 1
            rl.apply_policy(order, scores=base_score, policy=self.name)
            if mode != "baleen" and self._sel is not None:
                target = float(self.cfg.get("target_wr", self.train_target_wr or 35.599))
                lab = {ep_ident(ep) for ep in rl.residencies if ep.threshold < target}
                assert lab == set(self._sel), (f"prefix rule does not reproduce the selected set: "
                                               f"|lab|={len(lab)} |sel|={len(self._sel)} sym={len(lab ^ set(self._sel))}")
                print(f"[PB3] call {self._calls}: prefix rule reproduces |S|={len(lab)} exactly", flush=True)
        return residency_lists


def register():
    policies.PolicyPeakBaleen3 = PolicyPeakBaleen3
    return PolicyPeakBaleen3
