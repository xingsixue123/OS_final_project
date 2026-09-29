"""Shared evaluation + the SAME repair applied to every method's raw binary x."""
import numpy as np


def greedy(inst):
    """Baleen-style: sort by total savings / bytes desc, admit prefix within W."""
    D, s, W = inst["D"], inst["s"], inst["W"]
    ratio = np.asarray(D.sum(1)).ravel() / s
    order = np.argsort(-ratio, kind="stable")
    cs = np.cumsum(s[order])
    k = int(np.searchsorted(cs, W * (1 + 1e-12), side="right"))
    x = np.zeros(inst["n"])
    x[order[:k]] = 1.0
    return x


def _contrib_at(inst, idx, w):
    """d[e,w] for episodes idx (0 if e does not cover w)."""
    st, ln, v = inst["start"][idx], inst["length"][idx], inst["vals"][idx]
    off = w - st
    ok = (off >= 0) & (off < ln)
    out = np.zeros(len(idx))
    out[ok] = v[ok, off[ok]]
    return out


def repair_ref(inst, x_raw, max_add=None):
    """Reference (slow, O(n) per step) implementation; kept for equivalence testing."""
    """Phase 1: while s^T x > W, drop the selected episode with the worst
    (peak-window contribution per byte) [ties -> largest s].
    Phase 2: while feasible, add the unselected episode with the best
    (marginal max-load reduction per byte); stop when no strictly positive reduction fits."""
    D, s, W, C = inst["D"], inst["s"], inst["W"], inst["C"]
    st, ln, V = inst["start"], inst["length"], inst["vals"]
    x = (np.asarray(x_raw) > 0.5).astype(float)
    L = C - D.T @ x
    use = float(s @ x)
    n_drop = n_add = 0
    sel = np.flatnonzero(x)
    while use > W * (1 + 1e-12):
        w = int(np.argmax(L))
        c = _contrib_at(inst, sel, w)
        key = c / s[sel]
        cand = np.flatnonzero(key == key.min())
        j = cand[np.argmax(s[sel[cand]])]
        e = sel[j]
        x[e] = 0.0
        use -= s[e]
        L[st[e]:st[e] + ln[e]] += V[e, :ln[e]]
        sel = np.delete(sel, j)
        n_drop += 1
    # phase 2
    n = inst["n"]
    ar = np.arange(3)
    while True:
        rem = W - use
        pk = L.max()
        top = np.argsort(-L)[:4]
        unsel = np.flatnonzero((x == 0) & (s <= rem + 1e-12))
        if len(unsel) == 0:
            break
        a, b = st[unsel], st[unsel] + ln[unsel]
        # max load outside the episode span: first of top-4 windows not covered
        outside = np.full(len(unsel), -np.inf)
        done = np.zeros(len(unsel), bool)
        for t in top:
            inside = (t >= a) & (t < b)
            take = (~done) & (~inside)
            outside[take] = L[t]
            done |= take
        # max over span of L_w - d_ew
        idxw = np.minimum(a[:, None] + ar[None, :], inst["m"] - 1)
        span = np.where(ar[None, :] < ln[unsel][:, None], L[idxw] - V[unsel], -np.inf)
        newmax = np.maximum(outside, span.max(1))
        red = pk - newmax
        score = red / s[unsel]
        j = int(np.argmax(score))
        if red[j] <= 1e-12:
            break
        e = unsel[j]
        x[e] = 1.0
        use += s[e]
        L[st[e]:st[e] + ln[e]] -= V[e, :ln[e]]
        n_add += 1
        if max_add is not None and n_add >= max_add:
            break
    return x, dict(n_drop=n_drop, n_add=n_add)


def evaluate(inst, x):
    L = inst["C"] - inst["D"].T @ x
    return dict(peak=float(L.max()), use=float(inst["s"] @ x / inst["W"]),
                n_sel=int((x > 0.5).sum()))


def repair(inst, x_raw, max_add=None):
    """Same rule as repair_ref, exact but faster:
    Phase 1: an episode not covering the peak window w* has key 0 (the minimum), and the tie-break
      is largest s, so we drop the largest-s selected episode not covering w*; only if every selected
      episode covers w* do we fall back to min d[e,w*]/s_e.
    Phase 2: only episodes covering the (unique) argmax window can strictly reduce the max, so the
      candidate set is restricted to the CSC column of w* (identical argmax, same index order)."""
    D, s, W, C = inst["D"], inst["s"], inst["W"], inst["C"]
    st, ln, V = inst["start"], inst["length"], inst["vals"]
    Dc = inst["Dcsc"]
    x = (np.asarray(x_raw) > 0.5).astype(float)
    L = C - D.T @ x
    use = float(s @ x)
    n_drop = n_add = 0
    if use > W * (1 + 1e-12):
        sel = np.flatnonzero(x)
        order = sel[np.argsort(-s[sel], kind="stable")]
        alive = np.ones(len(order), bool)
        while use > W * (1 + 1e-12):
            w = int(np.argmax(L))
            # scan (in chunks) for the largest-s alive episode not covering w
            e = -1
            pos = 0
            while pos < len(order):
                blk = slice(pos, min(pos + 256, len(order)))
                oe = order[blk]
                ok = alive[blk] & ~((st[oe] <= w) & (w < st[oe] + ln[oe]))
                if ok.any():
                    j = pos + int(np.argmax(ok))
                    e = order[j]
                    break
                pos += 256
            if e < 0:  # all remaining selected episodes cover w: min contribution per byte
                idx = np.flatnonzero(alive)
                es = order[idx]
                key = _contrib_at(inst, es, w) / s[es]
                cand = np.flatnonzero(key == key.min())
                j = idx[cand[np.argmax(s[es[cand]])]]
                e = order[j]
            alive[j] = False
            x[e] = 0.0
            use -= s[e]
            L[st[e]:st[e] + ln[e]] += V[e, :ln[e]]
            n_drop += 1
    ar = np.arange(3)
    while True:
        rem = W - use
        top = np.argsort(-L)[:4]
        pk = L[top[0]]
        if L[top[1]] >= pk:  # tie at the max: no single add can strictly reduce it
            break
        w = top[0]
        col = Dc.indices[Dc.indptr[w]:Dc.indptr[w + 1]]
        col = np.sort(col)
        unsel = col[(x[col] == 0) & (s[col] <= rem + 1e-12)]
        if len(unsel) == 0:
            break
        a, b = st[unsel], st[unsel] + ln[unsel]
        outside = np.full(len(unsel), -np.inf)
        done = np.zeros(len(unsel), bool)
        for t in top:
            inside = (t >= a) & (t < b)
            take = (~done) & (~inside)
            outside[take] = L[t]
            done |= take
        idxw = np.minimum(a[:, None] + ar[None, :], inst["m"] - 1)
        span = np.where(ar[None, :] < ln[unsel][:, None], L[idxw] - V[unsel], -np.inf)
        newmax = np.maximum(outside, span.max(1))
        red = pk - newmax
        score = red / s[unsel]
        j = int(np.argmax(score))
        if red[j] <= 1e-12:
            break
        e = unsel[j]
        x[e] = 1.0
        use += s[e]
        L[st[e]:st[e] + ln[e]] -= V[e, :ln[e]]
        n_add += 1
        if max_add is not None and n_add >= max_add:
            break
    return x, dict(n_drop=n_drop, n_add=n_add)
