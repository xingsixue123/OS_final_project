"""Track B's one replaceable block (SCOPE.md §1): a single `Policy` subclass, copied from
harness_eval/src/peakbaleen_policy.py (same d(e,w)/C_w construction, same budget rule, same identity-fixed order and
prefix-rule assertion) with one change of mode:

  mode 'baleen'  : Baleen's own order (skeleton / reference), optional instance dump
  mode 'dump'    : dump the instance (npz, harness format) and emit Baleen's order
  mode 'replay'  : emit a selection computed OFFLINE by the Track-B solver runner (q2run.py, timed on cores 0-7):
                   the solution file lists the selected episodes in nested order by identity (block key, first ts);
                   order = selection (nested) + the remaining episodes in Baleen's order of this call; the instance of
                   this run is dumped next to it and must match the solved instance (identities, s_e, sts_e).
The class never modifies episodes / residency lists except through rl.apply_policy.
"""
import json
import os

import numpy as np

from BCacheSim.episodic_analysis import policies
from BCacheSim.episodic_analysis.episodes import service_time

WIN = 600.0


def _cfg():
    p = os.environ.get("Q2_POLICY_CONFIG")
    if not p:
        return {"mode": "baleen", "name": "q2_skeleton"}
    with open(p) as f:
        return json.load(f)


def ep_ident(ep):
    return (str(ep.key), float(ep.ts_physical[0]))


def budget_chunks(th, target_wr):
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
        for k, a in enumerate(ep.accesses):
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


class PolicyQ2(policies.Policy):
    def __init__(self, **kwargs):
        self.cfg = _cfg()
        super().__init__(self.cfg.get("name", "q2"), **kwargs)
        self._order_ids = None
        self._sel = None
        self._calls = 0

    @staticmethod
    def _baleen(rl):
        score = policies.score_service_time_size_fixed(rl)
        order = score.argsort()[::-1]
        return score, order

    def _dump(self, rl, base_order, base_score, path):
        cfg = self.cfg
        target = float(cfg.get("target_wr", self.train_target_wr or 35.599))
        th = rl.th
        B = budget_chunks(th, target)
        t0 = th.start_ts
        D, C, active = build_instance(rl, t0, int(cfg.get("skip_windows", 0)))
        s = np.asarray(rl.chunks_written, float)
        idents = [ep_ident(ep) for ep in rl.residencies]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        np.savez_compressed(path, D_data=D.data, D_indices=D.indices, D_indptr=D.indptr,
                            D_shape=np.asarray(D.shape), C=C, s=s, B=B, active=active,
                            base_order=np.asarray(base_order), base_score=np.asarray(base_score, float),
                            keys=np.asarray([x[0] for x in idents]), ts0=np.asarray([x[1] for x in idents]),
                            ts_end=np.asarray([float(ep.ts_physical[1]) for ep in rl.residencies]),
                            nchunks=np.asarray([ep.num_chunks for ep in rl.residencies], float),
                            ea=float(rl.eviction_age_physical), t0=t0, duration=th.duration, target_wr=target,
                            upsample1=th.upsample(1.0))
        return idents, s, np.asarray(D.sum(1)).ravel(), B

    def sort_residencies(self, residency_lists):
        for rl in residency_lists.values():
            rl.init(**self.rl_init_kwargs)
            rl.recompute()
            base_score, base_order = self._baleen(rl)
            mode = self.cfg.get("mode", "baleen")
            if mode in ("baleen", "dump"):
                order = base_order
                if mode == "dump" and self._calls == 0:
                    self._dump(rl, base_order, base_score, self.cfg["inst_path"])
            else:
                pos = {ep_ident(ep): i for i, ep in enumerate(rl.residencies)}
                if self._order_ids is None:
                    idents, s, sts, B = self._dump(rl, base_order, base_score, self.cfg["inst_path"])
                    sol = np.load(self.cfg["sol_path"], allow_pickle=False)
                    sel = list(zip([str(k) for k in sol["keys"]], [float(t) for t in sol["ts0"]]))
                    missing = [x for x in sel if x not in pos]
                    assert not missing, f"{len(missing)} selected episodes not found in this run"
                    # consistency with the solved instance: s_e and sts_e by identity
                    ref = np.load(self.cfg["solved_inst"], allow_pickle=False)
                    rid = {(str(k), float(t)): i for i, (k, t) in enumerate(zip(ref["keys"], ref["ts0"]))}
                    import scipy.sparse as sp
                    Dr = sp.csr_matrix((ref["D_data"], ref["D_indices"], ref["D_indptr"]), shape=tuple(ref["D_shape"]))
                    rsts = np.asarray(Dr.sum(1)).ravel()
                    assert len(rid) == len(idents) and float(ref["B"]) == float(B), "instance size / budget mismatch"
                    ii = np.array([rid[x] for x in idents])
                    assert np.allclose(ref["s"][ii], s) and np.allclose(rsts[ii], sts, rtol=1e-9, atol=1e-9), \
                        "episode data differ from the solved instance"
                    sel_idx = [pos[x] for x in sel]
                    in_sel = np.zeros(len(rl.residencies), bool)
                    in_sel[sel_idx] = True
                    order0 = np.r_[np.asarray(sel_idx, dtype=np.int64), base_order[~in_sel[base_order]]]
                    self._order_ids = [ep_ident(rl.residencies[i]) for i in order0]
                    self._sel = set(sel)
                    print(f"[PolicyQ2] replay {self.cfg['sol_path']}: |S|={len(sel)} matched the solved instance",
                          flush=True)
                order = np.asarray([pos[x] for x in self._order_ids], dtype=np.int64)
            self._calls += 1
            rl.apply_policy(order, scores=base_score, policy=self.name)
            if mode == "replay":
                target = float(self.cfg.get("target_wr", self.train_target_wr or 35.599))
                lab = {ep_ident(ep) for ep in rl.residencies if ep.threshold < target}
                assert lab == self._sel, (f"prefix rule does not reproduce the selected set: |lab|={len(lab)} "
                                          f"|sel|={len(self._sel)} sym={len(lab ^ self._sel)}")
                print(f"[PolicyQ2] call {self._calls}: prefix rule reproduces |S|={len(lab)} exactly", flush=True)
        return residency_lists


def register():
    policies.PolicyQ2 = PolicyQ2
    return PolicyQ2
