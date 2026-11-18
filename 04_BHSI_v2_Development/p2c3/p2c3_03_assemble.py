"""P2-C3 assemble the national reach-level analytical dataset from tile outputs, with completeness and conservation checks.
Usage: python -I p2c3_03_assemble.py   (reads overlay/tiles/*.npz; writes analysis/reach_table_B40.parquet, units_*.parquet, pooled.npz,
assemble_checks.json). Fails loudly on any check failure."""
import os, sys, json
from pathlib import Path
import numpy as np, pandas as pd, shapely
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p2c3_overlay as O, p2c3_scores as S

OV = O.R / '05_Experiments/BHSI_v2_P2C3/overlay'; AN = O.R / '05_Experiments/BHSI_v2_P2C3/analysis'; AN.mkdir(exist_ok=True)
G = O.load_common(); el = G['el']; ct = G['ct']
P = pd.read_csv(OV / 'tile_plan.csv'); A = pd.read_csv(OV / 'reach_tile_assignment.csv')
chk = {}
SRC = {'C': 'CORINE', 'LEn': 'LE', 'LEg': 'LE'}
units = {k: {'ids': [], 'npx': [], 'C': [], 'LEn': [], 'LEg': []} for k in O.UNIT_KINDS}
pair, wpair = [], []
pool = None; metas = {}
for t in P.tile:
    p = OV / 'tiles' / f'{t}.npz'; assert p.exists(), f'missing tile {t}'
    Z = np.load(p); m = json.loads(str(Z['meta_json'])); assert m['code_hash'] == O.CODE_HASH, f'{t} code hash differs'
    metas[t] = m
    for k in O.UNIT_KINDS:
        units[k]['ids'].append(Z[f'{k}_ids']); units[k]['npx'].append(Z[f'{k}_npx'])
        for a in ('C', 'LEn', 'LEg'): units[k][a].append(Z[f'{k}_cnt_{a}'])
    pair.append(Z['B40_pair']); wpair.append(Z['B40_woodypair'])
    arrs = {k: Z[k] for k in Z.files if k.startswith('pool_')}
    pool = arrs if pool is None else {k: pool[k] + arrs[k] for k in pool}
np.savez_compressed(AN / 'pooled.npz', **pool)
for k in units:
    for f in ('ids', 'npx', 'C', 'LEn', 'LEg'): units[k][f] = np.concatenate(units[k][f])
pair = np.concatenate(pair); wpair = np.concatenate(wpair)

# ---- completeness, uniqueness, conservation ----
ids = units['B40']['ids']
chk['n_reaches'] = int(len(ids)); chk['unique'] = bool(len(set(ids)) == len(ids)); chk['set_equal_C1'] = bool(set(ids) == set(el.fragment_id))
E = el.set_index('fragment_id').loc[ids]
tot = E.length_m.sum() / 1000; chk['eligible_km'] = float(tot); chk['eligible_km_diff_vs_71629.864'] = float(tot - 71629.86351928947)
C1T = pd.read_csv(O.C1 / 'p2c1_catchment_eligibility.csv').set_index('CaBA_ID')
d = E.groupby('CaBA_ID').length_m.sum() / 1000 - C1T.eligible_km[C1T.reportable_ge10km.astype(bool)]
chk['catchments'] = int(E.CaBA_ID.nunique()); chk['max_catchment_km_diff'] = float(d.abs().max())
chk['tiles'] = int(len(P)); chk['reaches_per_tile_match_plan'] = bool(all((A.tile == t).sum() == metas[t]['n_reaches'] for t in P.tile))
assert chk['unique'] and chk['set_equal_C1'] and abs(chk['eligible_km_diff_vs_71629.864']) < 1e-6 and chk['max_catchment_km_diff'] < 1e-6 and chk['catchments'] == 105 and chk['reaches_per_tile_match_plan'], chk

# ---- national B40 reach table ----
geo = pd.Series(E.geometry.values)
mid = shapely.line_interpolate_point(E.geometry.values, 0.5, normalized=True)
T = pd.DataFrame({'fragment_id': ids, 'parent_piece_id': E.parent_piece_id.values, 'CaBA_ID': E.CaBA_ID.values, 'length_m': E.length_m.values,
                  'tile': A.set_index('fragment_id').tile.loc[ids].values, 'x': shapely.get_x(mid), 'y': shapely.get_y(mid), 'buffer_px': units['B40']['npx']})
