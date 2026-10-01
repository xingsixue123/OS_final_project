"""G1 model-file replay: retrain the GBMs from ONE fixed set of prepared training data (a ta_launch_train dump: rows,
row order, train/test split), with whichever BCacheSim the cwd provides (frozen or overlay), and save the model files.

Training through train.py is not deterministic run-to-run in the frozen artifact itself (episode generation uses an
8-worker imap_unordered, so row order and the block-level train/test split change between runs). This replay removes
that source: the trainer methods of the code under test (GBAdmissionTrainer.train_all/save, PrefetcherConfTrainer's
split/train/splice) run on identical inputs, so frozen and overlay must produce byte-identical model files.

  cd work[_frozen] && taskset ... bwrap ... $BALEEN_PY -B ../src/g1_replay.py <dump_dir> <out_dir>   (under the train lock)
"""
import glob
import os
import pickle
import sys

from BCacheSim.episodic_analysis import train_ap
from BCacheSim.episodic_analysis import train_prefetcher as tpf


def main():
    dump, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    # admission GBM (train.py: AdmissionTrainer(labels=['threshold_binary']).train_all())
    D = pickle.load(open(os.path.join(dump, "admit_prep.pkl"), "rb"))
    tr = object.__new__(train_ap.GBAdmissionTrainer)
    tr.init_config()
    tr.clfs = {}
    tr.labels = ["threshold_binary"]
    tr.feat_subset = D["feat_subset"]
    tr.df_X, tr.df_Y, tr.split_idxes = D["df_X"], D["df_Y"], D["split_idxes"]
    tr.train_all()
    tr.clfs["threshold_binary"].save_model(os.path.join(out, "admit_threshold_binary.model"))
    print("feature columns:", tr.feat_cols)
    # prefetch models (train.py: PrefetcherConfTrainer.train_and_save_all() minus prep_data)
    P = {os.path.basename(f).split("_", 3)[-1].replace(".pkl", ""): pickle.load(open(f, "rb"))
         for f in glob.glob(os.path.join(dump, "prefetch_prep_*.pkl"))}
    tk = {"region": "replay"}
    pt = tpf.PrefetcherConfTrainer(trace_kwargs=tk, e_age_s=None, wr_threshold=None)
    assert pt.feat_names == P["PrefetcherConfTrainer"]["feat_names"][:len(pt.feat_names)]
    inner = pt.trainer
    inner.X, inner.Y = P["PrefetcherTrainer"]["X"], P["PrefetcherTrainer"]["Y"]
    inner.split()
    for label in inner.targets:
        inner.clfs[label] = inner.train(label)
        inner.clfs[label].save_model(os.path.join(out, f"prefetch_{label}.model"))
    pt.X, pt.Y = P["PrefetcherConfTrainer"]["X"], P["PrefetcherConfTrainer"]["Y"]
    pt.splice()
    pt.split()
    for label in pt.targets:
        pt.clfs[label] = pt.train(label)
        pt.clfs[label].save_model(os.path.join(out, f"prefetch_{label}.model"))
    print("saved", sorted(os.listdir(out)))


if __name__ == "__main__":
    main()
