"""P2-C3 post-run verification (independent of p2c3_alloc where stated). Usage: python -I -B p2c3_07_verify.py
Writes 05_Experiments/BHSI_v2_P2C3/verification/post_run_checks.json."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd

R = Path(__file__).resolve().parents[2]; AN = R / '05_Experiments/BHSI_v2_P2C3/analysis'; DEL = R / '06_Results_Figures/BHSI_v2_P2C3'; V = R / '05_Experiments/BHSI_v2_P2C3/verification'
T = pd.read_parquet(AN / 'reach_table_B40.parquet'); RG = pd.read_csv(DEL / 'P2C3_CROSS_SCENARIO_REGRET.csv'); AL = pd.read_csv(DEL / 'P2C3_ALLOCATION_RESULTS.csv')
Z = np.load(AN / 'alloc/allocations_primary_5pct.npz'); res = {}
SCEN = ['C_lo', 'C_hi', 'LEg_lo', 'LEg_hi', 'LEn_lo', 'LEn_hi']

# 1 identifiers consistent
res['ids_reach_table_eq_allocations'] = bool((Z['fragment_id'] == T.fragment_id.values).all())
for k in ('B20', 'B100'): res[f'ids_{k}_eq_reach_table'] = bool(set(pd.read_parquet(AN / f'units_{k}.parquet').fragment_id) == set(T.fragment_id))
for k in ('S1000', 'S500'): res[f'ids_{k}_fragments_eq_reach_table'] = bool(set(pd.read_parquet(AN / f'units_{k}.parquet').fragment_id) == set(T.fragment_id))

# 2 completeness of scenario outputs
res['regret_rows'] = int(len(RG)); res['regret_rows_expected'] = 3 * 21 * 6
res['regret_complete'] = bool(len(RG) == 378 and RG.groupby(['budget_pct', 'strategy', 'origin']).target.nunique().eq(6).all())
res['allocation_rows'] = int(len(AL)); res['scores_present'] = {j: float(T[f'{j.split("_")[0]}_s_{j.split("_")[1]}'].notna().mean()) for j in SCEN}

# 3 budget accounting for every allocation (saved vectors, 5%) and for the CSV (all budgets)
L = T.length_m.values; B = 0.05 * L.sum()
dev = {k: float((Z[k] * L).sum() - B) for k in Z.files if k != 'fragment_id'}
res['budget_max_abs_dev_km_5pct_vectors'] = max(abs(v) for v in dev.values()) / 1000
res['budget_max_abs_dev_km_csv'] = float((AL.selected_km - AL.budget_km).abs().max())
res['budget_ok'] = res['budget_max_abs_dev_km_5pct_vectors'] < 1e-6 and res['budget_max_abs_dev_km_csv'] < 1e-6
res['x_in_unit_interval'] = bool(all(((Z[k] >= 0) & (Z[k] <= 1 + 1e-12)).all() for k in Z.files if k != 'fragment_id'))

# 4 independent recomputation of representative regret entries (pandas sort/cumsum; not p2c3_alloc). The deliverable CSV is rounded
#   to 6 decimals, so CSV entries are compared at half a unit of the 6th decimal (5e-7); allocation vectors are compared exactly (1e-9).
perm = np.random.default_rng(20261117).permutation(len(T))
def indep_a1(score):
    d = pd.DataFrame({'s': np.nan_to_num(score), 'p': perm, 'L': L}).sort_values(['s', 'p'], ascending=[False, True])
    cum = d.L.cumsum(); x = pd.Series(0.0, index=d.index); x[cum <= B + 1e-9] = 1.0
    k = (cum > B + 1e-9).idxmax(); x[k] = (B - (cum[k] - d.L[k])) / d.L[k]
    return x.sort_index().values
def indep_a2(score):
    s0 = np.nan_to_num(score); df = pd.DataFrame({'c': T.CaBA_ID.values, 'v': L * s0, 'L': L})
    g = df.groupby('c').sum(); g['m'] = g.v / g.L; cp = np.random.default_rng(20261118).permutation(len(g)); g['cp'] = cp
    rank = g.sort_values(['m', 'cp'], ascending=[False, True]).reset_index().reset_index().set_index('c')['index']
    d = pd.DataFrame({'r': rank.loc[T.CaBA_ID.values].values, 'p': perm, 'L': L}).sort_values(['r', 'p'])
    cum = d.L.cumsum(); x = pd.Series(0.0, index=d.index); x[cum <= B + 1e-9] = 1.0
    k = (cum > B + 1e-9).idxmax(); x[k] = (B - (cum[k] - d.L[k])) / d.L[k]
    return x.sort_index().values
sc = {j: T[f'{j.split("_")[0]}_s_{j.split("_")[1]}'].values for j in SCEN}
X = {j: indep_a1(sc[j]) for j in SCEN}; checks = []
for (o, t) in [('C_lo', 'LEg_lo'), ('LEg_lo', 'C_lo'), ('C_hi', 'LEg_hi'), ('LEg_hi', 'C_hi'), ('C_lo', 'C_hi'), ('LEn_lo', 'LEg_lo'), ('LEg_lo', 'LEn_lo')]:
    st = np.nan_to_num(sc[t]); v = (X[o] * L * st).sum(); opt = (X[t] * L * st).sum(); er = B / L.sum() * (L * st).sum()
    cap = (v - er) / (opt - er); rf = 1 - (np.minimum(X[o], X[t]) * L).sum() / B
    row = RG[(RG.budget_pct == 5) & (RG.strategy == 'A1') & (RG.origin == o) & (RG.target == t)].iloc[0]
    checks.append({'entry': f'A1 {o}->{t}', 'indep_regret': 1 - cap, 'csv_regret': row.norm_regret, 'indep_replaced': rf, 'csv_replaced': row.replaced_fraction_vs_target_opt,
                   'abs_diff_regret': abs(1 - cap - row.norm_regret), 'abs_diff_replaced': abs(rf - row.replaced_fraction_vs_target_opt)})
for o in ('C_lo', 'LEg_lo'):
    x2 = indep_a2(sc[o]); st = np.nan_to_num(sc[o]); v = (x2 * L * st).sum(); opt = (X[o] * L * st).sum(); er = B / L.sum() * (L * st).sum()
    row = RG[(RG.budget_pct == 5) & (RG.strategy == 'A2') & (RG.origin == o) & (RG.target == o)].iloc[0]
    checks.append({'entry': f'A2 {o}->{o}', 'indep_regret': 1 - (v - er) / (opt - er), 'csv_regret': row.norm_regret, 'abs_diff_regret': abs(1 - (v - er) / (opt - er) - row.norm_regret),
                   'max_abs_diff_vector': float(np.abs(x2 - Z[f'A2__{o}']).max())})
for j in SCEN: checks.append({'entry': f'A1 vector {j}', 'max_abs_diff_vector': float(np.abs(X[j] - Z[f'A1__{j}']).max())})
C = pd.DataFrame(checks); C.to_csv(V / 'independent_regret_recomputation.csv', index=False)
res['independent_regret_max_abs_diff'] = float(C.abs_diff_regret.max()); res['independent_vector_max_abs_diff'] = float(C.max_abs_diff_vector.max())
res['independent_ok'] = res['independent_regret_max_abs_diff'] <= 5e-7 + 1e-12 and res['independent_vector_max_abs_diff'] < 1e-9

# 5 scientific consistency
d = RG[(RG.strategy == 'A1') & RG.diagonal]
res['diagonal_A1_capture_is_1'] = bool(np.allclose(d.capture, 1, atol=1e-9))
res['offdiag_regret_nonnegative'] = bool((RG[(RG.strategy == 'A1') & ~RG.diagonal].norm_regret > -1e-9).all())
res['capture_le_1_all'] = bool((RG.capture.dropna() <= 1 + 1e-9).all())
res['replaced_in_0_1'] = bool(RG.replaced_fraction_vs_target_opt.between(-1e-9, 1 + 1e-9).all())
res['all_ok'] = all(v for k, v in res.items() if k.endswith('_ok') or k.startswith(('ids_', 'diagonal', 'offdiag', 'capture_le', 'replaced_in', 'regret_complete', 'x_in')))
(V / 'post_run_checks.json').write_text(json.dumps(res, indent=1, default=float) + '\n'); print(json.dumps(res, indent=1, default=float))