import pyogrio
gr = pyogrio.read_dataframe(O.R / '05_Experiments/BHSI_v2_Phase1/native_001/canonical_native_rivers.gpkg', read_geometry=False, columns=['piece_id', 'gradient_pct', 'gradient_score']).set_index('piece_id')
T['gradient_pct'] = gr.gradient_pct.reindex(T.parent_piece_id).values; T['gradient_score'] = gr.gradient_score.reindex(T.parent_piece_id).values
chk['gradient_missing'] = int(T.gradient_score.isna().sum())
for a in ('C', 'LEn', 'LEg'):
    c = S.compose(units['B40'][a], ct, SRC[a]); cc = S.compose(units['B40'][a], ct, SRC[a], unknown='conditional')
    assert (c.buffer_px.values == T.buffer_px.values).all()
    for col in c.columns:
        if col != 'buffer_px': T[f'{a}_{col}'] = c[col].values
    T[f'{a}_s_lo_cond'] = cc.s_lo.values; T[f'{a}_s_hi_cond'] = cc.s_hi.values
for k, (p_, q_) in enumerate((('C', 'LEn'), ('C', 'LEg'), ('LEn', 'LEg'))):
    T[f'{p_}_{q_}_common_px'] = pair[:, k, 0]; T[f'{p_}_{q_}_agree_px'] = pair[:, k, 1]
for k, (p_, q_) in enumerate((('C', 'LEn'), ('C', 'LEg'))):
    T[f'{p_}_{q_}_woody_common_px'] = wpair[:, k, 0]; T[f'{p_}_{q_}_woody_agree_px'] = wpair[:, k, 1]
T = T.sort_values('fragment_id').reset_index(drop=True)
T.to_parquet(AN / 'reach_table_B40.parquet', index=False)

# ---- sensitivity unit tables ----
Lm = el.set_index('fragment_id').length_m; Cm = el.set_index('fragment_id').CaBA_ID
for k in ('B20', 'B100', 'S1000', 'S500'):
    u = units[k]; fr = np.array([i.split('#')[0] for i in u['ids']])
    if k.startswith('S'):
        sl = 1000.0 if k == 'S1000' else 500.0
        # fragments not split reuse their B40 unit
        n = np.ceil(Lm.loc[fr].values / sl); seglen = Lm.loc[fr].values / n
        keep = T.length_m.values <= sl
        D = pd.DataFrame({'unit_id': np.r_[u['ids'], T.fragment_id.values[keep]], 'fragment_id': np.r_[fr, T.fragment_id.values[keep]],
                          'length_m': np.r_[seglen, T.length_m.values[keep]]})
        cnts = {a: np.vstack([u[a], units['B40'][a][np.argsort(ids)][keep]]) for a in ('C', 'LEn', 'LEg')}
        assert np.array_equal(np.sort(ids), T.fragment_id.values)
    else:
        D = pd.DataFrame({'unit_id': u['ids'], 'fragment_id': fr, 'length_m': Lm.loc[fr].values}); cnts = {a: u[a] for a in ('C', 'LEn', 'LEg')}
    D['CaBA_ID'] = Cm.loc[D.fragment_id].values
    for a in ('C', 'LEn', 'LEg'):
        c = S.compose(cnts[a], ct, SRC[a])
        for col in ('s_lo', 's_hi', 'woody', 'land_px', 'water_frac'): D[f'{a}_{col}'] = c[col].values
    chk[f'{k}_units'] = int(len(D)); chk[f'{k}_km_diff'] = float(D.length_m.sum() / 1000 - tot)
    assert abs(chk[f'{k}_km_diff']) < 1e-6, (k, chk[f'{k}_km_diff'])
    D.sort_values('unit_id').reset_index(drop=True).to_parquet(AN / f'units_{k}.parquet', index=False)

chk['tile_seconds_total'] = float(sum(m['timing_s']['total'] for m in metas.values()))
chk['tile_seconds_by_step'] = {s: float(sum(m['timing_s'][s] for m in metas.values())) for s in ('rasterise', 'grain_control', 'units', 'pooled')}
chk['grain_control_cycles_max'] = int(max(len(m['grain_control_cycles']) for m in metas.values()))
chk['grain_control_last_change_max'] = float(max(m['grain_control_cycles'][-1]['frac_changed_vs_previous'] for m in metas.values()))
chk['le_nodata_px_total'] = int(sum(m['le_nodata_px'] for m in metas.values()))
chk['code_hash'] = O.CODE_HASH
(AN / 'assemble_checks.json').write_text(json.dumps(chk, indent=1) + '\n'); print(json.dumps(chk, indent=1))
