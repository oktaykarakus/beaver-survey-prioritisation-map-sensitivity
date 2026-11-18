"""P2-C3 fixed-budget allocations, cross-scenario regret, null models, resampling and robustness (frozen: P2C3_EXPERIMENTAL_FREEZE.md v1.0).
Usage: python -I p2c3_05_allocation.py     writes 05_Experiments/BHSI_v2_P2C3/analysis/alloc/ and the two deliverable CSVs."""
import os, sys, json, time
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p2c3_alloc as A

t0 = time.time()
R = Path(__file__).resolve().parents[2]
# P2C3_TEST_DIR (synthetic smoke tests only) redirects every input and output away from the project results
AN = Path(os.environ['P2C3_TEST_DIR']) if os.environ.get('P2C3_TEST_DIR') else R / '05_Experiments/BHSI_v2_P2C3/analysis'; OUT = AN / 'alloc'; OUT.mkdir(exist_ok=True)
DEL = AN if os.environ.get('P2C3_TEST_DIR') else R / '06_Results_Figures/BHSI_v2_P2C3'
T = pd.read_parquet(AN / 'reach_table_B40.parquet')
assert T.fragment_id.is_monotonic_increasing
CORE = ['C_lo', 'C_hi', 'LEg_lo', 'LEg_hi']; DIAG = ['LEn_lo', 'LEn_hi']; SCEN = CORE + DIAG
WOODY = ['C', 'LEg', 'LEn']; FRACS = (0.01, 0.05, 0.10); PRIMARY = 0.05
SEED_PERM, SEED_CPERM = 20261117, 20261118
log = lambda *a: print(f'{time.time() - t0:7.0f}s', *a, flush=True)


def scores_from(D, cond=False):
    sfx = '_cond' if cond else ''
    s = {f'{a}_{e}': D[f'{a}_s_{e}{sfx}'].values.astype(float) for a in ('C', 'LEg', 'LEn') for e in ('lo', 'hi')}
    w = {a: D[f'{a}_woody'].values.astype(float) for a in WOODY}
    return s, w


def perms(n, ncatch):
    return np.random.default_rng(SEED_PERM).permutation(n), np.random.default_rng(SEED_CPERM).permutation(ncatch)


def allocations(s, w, L, catch, f, perm, cperm):
    B = f * L.sum(); X = {}
    for j in SCEN:
        X[('A1', j)] = A.a1_reach(s[j], L, B, perm)
        X[('A2', j)] = A.a2_catchment(s[j], L, catch, B, perm, cperm)
        X[('A3', j)] = A.a3_stratified(s[j], L, catch, f, perm)
    for a in WOODY: X[('R2', f'woody_{a}')] = A.a1_reach(w[a], L, B, perm)
    for k, x in X.items(): assert abs((x * L).sum() - B) < 1e-3, (k, (x * L).sum() - B)     # 1e-6 km
    return B, X


def contrasts(X, L, B, strat):
    rf = lambda i, j: A.overlap(X[(strat, i)], X[(strat, j)], L, B)['replaced_fraction']
    d = {'D_R': np.mean([rf('C_lo', 'LEg_lo'), rf('C_hi', 'LEg_hi')]), 'D_A': np.mean([rf('C_lo', 'C_hi'), rf('LEg_lo', 'LEg_hi')]),
         'D_R_lo': rf('C_lo', 'LEg_lo'), 'D_R_hi': rf('C_hi', 'LEg_hi'), 'D_A_C': rf('C_lo', 'C_hi'), 'D_A_LEg': rf('LEg_lo', 'LEg_hi'),
         'D_G': np.mean([rf('LEn_lo', 'LEg_lo'), rf('LEn_hi', 'LEg_hi')]), 'D_RN': np.mean([rf('C_lo', 'LEn_lo'), rf('C_hi', 'LEn_hi')]),
         'D_A_LEn': rf('LEn_lo', 'LEn_hi')}
    d['RxA_interaction'] = d['D_R_lo'] - d['D_R_hi']; d['grain_persistence_share'] = d['D_R'] / d['D_RN'] if d['D_RN'] > 0 else np.nan
    return d


