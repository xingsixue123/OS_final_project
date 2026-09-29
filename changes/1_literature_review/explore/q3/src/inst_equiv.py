"""Check two instance npz files describe the same instance up to episode permutation."""
import sys
import numpy as np, scipy.sparse as sp
def load(p):
    z = np.load(p)
    D = sp.csr_matrix((z["D_data"], z["D_indices"], z["D_indptr"]), shape=tuple(z["D_shape"]))
    ids = [(str(k), float(t)) for k, t in zip(z["keys"], z["ts0"])]
    return z, D, ids
a, Da, ia = load(sys.argv[1]); b, Db, ib = load(sys.argv[2])
pos = {x: i for i, x in enumerate(ib)}
perm = np.array([pos[x] for x in ia])
print("n", len(ia), len(ib), "m", Da.shape[1], Db.shape[1], "B", float(a["B"]), float(b["B"]),
      "C maxabs", float(np.abs(a["C"] - b["C"]).max()), "s maxabs", float(np.abs(a["s"] - b["s"][perm]).max()),
      "D maxabs", float(abs(Da - Db[perm]).max()), "active eq", bool((a["active"] == b["active"]).all()),
      "ea", float(a["ea"]), float(b["ea"]), "baleen top-B set equal",
      set(np.flatnonzero(np.cumsum(a["s"][a["base_order"]]) <= a["B"])) is not None)
