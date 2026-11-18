"""P2-C3 preflight checks (criteria fixed in P2C3_PREFLIGHT_SELECTION.md before computation).
Usage: python -I p2c3_02_preflight_checks.py   (reads overlay/tiles, preflight/catchment_*.npz; writes preflight/preflight_checks.json + csvs)"""
import os, sys, json
from pathlib import Path
os.environ['OGR_GEOJSON_MAX_OBJ_SIZE'] = '0'
import numpy as np, pandas as pd, geopandas as gpd, shapely, pyogrio
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p2c3_overlay as O, p2c3_scores as S

R = O.R; OV = R / '05_Experiments/BHSI_v2_P2C3/overlay'; PF = R / '05_Experiments/BHSI_v2_P2C3/preflight'
sel = json.load(open(PF / 'preflight_selection.json')); CIDS = list(sel['chosen'].values()) + [19]
G = O.load_common(); el = G['el'].set_index('fragment_id'); ct = G['ct']
A = pd.read_csv(OV / 'reach_tile_assignment.csv'); C1T = pd.read_csv(O.C1 / 'p2c1_catchment_eligibility.csv').set_index('CaBA_ID')
res = {'catchments': {}, 'criteria': {}}
SRC = {'C': 'CORINE', 'LEn': 'LE', 'LEg': 'LE'}


def load_units(npz, kind):
    Z = np.load(npz); ids = Z[f'{kind}_ids']
    return ids, Z[f'{kind}_npx'], {a: Z[f'{kind}_cnt_{a}'] for a in ('C', 'LEn', 'LEg')}