def core_share(X, L, B, keys):
    m = np.min(np.vstack([X[k] for k in keys]), axis=0); return float((m * L).sum() / B), m


def evaluate(X, s, L, B, catch, ids, f_label, extra=None):
    """Regret rows for every allocation under every scenario, plus allocation rows."""
    opt = {j: A.value(X[('A1', j)], s[j], L) for j in SCEN}
    kmc = {k: A.by_catchment(x, L, catch, ids) for k, x in X.items()}
    rr, ar = [], []
    for k, x in X.items():
        strat, orig = k
        conc = A.concentration(kmc[k])
        ar.append({'budget_pct': f_label, 'strategy': strat, 'origin': orig, 'selected_km': (x * L).sum() / 1000, 'budget_km': B / 1000, 'n_reaches_any': int((x > 0).sum()),
                   'n_partial': int(((x > 0) & (x < 1)).sum()), **conc})
        for j in SCEN:
            cap, nreg, areg, preg = A.capture(x, s[j], L, B, opt[j]); ov = A.overlap(x, X[('A1', j)], L, B)
            rr.append({'budget_pct': f_label, 'strategy': strat, 'origin': orig, 'target': j, 'diagonal': (strat == 'A1' and orig == j),
                       'target_core': j in CORE, 'origin_core': orig in CORE, 'value': A.value(x, s[j], L) / 1000, 'opt_value': opt[j] / 1000,
                       'random_expectation': B / L.sum() * float((L * np.nan_to_num(s[j])).sum()) / 1000, 'capture': cap, 'norm_regret': nreg,
                       'prop_regret': preg, 'abs_regret_score_km': areg / 1000, 'replaced_fraction_vs_target_opt': ov['replaced_fraction'], 'jaccard_vs_target_opt': ov['jaccard'],
                       'catchment_redistribution_vs_target_opt': A.redistribution(kmc[k], kmc[('A1', j)], B)})
    return pd.DataFrame(rr), pd.DataFrame(ar), kmc


# ======================================================================== primary dataset
L = T.length_m.values; catch = T.CaBA_ID.values; ids = np.unique(catch); n = len(T)
s, w = scores_from(T); perm, cperm = perms(n, len(ids))
summary = {'n_reaches': n, 'eligible_km': L.sum() / 1000, 'zero_land_km': {a: float(L[T[f'{a}_land_px'].values == 0].sum() / 1000) for a in WOODY}}
REG, ALL, KMC, XS = [], [], [], {}
for f in FRACS:
    B, X = allocations(s, w, L, catch, f, perm, cperm)
    rg, al, kmc = evaluate(X, s, L, B, catch, ids, f * 100)
    # random references (R1, stratified) evaluated under every scenario
    caps = {j: [] for j in SCEN}; rfs = {j: [] for j in SCEN}; capss = {j: [] for j in SCEN}; conc = []
    optv = {j: A.value(X[('A1', j)], s[j], L) for j in SCEN}
    for r in range(1000):
        xr = A.random_alloc(L, B, np.random.default_rng(10001 + r)); xs = A.random_stratified(L, catch, f, np.random.default_rng(20001 + r))
        for j in SCEN:
            ov = optv[j]
            caps[j].append(A.capture(xr, s[j], L, B, ov)[0]); capss[j].append(A.capture(xs, s[j], L, B, ov)[0])
            rfs[j].append(A.overlap(xr, X[('A1', j)], L, B)['replaced_fraction'])
        conc.append(A.concentration(A.by_catchment(xr, L, catch, ids)))
    for j in SCEN:
        for nm, v in (('R1_random_capture', caps[j]), ('R1_stratified_random_capture', capss[j]), ('R1_random_replaced_fraction_vs_opt', rfs[j])):
            rg.loc[rg.target == j, f'{nm}_mean'] = np.mean(v); rg.loc[rg.target == j, f'{nm}_p2.5'] = np.percentile(v, 2.5); rg.loc[rg.target == j, f'{nm}_p97.5'] = np.percentile(v, 97.5)
    cdf = pd.DataFrame(conc)
    al = pd.concat([al, pd.DataFrame([{'budget_pct': f * 100, 'strategy': 'R1', 'origin': 'random_mean_of_1000', 'selected_km': B / 1000, 'budget_km': B / 1000,
                                       **{k: float(cdf[k].mean()) for k in cdf}}])], ignore_index=True)
    con = {st: contrasts(X, L, B, st) for st in ('A1', 'A2', 'A3')}
    cs, core_x = core_share(X, L, B, [('A1', j) for j in CORE])
    kc = A.by_catchment(core_x, L, catch, ids); kcs = np.sort(kc)[::-1]
    summary[f'budget_{f*100:g}'] = {'B_km': B / 1000, 'contrasts': con, 'core_share_of_budget': cs, 'core_km': cs * B / 1000,
                                    'core_n_catchments_holding_50pct': int(np.searchsorted(np.cumsum(kcs) / kcs.sum(), 0.5) + 1) if kcs.sum() > 0 else 0,
                                    'core_n_catchments_any': int((kc > 0).sum()),
                                    'core_share_A2': core_share(X, L, B, [('A2', j) for j in CORE])[0], 'core_share_A3': core_share(X, L, B, [('A3', j) for j in CORE])[0],
                                    'core_share_incl_LEn': core_share(X, L, B, [('A1', j) for j in SCEN])[0]}
    REG.append(rg); ALL.append(al)
    for k, v in kmc.items(): KMC.append(pd.DataFrame({'budget_pct': f * 100, 'strategy': k[0], 'origin': k[1], 'CaBA_ID': ids, 'selected_km': v / 1000}))
    XS[f] = X
    log('budget', f, 'done')
