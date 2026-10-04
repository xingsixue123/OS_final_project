"""PeakBaleen WP2 Policy (the SCOPE §1 swap block): labels = a PRE-SOLVED core selection on the day-1 instance.

Same slot and semantics as explore/q3/src/pb3_policy.py (copied helpers), except that the selection is read from a
label file instead of calling the solver inside the train (labels.py solves each (instance, design, seed) once on
common/inst/day1_<inst>.npz, which is the day-1 instance every deployed train builds, identical up to episode order).
Per residency list: rl.init(**rl_init_kwargs); rl.recompute(); Baleen score/order (score_service_time_size_fixed);
order = core selection (Baleen rank inside) + every other episode in Baleen order (SCOPE §1: the tail stays in Baleen
order, so the harness label rule `threshold < target` = core + its strict-prefix Baleen fill, computed in-run);
rl.apply_policy(order, scores=Baleen's scores). Asserted at every sort call: every core identity exists in the run, the
label budget B equals the file's, and the label set = core + a strict Baleen-order prefix of the rest.
Config: env HE_POLICY_CONFIG = json {"labels": <npz>, "name": ..., "target_wr": 35.599}.
"""
import json
import os

import numpy as np

from BCacheSim.episodic_analysis import policies


def _cfg():
    with open(os.environ["HE_POLICY_CONFIG"]) as f:
        return json.load(f)


def ep_ident(ep):
    return (str(ep.key), float(ep.ts_physical[0]))


def budget_chunks(th, target_wr):
    """Largest integer chunk count c with th.upsample(c/8)/th.duration < target_wr (the label rule) -- pb3 copy."""
    c = int(np.floor(target_wr * th.duration / th.upsample(1.0) * 8))
    while th.upsample((c + 1) / 8) / th.duration < target_wr:
        c += 1
    while c > 0 and not (th.upsample(c / 8) / th.duration < target_wr):
        c -= 1
    return c


class PolicyPeakBaleen4(policies.Policy):
    def __init__(self, **kwargs):
        self.cfg = _cfg()
        super().__init__(self.cfg.get("name", "pb4"), **kwargs)
        z = np.load(self.cfg["labels"], allow_pickle=False)
        self.core = set(zip([str(k) for k in z["core_keys"]], [float(t) for t in z["core_ts0"]]))
        self.B_file = int(z["B"])
        self._order_ids = None
        self._calls = 0

    def sort_residencies(self, residency_lists):
        target = float(self.cfg.get("target_wr", 35.599))
        for rl in residency_lists.values():
            rl.init(**self.rl_init_kwargs)
            rl.recompute()
            score = policies.score_service_time_size_fixed(rl)
            base_order = score.argsort()[::-1]
            ids = [ep_ident(ep) for ep in rl.residencies]
            pos = {x: i for i, x in enumerate(ids)}
            if self._order_ids is None:
                B = budget_chunks(rl.th, target)
                assert B == self.B_file, f"label budget differs: run {B} vs file {self.B_file}"
                missing = [x for x in self.core if x not in pos]
                assert not missing, f"{len(missing)} core episodes not in this run's day-1 episodes"
                in_core = np.zeros(len(ids), bool)
                in_core[[pos[x] for x in self.core]] = True
                order0 = np.r_[base_order[in_core[base_order]], base_order[~in_core[base_order]]]
                self._order_ids = [ids[i] for i in order0]
            order = np.asarray([pos[x] for x in self._order_ids], dtype=np.int64)
            self._calls += 1
            rl.apply_policy(order, scores=score, policy=self.name)
            lab = {ep_ident(ep) for ep in rl.residencies if ep.threshold < target}
            assert self.core <= lab, "core selection not fully labeled"
            fill = [x for x in self._order_ids[len(self.core):] if x in lab]
            nf = len(fill)
            assert set(self._order_ids[len(self.core):len(self.core) + nf]) == set(fill), "fill is not a strict prefix"
            print(f"[PB4] call {self._calls}: labels = core {len(self.core)} + Baleen-order fill {nf} "
                  f"(|lab|={len(lab)})", flush=True)
        return residency_lists


def register():
    policies.PolicyPeakBaleen4 = PolicyPeakBaleen4
    return PolicyPeakBaleen4