rows = []; fails = []
for cid in CIDS:
    r = {}
    tiles = sorted(A.tile[A.CaBA_ID == cid].unique())
    # tiled results, gathered from every tile holding this catchment's reaches
    T = {}
    for kind in O.UNIT_KINDS:
        ids_l, npx_l, cnt_l = [], [], {a: [] for a in ('C', 'LEn', 'LEg')}
        for t in tiles:
            ids, npx, cnt = load_units(OV / 'tiles' / f'{t}.npz', kind)
            fr = np.array([i.split('#')[0] for i in ids]); m = el.loc[fr, 'CaBA_ID'].values == cid if len(fr) else np.zeros(0, bool)
            ids_l.append(ids[m]); npx_l.append(npx[m]); [cnt_l[a].append(cnt[a][m]) for a in cnt]
        T[kind] = (np.concatenate(ids_l), np.concatenate(npx_l), {a: np.concatenate(v) for a, v in cnt_l.items()})
    U = {kind: load_units(PF / f'catchment_{cid}.npz', kind) for kind in O.UNIT_KINDS}
    # 1 length conservation
    ids = T['B40'][0]; lk = el.loc[ids, 'length_m'].sum() / 1000
    r['c1_km_tiled'] = lk; r['c1_km_C1'] = float(C1T.eligible_km[cid]); r['c1_ok'] = abs(lk - C1T.eligible_km[cid]) < 1e-6
    seg_err = 0.0; seg_ids_ok = True
    for kind, sl in (('S1000', 1000.0), ('S500', 500.0)):
        exp_ids = []
        for f in ids:
            s = O.segments(el.geometry[f], el.length_m[f], sl)
            if s is None: continue
            seg_err = max(seg_err, abs(sum(g.length for g in s) - el.length_m[f])); exp_ids += [f'{f}#{k}' for k in range(len(s))]
        seg_ids_ok &= sorted(exp_ids) == sorted(T[kind][0])
    r['c1_segment_max_abs_err_m'] = seg_err; r['c1_segment_ids_match'] = bool(seg_ids_ok); r['c1_ok'] &= seg_err < 1e-6 and seg_ids_ok
    # 2/3 assignment, uniqueness, set equality
    c1ids = set(el.index[el.CaBA_ID == cid])
    r['c2_unique'] = len(ids) == len(set(ids)); r['c2_set_equal_C1'] = set(ids) == c1ids
    r['c2_tiles'] = tiles; r['c2_ok'] = r['c2_unique'] and r['c2_set_equal_C1']
    # 4-6 tiled vs untiled per unit
    det = {}
    for kind in O.UNIT_KINDS:
        ti, tn, tc = T[kind]; ui, un, uc = U[kind]
        o_t = np.argsort(ti); o_u = np.argsort(ui); assert (ti[o_t] == ui[o_u]).all(), f'{cid} {kind} unit sets differ'
        d = {'units': int(len(ti)), 'npx_identical': bool((tn[o_t] == un[o_u]).all())}
        for a in ('C', 'LEn', 'LEg'): d[f'{a}_counts_identical_units_pct'] = float(100 * (tc[a][o_t] == uc[a][o_u]).all(1).mean()) if len(ti) else 100.0
        if kind in ('B40',):
            lens = el.loc[ti[o_t], 'length_m'].values
            for a in ('C', 'LEn', 'LEg'):
                ct_ = S.compose(tc[a][o_t], ct, SRC[a]); cu_ = S.compose(uc[a][o_u], ct, SRC[a])
                for e in ('s_lo', 's_hi'):
                    dd = np.abs(np.nan_to_num(ct_[e].values, nan=-9) - np.nan_to_num(cu_[e].values, nan=-9))
                    d[f'{a}_{e}_lenw_mean_absdiff'] = float((dd * lens).sum() / lens.sum()); d[f'{a}_{e}_max_absdiff'] = float(dd.max())
                    d[f'{a}_{e}_pct_len_absdiff_gt_0.01'] = float(100 * lens[dd > 0.01].sum() / lens.sum())
                d[f'{a}_water_frac_identical'] = bool(np.array_equal(np.nan_to_num(ct_.water_frac.values), np.nan_to_num(cu_.water_frac.values)))
                d[f'{a}_zero_land_identical'] = bool(((ct_.land_px == 0) == (cu_.land_px == 0)).all())
                d[f'{a}_zero_land_km'] = float(lens[ct_.land_px.values == 0].sum() / 1000)
                d[f'{a}_RW_flag_pct_len'] = float(100 * lens[np.nan_to_num(ct_.water_frac.values) > 0.75].sum() / lens.sum())
                d[f'{a}_unknown_pct_of_land_lenw'] = float(100 * np.nansum(ct_.unknown_frac_of_land.values * lens) / lens.sum())
                if a == 'LEn':
                    nc = np.where(ct_.land_px > 0, ct_.nocov_px / ct_.land_px.replace(0, np.nan), 0)
                    d['LE_nocov_gt50pct_of_land_pct_len'] = float(100 * lens[np.nan_to_num(nc) > 0.5].sum() / lens.sum())
                    d['LE_nocov_pct_of_land_lenw'] = float(100 * np.nansum(nc * lens) / lens.sum())
                    d['LE_nocov_reaches_gt50pct'] = int((np.nan_to_num(nc) > 0.5).sum())
        det[kind] = d
    r['units'] = det
    b = det['B40']
    r['c4_ok'] = all(det[k]['npx_identical'] for k in det)
    r['c5_native_ok'] = all(det[k][f'{a}_counts_identical_units_pct'] == 100.0 for k in det for a in ('C', 'LEn'))
    r['c5_leg_ok'] = all(b[f'LEg_{e}_lenw_mean_absdiff'] <= 0.001 and b[f'LEg_{e}_pct_len_absdiff_gt_0.01'] <= 0.5 for e in ('s_lo', 's_hi'))
    r['c6_consistency_ok'] = all(b[f'{a}_water_frac_identical'] and b[f'{a}_zero_land_identical'] for a in ('C', 'LEn', 'LEg'))
    r['c6_RW_trigger_reached'] = any(b[f'{a}_RW_flag_pct_len'] > 2 for a in ('C', 'LEn', 'LEg'))
    r['c6_material_nocov_asymmetry'] = b['LE_nocov_gt50pct_of_land_pct_len'] > 2
    res['catchments'][int(cid)] = r
    for k in ('c1_ok', 'c2_ok', 'c4_ok', 'c5_native_ok', 'c5_leg_ok', 'c6_consistency_ok'):
        if not r[k]: fails.append(f'{cid}:{k}')
    if r['c6_material_nocov_asymmetry']: fails.append(f'{cid}:c6_material_nocov_asymmetry')