REG = pd.concat(REG, ignore_index=True); ALL = pd.concat(ALL, ignore_index=True); KMC = pd.concat(KMC, ignore_index=True)

# gradient diagnostic and inherited-overlap influence, per allocation
gs = T.gradient_score.values; gp = T.gradient_pct.values
IO = pd.read_csv(R / '05_Experiments/BHSI_v2_P2C/c1/p2c1_inherited_overlaps.csv'); IO = IO[IO.both_eligible]
pos = pd.Series(np.arange(n), index=T.fragment_id)
present = IO.fragment_a.isin(pos.index) & IO.fragment_b.isin(pos.index)
assert present.all() or os.environ.get('P2C3_TEST_DIR'), 'inherited-overlap fragments missing'
IO = IO[present]; ia, ib, iol = pos[IO.fragment_a].values, pos[IO.fragment_b].values, IO.overlap_m.values
gd = []
for f, X in XS.items():
    for k, x in X.items():
        sel = x * L
        gd.append({'budget_pct': f * 100, 'strategy': k[0], 'origin': k[1], 'pct_selected_len_gradient_gt6pct': 100 * sel[gs < 1].sum() / sel.sum(),
                   'lenw_mean_gradient_pct_selected': float((sel * np.nan_to_num(gp)).sum() / sel.sum()),
                   'double_counted_overlap_km': float((np.minimum(x[ia], x[ib]) * iol).sum() / 1000)})
G = pd.DataFrame(gd)
ALL = ALL.merge(G, on=['budget_pct', 'strategy', 'origin'], how='left')
summary['pool_pct_len_gradient_gt6pct'] = float(100 * L[gs < 1].sum() / L.sum()); summary['pool_lenw_mean_gradient_pct'] = float(np.average(np.nan_to_num(gp), weights=L))
summary['gradient_spearman_with_scores'] = {j: float(stats.spearmanr(np.nan_to_num(s[j]), np.nan_to_num(gp))[0]) for j in SCEN}
REG.round(6).to_csv(DEL / 'P2C3_CROSS_SCENARIO_REGRET.csv', index=False)
ALL.round(6).to_csv(DEL / 'P2C3_ALLOCATION_RESULTS.csv', index=False)
KMC.round(6).to_csv(OUT / 'selected_km_by_catchment.csv', index=False)
np.savez_compressed(OUT / 'allocations_primary_5pct.npz', fragment_id=T.fragment_id.values.astype(str), **{f'{k[0]}__{k[1]}': v for k, v in XS[PRIMARY].items()})
# overlap matrices (A1 + woody), primary budget
X = XS[PRIMARY]; B = PRIMARY * L.sum(); keys = [('A1', j) for j in SCEN] + [('R2', f'woody_{a}') for a in WOODY]
M = pd.DataFrame([[A.overlap(X[a], X[b], L, B)['replaced_fraction'] for b in keys] for a in keys], index=[f'{a}:{b}' for a, b in keys], columns=[f'{a}:{b}' for a, b in keys])
M.round(5).to_csv(OUT / 'replaced_fraction_matrix_5pct.csv')
log('primary evaluation done')

