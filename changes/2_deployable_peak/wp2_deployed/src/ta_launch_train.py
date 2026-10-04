"""Entry module for every Track A training: optional READ-ONLY dump hooks, then the unmodified train.main() of
whichever BCacheSim the cwd provides (work/ = overlay, work_frozen/ = frozen artifact).

If TA_DUMP_DIR is set, after the admission trainer's prep() (rows/df_X/df_Y built, before any GBM training) we pickle
df_X, df_Y and a per-row key (block_id, episode first ts, access index k, access ts); after each prefetch trainer's
prep_data() we pickle its X, Y and the (block_id, first-access ts) of every row. The hooks call the original methods
first and only read attributes afterwards, so the training computation is unchanged. Used identically for the frozen
and overlay runs of gate G1 and for the train/serve parity test.

  cd work && taskset ... bwrap ... $BALEEN_PY -B -m ta_launch_train <train.py args>
"""
import itertools
import os
import pickle

from BCacheSim.episodic_analysis import train, train_ap
from BCacheSim.episodic_analysis import train_prefetcher as tpf

DUMP = os.environ.get("TA_DUMP_DIR")
_CNT = itertools.count()


def _dump(name, obj):
    with open(os.path.join(DUMP, name), "wb") as f:
        pickle.dump(obj, f, protocol=4)
    print(f"[ta_launch_train] dumped {name}", flush=True)


def _ap_keys(tr):
    sorted_eps = {b: sorted(e, key=lambda x: x.ts_logical[0]) for b, e in tr.eps_by_block.items()}
    keys = []
    for row in tr.rows:
        i, j, k = row["id"]
        ep = sorted_eps[row["block_id"]][j]
        keys.append((str(row["block_id"]), float(ep.ts_physical[0]), int(k), float(ep.accesses[k].ts)))
    return keys


_orig_prep = train_ap.BaseAdmissionTrainer.prep


def _prep(self, force=False):
    fresh = self.df_X is None
    _orig_prep(self, force)
    if DUMP and fresh:
        cols = train_ap.subsets(self.df_X)[self.feat_subset] if self.feat_subset else list(self.df_X.columns)
        _dump("admit_prep.pkl", dict(df_X=self.df_X, df_Y=self.df_Y, keys=_ap_keys(self), feat_subset=self.feat_subset,
                                     feat_cols=cols, split_idxes=self.split_idxes))


_orig_prep_data = tpf.PrefetcherTrainer.prep_data


def _prep_data(self, threshold):
    _orig_prep_data(self, threshold)
    if DUMP:
        keys = [(str(ep.key), float(ep.accesses[0].ts)) for ep in self.rl.residencies[:len(self.X)]]
        _dump(f"prefetch_prep_{next(_CNT)}_{type(self).__name__}.pkl",
              dict(X=self.X, Y=self.Y, keys=keys, feat_names=list(self.feat_names), label_names=list(self.label_names)))


if __name__ == "__main__":
    if os.environ.get("TA_DETERMINISTIC") == "1":
        # G1-det only: pin the artifact's one run-to-run nondeterminism source -- episode generation's
        # Pool.imap_unordered (episodes.generate_residencies) -- to the ordered Pool.imap (same results, input order).
        # Applied identically to the frozen and overlay runs; PYTHONHASHSEED is fixed by the caller.
        import multiprocessing.pool
        multiprocessing.pool.Pool.imap_unordered = multiprocessing.pool.Pool.imap
        print("[ta_launch_train] deterministic mode: Pool.imap_unordered -> Pool.imap, PYTHONHASHSEED="
              f"{os.environ.get('PYTHONHASHSEED')}", flush=True)
    if DUMP:
        train_ap.BaseAdmissionTrainer.prep = _prep
        tpf.PrefetcherTrainer.prep_data = _prep_data
    train.main()