# 7 determinism
h1 = O.array_hash(OV / 'tiles/t012_003.npz'); h2 = O.array_hash(PF / 'determinism_t012_003.npz')
res['c7_determinism'] = {'tile': 't012_003', 'hash_run1': h1, 'hash_run2': h2, 'ok': h1 == h2}
if h1 != h2: fails.append('c7')

# 8a exact vector overlay of 40 m buffers, 100 seeded random reaches per catchment (CORINE, LE-native) vs tiled B40 counts
from pyproj import Transformer
rng = np.random.default_rng(20261117); vrows = []
kc, kl = G['keys']['C'], G['keys']['LE']
for cid in CIDS:
    pool_ids = np.array(sorted(el.index[el.CaBA_ID == cid])); pick = rng.choice(pool_ids, size=min(100, len(pool_ids)), replace=False)
    for f in pick:
        t = A.tile[A.fragment_id == f].iloc[0]; Z = np.load(OV / 'tiles' / f'{t}.npz'); j = np.flatnonzero(Z['B40_ids'] == f)[0]
        b = shapely.buffer(el.geometry[f], 40.0, quad_segs=16); bb = b.bounds
        le = pyogrio.read_dataframe(O.LE_PATH, bbox=bb, columns=['a_pred'])
        tr = Transformer.from_crs(27700, 3035, always_xy=True)
        cl = gpd.read_file(O.CLC_PATH, bbox=tr.transform_bounds(*bb, densify_pts=21)).to_crs(27700); cl['Code_18'] = cl.Code_18.astype(str)
        cl['geometry'] = shapely.make_valid(cl.geometry.values)
        for arm, gg, kk, keys in (('C', cl.geometry.values, cl.Code_18.values, kc), ('LEn', le.geometry.values, le.a_pred.values, kl)):
            ex = np.zeros(len(keys) + 1)
            if len(gg):
                ar = shapely.area(shapely.intersection(b, gg))
                for k, a_ in zip(kk, ar): ex[keys.index(k) + 1] += a_
            ras = Z[f'B40_cnt_{arm}'][j] * 100.0
            vrows.append({'CaBA_ID': cid, 'fragment_id': f, 'arm': arm, 'buffer_m2': b.area, 'abs_diff_pct_of_buffer': 100 * np.abs(ex[1:] - ras[1:]).sum() / b.area})
V = pd.DataFrame(vrows); V.to_csv(PF / 'preflight_vector_check.csv', index=False)
vs = V.groupby(['CaBA_ID', 'arm']).abs_diff_pct_of_buffer.agg(['mean', 'median', 'max']).round(3)
res['c8a_vector_check'] = {f'{k[0]}_{k[1]}': v for k, v in vs.to_dict('index').items()}
res['c8a_ok'] = bool((vs['mean'] < 2).all())
if not res['c8a_ok']: fails.append('c8a')

# 8b Derbyshire Derwent: tiled vs 8 Nov pilot reach table
P = pd.read_csv(R / '05_Experiments/BHSI_v2_P2C/c2/pilot_reach_table.csv').set_index('fragment_id')
ids, npx, cnt = [], [], {a: [] for a in ('C', 'LEn', 'LEg')}
for t in sorted(A.tile[A.CaBA_ID == 19].unique()):
    i_, n_, c_ = load_units(OV / 'tiles' / f'{t}.npz', 'B40'); m = el.loc[i_, 'CaBA_ID'].values == 19
    ids.append(i_[m]); npx.append(n_[m]); [cnt[a].append(c_[a][m]) for a in cnt]