# ======================================================================== tie-breaking replicates (A1)
tie = {j: [] for j in SCEN}; tieDR = []
for r in range(200):
    p2 = np.random.default_rng(r + 1).permutation(n); Xr = {}
    for j in SCEN:
        Xr[('A1', j)] = A.a1_reach(s[j], L, B, p2); tie[j].append(A.overlap(Xr[('A1', j)], X[('A1', j)], L, B)['replaced_fraction'])
    tieDR.append(np.mean([A.overlap(Xr[('A1', 'C_lo')], Xr[('A1', 'LEg_lo')], L, B)['replaced_fraction'], A.overlap(Xr[('A1', 'C_hi')], Xr[('A1', 'LEg_hi')], L, B)['replaced_fraction']]))
summary['tie_breaking_5pct'] = {j: {'mean_replaced_vs_primary': float(np.mean(v)), 'max_replaced_vs_primary': float(np.max(v))} for j, v in tie.items()}
summary['tie_breaking_5pct']['D_R_range'] = [float(np.min(tieDR)), float(np.max(tieDR))]
summary['ties_pct_len_at_score_1'] = {j: float(100 * L[np.nan_to_num(s[j]) >= 1].sum() / L.sum()) for j in SCEN}
log('ties done')

# ======================================================================== null models (5%)
nulls = {}
def a1_rf(sa, sb, p):
    return A.overlap(A.a1_reach(sa, L, B, p), A.a1_reach(sb, L, B, p), L, B)['replaced_fraction']
# rank copula
PAIRS = [('C_lo', 'LEg_lo'), ('C_hi', 'LEg_hi'), ('C_lo', 'C_hi'), ('LEg_lo', 'LEg_hi'), ('LEn_lo', 'LEg_lo'), ('C_lo', 'LEn_lo')]
for a, b in PAIRS:
    sa, sb = np.nan_to_num(s[a]), np.nan_to_num(s[b]); rho = stats.spearmanr(sa, sb)[0]; r_ = 2 * np.sin(np.pi * rho / 6)
    qa, qb = np.sort(sa), np.sort(sb); out = []
    for k in range(200):
        g = np.random.default_rng(30001 + k); z1 = g.standard_normal(n); z2 = r_ * z1 + np.sqrt(1 - r_ ** 2) * g.standard_normal(n)
        ya = np.empty(n); ya[np.argsort(z1)] = qa; yb = np.empty(n); yb[np.argsort(z2)] = qb
        out.append(a1_rf(ya, yb, perm))
    obs = A.overlap(X[('A1', a)], X[('A1', b)], L, B)['replaced_fraction']
    nulls[f'copula|{a}|{b}'] = {'spearman': float(rho), 'observed_replaced': float(obs), 'null_mean': float(np.mean(out)), 'null_p2.5': float(np.percentile(out, 2.5)), 'null_p97.5': float(np.percentile(out, 97.5))}
# shuffles
cell = (np.floor(T.x.values / 10000).astype(np.int64) * 100000 + np.floor(T.y.values / 10000).astype(np.int64))
def shuffle_within(v, grp, rng):
    o = np.lexsort((rng.random(len(v)), grp)); srt = np.argsort(grp, kind='stable'); out = np.empty_like(v); out[srt] = v[o]; return out
