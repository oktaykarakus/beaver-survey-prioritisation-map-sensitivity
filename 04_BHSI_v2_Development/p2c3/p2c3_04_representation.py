"""P2-C3 national representation results (descriptive; freeze §8). Reads analysis/reach_table_B40.parquet and pooled.npz.
Writes analysis/rep/*.csv and rep_summary.json. No allocation here."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'p2c'))
import p2c_lc as L

R = Path(__file__).resolve().parents[2]; AN = R / '05_Experiments/BHSI_v2_P2C3/analysis'; OUT = AN / 'rep'; OUT.mkdir(exist_ok=True)
T = pd.read_parquet(AN / 'reach_table_B40.parquet'); Z = np.load(AN / 'pooled.npz')
CATS = L.CATS; NC = len(CATS); IDX = {c: i + 1 for i, c in enumerate(CATS)}; W, U = IDX['WATER'], IDX['UNK']
LANDK = [i for i in range(1, NC + 1) if i not in (W, U)]; WOODY = [IDX[c] for c in L.WOODY]; STRUCT = [IDX[c] for c in ('AGM', 'URBVEG', 'MIN')]
ARMS = ('C', 'LEn', 'LEg'); SCEN = ['C_lo', 'C_hi', 'LEg_lo', 'LEg_hi', 'LEn_lo', 'LEn_hi']
w = T.length_m.values; res = {}
tri = Z['pool_triple'].reshape(256, 16, 16, 16).astype(np.float64)            # [pixel catchment, C, LEn, LEg]
cids = sorted(T.CaBA_ID.unique())


def pair_stats(M):
    """M: 16x16 confusion (row first arm). Agreement/kappa on common known land; woody-binary agreement."""
    sub = M[np.ix_(LANDK, LANDK)]; n = sub.sum()
    if n == 0: return dict(n_px=0, agreement=np.nan, kappa=np.nan, woody_agreement=np.nan)
    a = np.trace(sub) / n; pa = sub.sum(1) / n; pb = sub.sum(0) / n; pe = (pa * pb).sum()
    wi = [LANDK.index(k) for k in WOODY]; nw = [k for k in range(len(LANDK)) if k not in wi]
    wa = (sub[np.ix_(wi, wi)].sum() + sub[np.ix_(nw, nw)].sum()) / n
    return dict(n_px=int(n), agreement=float(a), kappa=float((a - pe) / (1 - pe)), woody_agreement=float(wa))


def partition(t3):
    """t3: 16x16x16 counts (C, LEn, LEg). P2-C2 evaluation partition on pixels known land in all three arms."""
    k = np.ix_(LANDK, LANDK, LANDK); X = t3[k]; N = X.sum()
    if N == 0: return {}
    ci, ni, gi = np.meshgrid(LANDK, LANDK, LANDK, indexing='ij')
    an = ci == ni; ag = ci == gi; st = np.isin(ci, STRUCT)
    p = {'AGREE_NATIVE': X[an].sum(), 'GRAIN_RESOLVED': X[~an & ag].sum(), 'GRAIN_INTRODUCED': X[an & ~ag].sum(),
         'RESID_STRUCTURAL': X[~an & ~ag & st].sum(), 'RESID_OTHER': X[~an & ~ag & ~st].sum()}
    dn = N - p['AGREE_NATIVE']
    out = {f'{k}_pct_land': 100 * v / N for k, v in p.items()}
    out.update({f'{k}_pct_native_disagreement': 100 * v / dn for k, v in p.items() if k != 'AGREE_NATIVE'})
    out['NET_EXPLAINED_pct_native_disagreement'] = 100 * (p['GRAIN_RESOLVED'] - p['GRAIN_INTRODUCED']) / dn
    out['n_px'] = int(N)
    return out


def composition(t3, arm):
    ax = {'C': (1, 2), 'LEn': (0, 2), 'LEg': (0, 1)}[arm]; v = t3.sum(axis=ax)
    land = v.sum() - v[W]; tot = v.sum()
    d = {f'{c}_pct_land': 100 * v[IDX[c]] / land for c in CATS if c != 'WATER'}
    d['water_pct_buffer'] = 100 * v[W] / tot; d['nodata_pct_land'] = 100 * v[0] / land; d['woody_pct_land'] = 100 * v[WOODY].sum() / land
    d['interval_categories_pct_land'] = 100 * v[[IDX['GRS'], IDX['AGM'], IDX['URBVEG']]].sum() / land
    return d


nat = tri.sum(0)
pairs = {'C|LEn': nat.sum(2), 'C|LEg': nat.sum(1), 'LEn|LEg': nat.sum(0)}     # nat axes: (C, LEn, LEg)
res['pooled_pair'] = {k: pair_stats(v) for k, v in pairs.items()}
res['pooled_partition'] = partition(nat)
res['pooled_composition'] = {a: composition(nat, a) for a in ARMS}
res['pooled_px_total'] = int(nat.sum()); res['pooled_px_outside_catchment_polygons'] = int(tri[0].sum())
for nm, M in pairs.items():
    pd.DataFrame(M, index=['(none)'] + CATS, columns=['(none)'] + CATS).astype(np.int64).to_csv(OUT / f'confusion_national_{nm.replace("|", "_")}.csv')
# category correspondence (C row)
cc = []
for q, M in (('LEn', pairs['C|LEn']), ('LEg', pairs['C|LEg'])):
    for c in CATS:
        if c == 'WATER': continue
        r = M[IDX[c]]; n = r.sum()
        if n: cc.append({'comparison': f'C vs {q}', 'corine_category': c, 'corine_pct_land': 100 * n / M[LANDK].sum(), 'pct_same_in_other': 100 * r[IDX[c]] / n,
                         'pct_woody_in_other': 100 * r[WOODY].sum() / n, 'pct_water_in_other': 100 * r[W] / n, 'pct_unknown_or_nodata_in_other': 100 * (r[U] + r[0]) / n})
pd.DataFrame(cc).round(3).to_csv(OUT / 'category_correspondence_national.csv', index=False)
# residual-other top pairs (C -> LEg)
ci, ni, gi = np.meshgrid(range(16), range(16), range(16), indexing='ij')
m = np.isin(ci, LANDK) & np.isin(ni, LANDK) & np.isin(gi, LANDK) & (ci != ni) & (ci != gi) & ~np.isin(ci, STRUCT)
rp = pd.DataFrame({'C': ci[m], 'LEg': gi[m], 'px': nat[m]}).groupby(['C', 'LEg']).px.sum().sort_values(ascending=False)
rp = (100 * rp / rp.sum()).head(12).reset_index(); rp['C'] = [CATS[i - 1] for i in rp.C]; rp['LEg'] = [CATS[i - 1] for i in rp.LEg]
rp.rename(columns={'px': 'pct_of_resid_other'}).round(2).to_csv(OUT / 'residual_other_top_pairs_national.csv', index=False)

# ---- water (pooled sub-types) ----
WS = ['RIVER_CHANNEL', 'RIVER_CHANNEL_EXCLUDED', 'OTHER_INLAND_LAKE', 'OTHER_INLAND_CANAL', 'COASTAL_TIDAL', 'OTHER_INLAND_OFFNETWORK']
tot = nat.sum(); wr = []
for a in ARMS:
    v = Z[f'pool_water_{a}'].sum(0)
    wr.append({'arm': a, **{f'{s}_pct_buffer': 100 * v[k + 1] / tot for k, s in enumerate(WS)}, 'all_water_pct_buffer': 100 * v.sum() / tot})
pd.DataFrame(wr).round(4).to_csv(OUT / 'water_subtypes_national.csv', index=False); res['water_subtypes'] = wr
# ---- reach-level diagnostics ----
rl = {}
for a in ARMS:
    zl = T[f'{a}_land_px'] == 0
    rl[a] = {'zero_land_reaches': int(zl.sum()), 'zero_land_km': float(w[zl].sum() / 1000), 'RW_flag_pct_len': float(100 * w[T[f'{a}_water_frac'] > 0.75].sum() / w.sum()),
             'unknown_pct_land_lenw': float(100 * np.nansum(T[f'{a}_unknown_frac_of_land'] * w) / w.sum()),
             'nocov_gt50pct_land_pct_len': float(100 * w[(T[f'{a}_nocov_px'] / T[f'{a}_land_px'].replace(0, np.nan)).fillna(0) > 0.5].sum() / w.sum()),
             'woody_lenw_mean_pct': float(100 * np.nansum(T[f'{a}_woody'] * w) / w[T[f'{a}_woody'].notna()].sum()),
             'interval_width_lenw_mean': float(np.nansum((T[f'{a}_s_hi'] - T[f'{a}_s_lo']) * w) / w[T[f'{a}_s_lo'].notna()].sum()),
             'pct_len_interval_width_ge_0.2': float(100 * w[(T[f'{a}_s_hi'] - T[f'{a}_s_lo']) >= 0.2].sum() / w.sum())}
    for e in ('lo', 'hi'):
        s = T[f'{a}_s_{e}'].values; ok = np.isfinite(s); o = np.argsort(s[ok]); cw = np.cumsum(w[ok][o]) / w[ok].sum()
        rl[a][f's_{e}_lenw_mean'] = float(np.average(s[ok], weights=w[ok]))
        rl[a][f's_{e}_lenw_quantiles_10_25_50_75_90'] = [float(s[ok][o][np.searchsorted(cw, q)]) for q in (0.1, 0.25, 0.5, 0.75, 0.9)]
        rl[a][f's_{e}_pct_len_at_0'] = float(100 * w[ok][s[ok] == 0].sum() / w.sum()); rl[a][f's_{e}_pct_len_at_1'] = float(100 * w[ok][s[ok] == 1].sum() / w.sum())
    rl[a]['within_source_lo_hi_spearman'] = float(stats.spearmanr(T[f'{a}_s_lo'], T[f'{a}_s_hi'], nan_policy='omit')[0])
for p, q in (('C', 'LEn'), ('C', 'LEg'), ('LEn', 'LEg')):
    n = T[f'{p}_{q}_common_px'].values; ag = T[f'{p}_{q}_agree_px'].values; ok = n > 0
    rl[f'{p}|{q}'] = {'reach_agreement_lenw_mean': float(np.average(ag[ok] / n[ok], weights=w[ok]))}
    if f'{p}_{q}_woody_common_px' in T:
        n2 = T[f'{p}_{q}_woody_common_px'].values; a2 = T[f'{p}_{q}_woody_agree_px'].values; ok2 = n2 > 0
        rl[f'{p}|{q}']['reach_woody_agreement_lenw_mean'] = float(np.average(a2[ok2] / n2[ok2], weights=w[ok2]))
res['reach_level'] = rl
# variance decomposition (length-weighted) and rank agreement
S = {f'{a}_{e}': T[f'{a}_s_{e}'].fillna(0).values for a in ARMS for e in ('lo', 'hi')}
S.update({f'{a}_woody': T[f'{a}_woody'].fillna(0).values for a in ARMS})
cat = T.CaBA_ID.values; ui, inv = np.unique(cat, return_inverse=True); Lc = np.bincount(inv, weights=w)
vd = {}; cm = {}
for k, s in S.items():
    mu = np.average(s, weights=w); mc = np.bincount(inv, weights=w * s) / Lc; cm[k] = mc
    sst = (w * (s - mu) ** 2).sum(); ssb = (Lc * (mc - mu) ** 2).sum(); vd[k] = {'between_catchment_share': float(ssb / sst), 'catchment_mean_range': [float(mc.min()), float(mc.max())]}
res['variance_decomposition'] = vd
keys = list(S); ra = []
for i, k1 in enumerate(keys):
    for k2 in keys[i + 1:]:
        top1 = set(ui[np.argsort(-cm[k1], kind='mergesort')[:10]]); top2 = set(ui[np.argsort(-cm[k2], kind='mergesort')[:10]])
        ra.append({'a': k1, 'b': k2, 'reach_spearman': stats.spearmanr(S[k1], S[k2])[0], 'reach_kendall_tau_b': stats.kendalltau(S[k1], S[k2])[0],
                   'catchment_spearman': stats.spearmanr(cm[k1], cm[k2])[0], 'catchment_top10_overlap': len(top1 & top2)})
pd.DataFrame(ra).round(4).to_csv(OUT / 'rank_agreement.csv', index=False)
pd.DataFrame(cm, index=ui).round(5).rename_axis('CaBA_ID').to_csv(OUT / 'catchment_mean_scores.csv')
# ---- per-catchment table (pixel catchment = reach catchment for the pooled stats) ----
C1T = pd.read_csv(R / '05_Experiments/BHSI_v2_P2C/c1/p2c1_catchment_eligibility.csv').set_index('CaBA_ID')
rows = []
for c in cids:
    t3 = tri[c]; r = {'CaBA_ID': c, 'CaBA_Catch': C1T.CaBA_Catch[c], 'eligible_km': C1T.eligible_km[c], 'partial_flag': bool(C1T.partial_coverage_flag_lt50pct[c])}
    for nm, ax in (('C_LEn', 2), ('C_LEg', 1), ('LEn_LEg', 0)):
        ps = pair_stats(t3.sum(ax)); r[f'agree_{nm}'] = ps['agreement']; r[f'kappa_{nm}'] = ps['kappa']; r[f'woody_agree_{nm}'] = ps['woody_agreement']
    for a in ARMS: r[f'woody_pct_{a}'] = composition(t3, a)['woody_pct_land']
    pt = partition(t3); r['grain_net_explained_pct'] = pt.get('NET_EXPLAINED_pct_native_disagreement', np.nan); r['resid_other_pct_native_disagreement'] = pt.get('RESID_OTHER_pct_native_disagreement', np.nan)
    r['resid_structural_pct_native_disagreement'] = pt.get('RESID_STRUCTURAL_pct_native_disagreement', np.nan)
    for k in ('C_lo', 'C_hi', 'LEg_lo', 'LEg_hi', 'LEn_lo', 'LEn_hi'): r[f'mean_{k}'] = cm[k][list(ui).index(c)]
    rows.append(r)
CT = pd.DataFrame(rows); CT.round(5).to_csv(OUT / 'catchment_representation.csv', index=False)
res['catchment_spread'] = {k: {'min': float(CT[k].min()), 'median': float(CT[k].median()), 'max': float(CT[k].max())} for k in ('agree_C_LEn', 'agree_C_LEg', 'woody_pct_C', 'woody_pct_LEg', 'woody_pct_LEn', 'grain_net_explained_pct')}
res['catchments_grain_net_negative'] = int((CT.grain_net_explained_pct < 0).sum())
(OUT / 'rep_summary.json').write_text(json.dumps(res, indent=1, default=float) + '\n')
print(json.dumps({k: res[k] for k in ('pooled_pair', 'pooled_partition', 'catchment_spread')}, indent=1, default=float))
