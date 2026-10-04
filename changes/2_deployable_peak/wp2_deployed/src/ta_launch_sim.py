"""Entry module for every Track A simulation: optional READ-ONLY recording hooks, then the unmodified
simulate_ap entry point of whichever BCacheSim the cwd provides.

If TA_RECORD=<path.pkl> is set (train/serve parity test only), we wrap
  * cachesim.sim_features.collect_features (the admission feature vector the simulator builds for every inserted
    chunk; called through the module attribute by QueueCache.collect_features), and
  * CacheSimulator._prefetch_batch + the prefetch model's predict_batch (the feature rows the ML prefetch models see),
and keep, for accesses in the first RECORD_SECS of the trace, one record per (block_id, access ts): the feature
vector returned by the original function. The originals are called unchanged; results are only copied.

  cd work && taskset ... bwrap ... $BALEEN_PY -B -m ta_launch_sim <simulate_ap args>
"""
import atexit
import os
import pickle

from BCacheSim.cachesim import prefetchers, sim_cache, sim_features, simulate_ap

RECORD = os.environ.get("TA_RECORD")
RECORD_SECS = float(os.environ.get("TA_RECORD_SECS", 86400 + 3600))
REC = {"admit": {}, "admit_mismatch": 0, "admit_calls": 0, "pf": {}, "pf_calls": 0, "t0": None}


def _in_window(t):
    if REC["t0"] is None:
        REC["t0"] = t
    return t - REC["t0"] <= RECORD_SECS


_orig_cf = sim_features.collect_features


def _collect_features(cache, key, acc):
    fv = _orig_cf(cache, key, acc)
    t = acc.ts.physical
    if _in_window(t):
        REC["admit_calls"] += 1
        k = (str(key[0]), float(t))
        if k not in REC["admit"]:
            REC["admit"][k] = list(fv)
        elif REC["admit"][k][:6] == list(fv)[:6] and REC["admit"][k][18:] != list(fv)[18:]:
            REC["admit_mismatch"] += 1  # same access, different load/tod part (must never happen)
    return fv


_STASH = []
_orig_pb = sim_cache.CacheSimulator._prefetch_batch
_orig_pred = prefetchers.LearnedRangePrefetcherModel.predict_batch


def _predict_batch(self, features):
    if not _STASH:
        _STASH.append(features.copy())
    return _orig_pred(self, features)


def _prefetch_batch(self, batch_pf, batch):
    _STASH.clear()
    out = _orig_pb(self, batch_pf, batch)
    if _STASH:
        for acc_, row in zip(batch_pf, _STASH[0]):
            t = acc_.ts.physical
            if _in_window(t):
                REC["pf_calls"] += 1
                REC["pf"].setdefault((str(acc_.block_id), float(t)), row.tolist())
    return out


def _save():
    with open(RECORD, "wb") as f:
        pickle.dump(REC, f, protocol=4)
    print(f"[ta_launch_sim] recorded {len(REC['admit'])} admit / {len(REC['pf'])} prefetch accesses -> {RECORD}")


if __name__ == "__main__":
    if RECORD:
        sim_features.collect_features = _collect_features
        sim_cache.CacheSimulator._prefetch_batch = _prefetch_batch
        prefetchers.LearnedRangePrefetcherModel.predict_batch = _predict_batch
        atexit.register(_save)
    sim_cache.simulate_cache_driver(simulate_ap.get_parsed_args())
