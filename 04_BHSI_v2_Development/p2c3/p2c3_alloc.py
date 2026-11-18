"""P2-C3 fixed-budget allocation and decision metrics (frozen in P2C3_EXPERIMENTAL_FREEZE.md).
An allocation is x in [0,1]^n, the selected fraction of each reach; selected length = sum(x * L) = B exactly (one partial reach).
Scores: NaN (zero-land reach) counts as value 0 for selection and for evaluation (frozen rule F-Z); reported separately.
All tie-breaking uses a seeded permutation `perm` (rank of each reach in a random order): order = (-score, perm).
"""
import numpy as np


def _fill(order, L, B):
    """Select reaches in `order` until length B; the first reach that would exceed B is taken pro rata."""
    x = np.zeros(len(L)); cum = np.cumsum(L[order])
    full = cum <= B + 1e-9
    x[order[full]] = 1.0
    k = int(full.sum())
    if k < len(order):
        prev = cum[k - 1] if k > 0 else 0.0
        x[order[k]] = (B - prev) / L[order[k]]
    return x


def a1_reach(s, L, B, perm):
    """A1 national reach ranking (also the scenario optimum O when s is the evaluating scenario's own score)."""
    s0 = np.nan_to_num(s, nan=0.0)
    return _fill(np.lexsort((perm, -s0)), L, B)


def a2_catchment(s, L, catch, B, perm, cperm):
    """A2 catchment ranking: catchments ranked by length-weighted mean score (ties: cperm, a seeded rank per catchment id),
    whole catchments surveyed in order; the marginal catchment is filled in a seeded random reach order that ignores score."""
    s0 = np.nan_to_num(s, nan=0.0)
    ids, inv = np.unique(catch, return_inverse=True)
    Lc = np.bincount(inv, weights=L); mc = np.bincount(inv, weights=L * s0) / Lc
    corder = np.lexsort((cperm, -mc))                      # cperm: seeded rank per catchment, aligned with np.unique(catch)
    # reach order: by catchment rank, then by the seeded random reach order inside the catchment
    crank = np.empty(len(ids), int); crank[corder] = np.arange(len(ids))
    order = np.lexsort((perm, crank[inv]))
    return _fill(order, L, B)


def _fill_grouped(order, L, ginv, Bg):
    """`order` sorted by group first; select within each group until its budget Bg[group] (one partial reach per group)."""
    g = ginv[order]; Lo = L[order]; cum = np.cumsum(Lo)
    start = np.r_[0, np.flatnonzero(g[1:] != g[:-1]) + 1]
    base = np.repeat(cum[start] - Lo[start], np.diff(np.r_[start, len(g)]))
    cumc = cum - base; prev = cumc - Lo; Bo = Bg[g]
    x = np.zeros(len(L)); full = cumc <= Bo + 1e-9
    x[order[full]] = 1.0
    part = ~full & (prev < Bo)
    x[order[part]] = (Bo[part] - prev[part]) / Lo[part]
    return x


def a3_stratified(s, L, catch, f, perm):
    """A3 catchment-stratified: fraction f of every catchment's eligible length, reaches ranked by score within catchment."""
    s0 = np.nan_to_num(s, nan=0.0); ids, inv = np.unique(catch, return_inverse=True)
    return _fill_grouped(np.lexsort((perm, -s0, inv)), L, inv, f * np.bincount(inv, weights=L))


def random_alloc(L, B, rng):
    return _fill(rng.permutation(len(L)), L, B)


def random_stratified(L, catch, f, rng):
    ids, inv = np.unique(catch, return_inverse=True)
    return _fill_grouped(np.lexsort((rng.permutation(len(L)), inv)), L, inv, f * np.bincount(inv, weights=L))


def value(x, s, L):
    return float((x * L * np.nan_to_num(s, nan=0.0)).sum())


def capture(x, s, L, B, opt_value):
    """C = (V(x) - E_rand) / (V(O) - E_rand), E_rand = (B / sum L) * sum(L s). Returns (capture, norm_regret, abs_regret, prop_regret)."""
    v = value(x, s, L); er = B / L.sum() * float((L * np.nan_to_num(s, nan=0.0)).sum())
    den = opt_value - er
    cap = (v - er) / den if den > 1e-9 else np.nan
    return cap, (1 - cap) if np.isfinite(cap) else np.nan, opt_value - v, (1 - v / opt_value) if opt_value > 1e-12 else np.nan


def overlap(x, y, L, B):
    i = float((np.minimum(x, y) * L).sum())
    return {'intersection_km': i / 1000, 'replaced_fraction': 1 - i / B, 'jaccard': i / (2 * B - i)}


def by_catchment(x, L, catch, ids):
    """Selected length per catchment, aligned with sorted `ids` (every catch value must be in ids)."""
    return np.bincount(np.searchsorted(ids, catch), weights=x * L, minlength=len(ids))


def concentration(km_by_c):
    p = km_by_c / km_by_c.sum(); p = p[p > 0]
    srt = np.sort(km_by_c)
    n = len(km_by_c); gini = float((2 * np.arange(1, n + 1) - n - 1).dot(srt) / (n * srt.sum()))
    return {'top5_share': float(np.sort(km_by_c)[::-1][:5].sum() / km_by_c.sum()), 'effective_n_catchments': float(np.exp(-(p * np.log(p)).sum())),
            'gini': gini, 'n_catchments_selected': int((km_by_c > 1e-9).sum())}


def redistribution(km_a, km_b, B):
    """Share of the budget that sits in different catchments between two allocations: 0.5 * sum|a - b| / B."""
    return float(0.5 * np.abs(km_a - km_b).sum() / B)