for j in SCEN:
    sj = np.nan_to_num(s[j]); ov = A.value(X[('A1', j)], sj, L); res_ = {}
    for nm, grp, seed in (('within_catchment', catch, 40001), ('within_10km_cell', cell, 50001)):
        caps = []
        for k in range(200):
            sh = shuffle_within(sj, grp, np.random.default_rng(seed + k)); caps.append(A.capture(A.a1_reach(sh, L, B, perm), sj, L, B, ov)[0])
        res_[nm] = {'capture_mean': float(np.mean(caps)), 'p2.5': float(np.percentile(caps, 2.5)), 'p97.5': float(np.percentile(caps, 97.5))}
    cc = [A.concentration(A.by_catchment(A.a1_reach(np.random.default_rng(60001 + k).permutation(sj), L, B, perm), L, catch, ids)) for k in range(200)]
    res_['global_shuffle_concentration'] = {m: [float(np.mean([c[m] for c in cc])), float(np.percentile([c[m] for c in cc], 2.5)), float(np.percentile([c[m] for c in cc], 97.5))] for m in cc[0]}
    nulls[f'shuffle|{j}'] = res_
# shuffle null for cross-scenario turnover: if both scenarios kept only their catchment-level information
for a, b in PAIRS[:2]:
    out = []
    for k in range(200):
        g = np.random.default_rng(40001 + k); ga = shuffle_within(np.nan_to_num(s[a]), catch, g); gb = shuffle_within(np.nan_to_num(s[b]), catch, g)
        out.append(a1_rf(ga, gb, perm))
    nulls[f'within_catchment_shuffle_turnover|{a}|{b}'] = {'mean': float(np.mean(out)), 'p2.5': float(np.percentile(out, 2.5)), 'p97.5': float(np.percentile(out, 97.5))}
(OUT / 'nulls_5pct.json').write_text(json.dumps(nulls, indent=1) + '\n'); summary['nulls_5pct'] = nulls
log('nulls done')

# ======================================================================== spatial dependence (correlogram of reach scores)
xy = T[['x', 'y']].values; BANDS = [0, 1, 2, 5, 10, 20, 50, 100]
cg = {}
rng = np.random.default_rng(80001); foc = rng.choice(n, 3000, replace=False); tree = cKDTree(xy)
nb = tree.query_ball_point(xy[foc], r=20000)
pi = np.concatenate([np.full(len(v), f_) for f_, v in zip(foc, nb)]); pj = np.concatenate(nb); keep = pi != pj; pi, pj = pi[keep], pj[keep]
qi = rng.integers(0, n, 2_000_000); qj = rng.integers(0, n, 2_000_000)
dP = np.hypot(*(xy[pi] - xy[pj]).T) / 1000; dQ = np.hypot(*(xy[qi] - xy[qj]).T) / 1000
for j in ['C_lo', 'LEg_lo', 'LEn_lo', 'C_hi', 'LEg_hi']:
    z = np.nan_to_num(s[j]); z = (z - z.mean()) / z.std(); row = {}
    for lo_, hi_ in zip(BANDS[:-1], BANDS[1:]):
        a_, b_, d = (pi, pj, dP) if hi_ <= 20 else (qi, qj, dQ)
        m = (d >= lo_) & (d < hi_)
        row[f'{lo_}-{hi_}km'] = float((z[a_[m]] * z[b_[m]]).mean()) if m.sum() > 100 else np.nan
    first = next((hi_ for (lo_, hi_) in zip(BANDS[:-1], BANDS[1:]) if row[f'{lo_}-{hi_}km'] < 0.1), np.nan)
    row['correlation_length_km'] = first; row['effective_n_stretches'] = float(L.sum() / 1000 / first) if np.isfinite(first) else np.nan
    cg[j] = row
summary['correlogram'] = cg
log('correlogram done')