ids = np.concatenate(ids); npx = np.concatenate(npx); P = P.loc[ids]
d8 = {'reaches': int(len(ids)), 'buffer_px_identical': bool((P.buffer_px.values == npx).all())}
lens = P.length_m.values
for a in ('C', 'LEn', 'LEg'):
    c = S.compose(np.concatenate(cnt[a]), ct, SRC[a])
    d8[f'{a}_land_px_identical'] = bool((P[f'{a}_land_px'].values == c.land_px.values).all())
    for e in ('lo', 'hi'):
        dd = np.abs(np.nan_to_num(P[f'{a}_score_{e}'].values, nan=-9) - np.nan_to_num(c[f's_{e}'].values, nan=-9))
        d8[f'{a}_s_{e}_max_absdiff'] = float(dd.max()); d8[f'{a}_s_{e}_lenw_mean_absdiff'] = float((dd * lens).sum() / lens.sum())
        d8[f'{a}_s_{e}_pct_len_absdiff_gt_0.01'] = float(100 * lens[dd > 0.01].sum() / lens.sum())
d8['ok'] = d8['buffer_px_identical'] and d8['C_land_px_identical'] and d8['LEn_land_px_identical'] and all(d8[f'{a}_s_{e}_max_absdiff'] < 1e-12 for a in ('C', 'LEn') for e in ('lo', 'hi')) \
    and all(d8[f'LEg_s_{e}_lenw_mean_absdiff'] <= 0.001 and d8[f'LEg_s_{e}_pct_len_absdiff_gt_0.01'] <= 0.5 for e in ('lo', 'hi'))
res['c8b_pilot_reproduction'] = d8
if not d8['ok']: fails.append('c8b')

# 3 inherited overlap (quantified, not edited)
IO = pd.read_csv(O.C1 / 'p2c1_inherited_overlaps.csv'); ee = IO[IO.both_eligible]
B5 = 0.05 * el.length_m.sum() / 1000; B1 = 0.01 * el.length_m.sum() / 1000
res['c3_inherited_overlap'] = {'pairs_both_eligible': int(len(ee)), 'overlap_km': float(ee.overlap_m.sum() / 1000),
                               'catchments': sorted(set(int(el.CaBA_ID[f]) for f in pd.concat([ee.fragment_a, ee.fragment_b]))),
                               'upper_bound_share_of_5pct_budget_pct': float(100 * ee.overlap_m.sum() / 1000 / B5), 'upper_bound_share_of_1pct_budget_pct': float(100 * ee.overlap_m.sum() / 1000 / B1)}
res['timing_s'] = {n: json.loads(str(np.load(PF / f'catchment_{c}.npz')['meta_json']))['timing_s']['total'] for c in CIDS for n in [f'untiled_{c}']}
res['tile_timing_s'] = {t: json.loads(str(np.load(OV / 'tiles' / f'{t}.npz')['meta_json']))['timing_s'] for t in sorted(set(A.tile[A.CaBA_ID.isin(CIDS)]))}
res['failures'] = fails; res['verdict'] = 'PASS' if not fails else 'FAIL'
(PF / 'preflight_checks.json').write_text(json.dumps(res, indent=1, default=lambda x: x.item() if hasattr(x, 'item') else str(x)) + '\n')
print(json.dumps({k: res[k] for k in ('failures', 'verdict', 'c7_determinism', 'c8a_ok', 'c3_inherited_overlap')}, indent=1, default=str))
for cid, r in res['catchments'].items(): print(cid, {k: v for k, v in r.items() if k.startswith('c')}); print('  B40', r['units']['B40'])
print('pilot', d8)
