"""P2-D Task 4: effect of continuing LE-G25 to convergence in the 6 capped tiles on LE-G25 reach scores and on the P2-C3 headline
decision metrics. Replaces LEg counts for reaches of those tiles only (B40 primary units); C and LEn are unchanged by construction.
Uses the verified P2-C3 libraries (p2c3_scores.compose, p2c3_alloc) read-only. Writes 05_Experiments/BHSI_v2_P2D/grain_continuation/
grain_effect.json and reach_score_changes.csv."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / '04_BHSI_v2_Development/p2c3')); sys.path.insert(0, str(R / '04_BHSI_v2_Development/p2c'))
import p2c3_scores as S, p2c3_alloc as A, p2c_lc as Lc
GC = R / '05_Experiments/BHSI_v2_P2D/grain_continuation'; OV = R / '05_Experiments/BHSI_v2_P2C3/overlay/tiles'
TILES = ['t005_000', 't005_002', 't006_009', 't007_008', 't007_009', 't012_004']
ct = Lc.class_table(R / '06_Results_Figures/BHSI_v2_P2B/P2B_ECOLOGICAL_CROSSWALK.csv')
T0 = pd.read_parquet(R / '05_Experiments/BHSI_v2_P2C3/analysis/reach_table_B40.parquet'); T1 = T0.copy()
pos = pd.Series(np.arange(len(T0)), index=T0.fragment_id); res = {'tiles': {}}
for t in TILES:
    Zn = np.load(GC / f'{t}.npz'); Zo = np.load(OV / f'{t}.npz')
    mn = json.loads(str(Zn['meta_json'])); mo = json.loads(str(Zo['meta_json']))
    assert (Zn['B40_ids'] == Zo['B40_ids']).all() and (Zn['B40_cnt_C'] == Zo['B40_cnt_C']).all() and (Zn['B40_cnt_LEn'] == Zo['B40_cnt_LEn']).all()
    first5_same = all(abs(a['frac_changed_vs_previous'] - b['frac_changed_vs_previous']) < 1e-15 for a, b in zip(mn['grain_control_cycles'][:5], mo['grain_control_cycles']))
    i = pos[Zn['B40_ids']].values; c = S.compose(Zn['B40_cnt_LEg'], ct, 'LE')
    for col in ('s_lo', 's_hi', 'woody', 'land_px', 'water_px', 'water_frac'): T1.loc[i, f'LEg_{col}'] = c[col].values
    res['tiles'][t] = {'cycles_total': len(mn['grain_control_cycles']), 'cycle_changes_pct': [round(100 * x['frac_changed_vs_previous'], 5) for x in mn['grain_control_cycles']],
                       'converged': mn['grain_control_cycles'][-1]['frac_changed_vs_previous'] < 1e-4, 'cycles_1_to_5_reproduce_p2c3': first5_same,
                       'reaches': int(len(i)), 'reach_LEg_counts_changed': int((Zn['B40_cnt_LEg'] != Zo['B40_cnt_LEg']).any(1).sum())}
L = T0.length_m.values; catch = T0.CaBA_ID.values; n = len(T0)
d = {e: (T1[f'LEg_s_{e}'] - T0[f'LEg_s_{e}']).abs().fillna(0).values for e in ('lo', 'hi')}
aff = T0.tile.isin(TILES).values
res['score_change'] = {e: {'reaches_changed': int((d[e] > 0).sum()), 'max_abs': float(d[e].max()), 'lenw_mean_abs_affected_tiles': float((d[e] * L)[aff].sum() / L[aff].sum()),
                           'pct_len_affected_tiles_gt_0.01': float(100 * L[aff & (d[e] > 0.01)].sum() / L[aff].sum())} for e in ('lo', 'hi')}
pd.DataFrame({'fragment_id': T0.fragment_id, 'tile': T0.tile, 'd_LEg_s_lo': d['lo'], 'd_LEg_s_hi': d['hi']})[aff].to_csv(GC / 'reach_score_changes.csv', index=False)
perm = np.random.default_rng(20261117).permutation(n)
def scen(T): return {f'{a}_{e}': T[f'{a}_s_{e}'].values for a in ('C', 'LEg', 'LEn') for e in ('lo', 'hi')}
def metrics(T, f):
    s = scen(T); B = f * L.sum(); X = {j: A.a1_reach(s[j], L, B, perm) for j in s}; ov = {j: A.value(X[j], s[j], L) for j in s}
    rf = lambda a, b: A.overlap(X[a], X[b], L, B)['replaced_fraction']; rg = lambda a, b: A.capture(X[a], s[b], L, B, ov[b])[1]
    DR = np.mean([rf('C_lo', 'LEg_lo'), rf('C_hi', 'LEg_hi')]); DRN = np.mean([rf('C_lo', 'LEn_lo'), rf('C_hi', 'LEn_hi')])
    core = float((np.min(np.vstack([X[j] for j in ('C_lo', 'C_hi', 'LEg_lo', 'LEg_hi')]), 0) * L).sum() / B)
    return {'D_R': DR, 'D_A': np.mean([rf('C_lo', 'C_hi'), rf('LEg_lo', 'LEg_hi')]), 'D_G': np.mean([rf('LEn_lo', 'LEg_lo'), rf('LEn_hi', 'LEg_hi')]), 'persistence': DR / DRN,
            'regret_C_lo_to_LEg_lo': rg('C_lo', 'LEg_lo'), 'regret_LEg_lo_to_C_lo': rg('LEg_lo', 'C_lo'), 'regret_C_hi_to_LEg_hi': rg('C_hi', 'LEg_hi'), 'regret_LEg_hi_to_C_hi': rg('LEg_hi', 'C_hi'),
            'core_share': core}, X
for f in (0.01, 0.05, 0.10):
    m0, X0 = metrics(T0, f); m1, X1 = metrics(T1, f); B = f * L.sum()
    res[f'budget_{f*100:g}'] = {'p2c3': m0, 'continued': m1, 'abs_diff': {k: abs(m1[k] - m0[k]) for k in m0},
                                'LEg_lo_allocation_replaced_fraction_p2c3_vs_continued': A.overlap(X0['LEg_lo'], X1['LEg_lo'], L, B)['replaced_fraction'],
                                'LEg_hi_allocation_replaced_fraction_p2c3_vs_continued': A.overlap(X0['LEg_hi'], X1['LEg_hi'], L, B)['replaced_fraction']}
# cutoff proximity at 5%: LEg cutoff score and affected reaches near it
B = 0.05 * L.sum(); s0 = scen(T0)
for e in ('lo', 'hi'):
    j = f'LEg_{e}'; x = A.a1_reach(s0[j], L, B, perm); cut = float(np.nan_to_num(s0[j])[(x > 0) & (x < 1)][0]) if ((x > 0) & (x < 1)).any() else float(np.nan_to_num(s0[j])[x > 0].min())
    near = aff & (np.abs(np.nan_to_num(s0[j]) - cut) <= np.maximum(d[e], 1e-12)) & (d[e] > 0)
    res[f'cutoff_{j}'] = {'cutoff_score': cut, 'affected_reaches_whose_change_spans_cutoff': int(near.sum()), 'their_km': float(L[near].sum() / 1000),
                          'pct_of_budget_selected_in_affected_tiles': float(100 * (x * L)[aff].sum() / B)}
(GC / 'grain_effect.json').write_text(json.dumps(res, indent=1, default=float) + '\n'); print(json.dumps(res, indent=1, default=float))