# ======================================================================== block resampling (catchment bootstrap, 5%) and jackknife
gidx = {c: np.flatnonzero(catch == c) for c in ids}
def boot_metrics(idx, cvec, seed):
    Lb = L[idx]; Bb = PRIMARY * Lb.sum(); pb = np.random.default_rng(seed).permutation(len(idx)); cpb = np.random.default_rng(seed + 500000).permutation(len(np.unique(cvec)))
    sb = {j: s[j][idx] for j in SCEN}; Xb = {}
    for j in SCEN:
        Xb[('A1', j)] = A.a1_reach(sb[j], Lb, Bb, pb); Xb[('A2', j)] = A.a2_catchment(sb[j], Lb, cvec, Bb, pb, cpb)
    c1 = contrasts({**Xb, **{('A3', j): Xb[('A1', j)] for j in SCEN}}, Lb, Bb, 'A1'); c2 = contrasts({**Xb, **{('A3', j): Xb[('A1', j)] for j in SCEN}}, Lb, Bb, 'A2')
    ov = {j: A.value(Xb[('A1', j)], sb[j], Lb) for j in SCEN}
    reg = lambda i, j: A.capture(Xb[('A1', i)], sb[j], Lb, Bb, ov[j])[1]
    return {'D_R': c1['D_R'], 'D_A': c1['D_A'], 'D_G': c1['D_G'], 'D_RN': c1['D_RN'], 'D_R_A2': c2['D_R'], 'grain_persistence_share': c1['grain_persistence_share'],
            'regret_C_lo_to_LEg_lo': reg('C_lo', 'LEg_lo'), 'regret_LEg_lo_to_C_lo': reg('LEg_lo', 'C_lo'), 'regret_C_hi_to_LEg_hi': reg('C_hi', 'LEg_hi'), 'regret_LEg_hi_to_C_hi': reg('LEg_hi', 'C_hi'),
            'capture_A2_C_lo': A.capture(Xb[('A2', 'C_lo')], sb['C_lo'], Lb, Bb, ov['C_lo'])[0], 'capture_A2_LEg_lo': A.capture(Xb[('A2', 'LEg_lo')], sb['LEg_lo'], Lb, Bb, ov['LEg_lo'])[0],
            'core_share': core_share(Xb, Lb, Bb, [('A1', j) for j in CORE])[0]}
bt = []
for r in range(1000):
    g = np.random.default_rng(70001 + r); pick = g.choice(ids, len(ids), replace=True)
    idx = np.concatenate([gidx[c] for c in pick]); cvec = np.concatenate([np.full(len(gidx[c]), k) for k, c in enumerate(pick)])
    bt.append(boot_metrics(idx, cvec, 70001 + r))
BT = pd.DataFrame(bt); BT.to_csv(OUT / 'catchment_bootstrap_5pct.csv', index=False)
jk = []
for c in ids:
    idx = np.flatnonzero(catch != c); jk.append({'left_out': int(c), **boot_metrics(idx, catch[idx], 90001)})
JK = pd.DataFrame(jk); JK.to_csv(OUT / 'jackknife_5pct.csv', index=False)
summary['bootstrap_5pct'] = {k: {'p2.5': float(BT[k].quantile(0.025)), 'median': float(BT[k].median()), 'p97.5': float(BT[k].quantile(0.975))} for k in BT}
summary['jackknife_5pct'] = {k: {'min': float(JK[k].min()), 'max': float(JK[k].max())} for k in JK if k != 'left_out'}
log('resampling done')

# ======================================================================== robustness set (5%)
def headline(D, s_, w_, label, cond_note=''):
    Ld = D.length_m.values; cd = D.CaBA_ID.values; idd = np.unique(cd); p_, cp_ = perms(len(D), len(idd))
    Bd, Xd = allocations(s_, w_, Ld, cd, PRIMARY, p_, cp_)
    ov = {j: A.value(Xd[('A1', j)], s_[j], Ld) for j in SCEN}
    reg = lambda i, j, st='A1': A.capture(Xd[(st, i)], s_[j], Ld, Bd, ov[j])
    c1 = contrasts(Xd, Ld, Bd, 'A1'); c2 = contrasts(Xd, Ld, Bd, 'A2')
    offd = [reg(i, j)[1] for i in CORE for j in CORE if i != j]
    return {'variant': label, 'units': len(D), 'km': Ld.sum() / 1000, 'D_R': c1['D_R'], 'D_A': c1['D_A'], 'D_G': c1['D_G'], 'D_RN': c1['D_RN'], 'grain_persistence_share': c1['grain_persistence_share'],
            'D_R_A2': c2['D_R'], 'regret_C_lo_to_LEg_lo': reg('C_lo', 'LEg_lo')[1], 'regret_LEg_lo_to_C_lo': reg('LEg_lo', 'C_lo')[1],
            'mean_offdiag_core_regret': float(np.mean(offd)), 'max_offdiag_core_regret': float(np.max(offd)),
            'capture_A2_C_lo': reg('C_lo', 'C_lo', 'A2')[0], 'capture_A2_LEg_lo': reg('LEg_lo', 'LEg_lo', 'A2')[0], 'capture_A3_C_lo': reg('C_lo', 'C_lo', 'A3')[0], 'capture_A3_LEg_lo': reg('LEg_lo', 'LEg_lo', 'A3')[0],
            'core_share': core_share(Xd, Ld, Bd, [('A1', j) for j in CORE])[0]}
rob = [headline(T, s, w, 'primary (B40 fragments)')]
for k in ('B20', 'B100', 'S1000', 'S500'):
    D = pd.read_parquet(AN / f'units_{k}.parquet').sort_values('unit_id').reset_index(drop=True)
    s_ = {f'{a}_{e}': D[f'{a}_s_{e}'].values for a in ('C', 'LEg', 'LEn') for e in ('lo', 'hi')}; w_ = {a: D[f'{a}_woody'].values for a in WOODY}
    rob.append(headline(D, s_, w_, {'B20': '20 m buffer', 'B100': '100 m buffer', 'S1000': '1 km segments', 'S500': '500 m segments'}[k]))
s_c, _ = scores_from(T, cond=True); rob.append(headline(T, s_c, w, 'unknown conditional'))
zl = (T[[f'{a}_land_px' for a in WOODY]].values == 0).any(1)
Tz = T[~zl].reset_index(drop=True); s_z, w_z = scores_from(Tz); rob.append(headline(Tz, s_z, w_z, 'F-Z zero-land reaches dropped jointly'))
C1T = pd.read_csv(R / '05_Experiments/BHSI_v2_P2C/c1/p2c1_catchment_eligibility.csv'); part = set(C1T.CaBA_ID[C1T.partial_coverage_flag_lt50pct.astype(bool)])
Tp = T[~T.CaBA_ID.isin(part)].reset_index(drop=True); s_p, w_p = scores_from(Tp); rob.append(headline(Tp, s_p, w_p, 'S-C2 partial-coverage catchments dropped'))
rw = {a: float(100 * L[T[f'{a}_water_frac'].values > 0.75].sum() / L.sum()) for a in WOODY}; summary['RW_flag_pct_len'] = rw
if max(rw.values()) > 2:
    fl = (T[[f'{a}_water_frac' for a in WOODY]].values > 0.75).any(1); Tw = T[~fl].reset_index(drop=True); s_w, w_w = scores_from(Tw); rob.append(headline(Tw, s_w, w_w, 'S-W4 R-W flagged dropped jointly'))
ROB = pd.DataFrame(rob); ROB.round(6).to_csv(OUT / 'robustness_5pct.csv', index=False)
# materiality sensitivity on the primary contrasts
mat = []
for f in FRACS:
    for st in ('A1', 'A2', 'A3'):
        c = summary[f'budget_{f*100:g}']['contrasts'][st]
        for k in ('D_R', 'D_A', 'D_G', 'D_RN'):
            mat.append({'budget_pct': f * 100, 'strategy': st, 'contrast': k, 'replaced_fraction': c[k], **{f'material_at_{t}': c[k] >= t for t in (0.05, 0.10, 0.20)}})
pd.DataFrame(mat).round(6).to_csv(OUT / 'materiality.csv', index=False)
summary['seconds'] = time.time() - t0
(OUT / 'alloc_summary.json').write_text(json.dumps(summary, indent=1, default=lambda x: x.item() if hasattr(x, 'item') else str(x)) + '\n')
log('all done')
