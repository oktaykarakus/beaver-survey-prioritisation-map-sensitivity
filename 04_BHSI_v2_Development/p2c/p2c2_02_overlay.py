"""P2-C2 step 2: riparian land-cover composition for the pilot catchment from CORINE 2018 (recovered), Living England IV (native) and
Living England IV with the 25 ha / 100 m grain control (LE-G25), all evaluated on ONE common 10 m raster and ONE set of 40 m buffers
of the P2-C1 eligible reaches. Nothing here is a national ranking or an allocation.

Usage: python -I p2c2_02_overlay.py <c1_dir> <c2_dir>
Refuses to run unless P2C2_PILOT_SELECTION.md exists (selection documented first); records its hash.
"""
import os, sys, json, time, hashlib
from pathlib import Path
os.environ['OGR_GEOJSON_MAX_OBJ_SIZE'] = '0'
import numpy as np, pandas as pd, geopandas as gpd, shapely, pyogrio, rasterio
from rasterio.transform import Affine
from rasterio.features import rasterize
from pyproj import Transformer
from scipy import ndimage as ndi, stats
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p2c_lc as L

t0 = time.time()
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
R = Path(__file__).resolve().parents[2]
C1 = Path(sys.argv[1]); C2 = Path(sys.argv[2])
SEL = R / '06_Results_Figures/BHSI_v2_P2C/P2C2_PILOT_SELECTION.md'
assert SEL.exists(), 'pilot selection must be documented before the overlay'
sel = json.load(open(C2 / 'pilot_selection.json')); PID = sel['chosen_CaBA_ID']
assert SEL.stat().st_mtime < time.time()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
prov = {'pilot_selection_md_sha256': sha(SEL), 'class_table_sha256': sha(C2 / 'class_treatment_table_FROZEN.csv'), 'pilot_catchment': PID}

CW = R / '06_Results_Figures/BHSI_v2_P2B/P2B_ECOLOGICAL_CROSSWALK.csv'
ct = L.class_table(CW)
frozen = pd.read_csv(C2 / 'class_treatment_table_FROZEN.csv', dtype={'class_key': str})
assert (frozen.class_key.values == ct.class_key.values).all() and (frozen.model_category.values == ct.model_category.values).all()
NC = len(L.CATS); IDX = {c: i + 1 for i, c in enumerate(L.CATS)}; W, U = IDX['WATER'], IDX['UNK']
keys_c, lut_c, tc = L.label_maps(ct, 'CORINE'); keys_l, lut_l, tl = L.label_maps(ct, 'LE')

# ---- domain and eligible reaches -------------------------------------------------------------------------------------
el = gpd.read_file(C1 / 'p2c1_eligible_network.gpkg')
el = el[el.CaBA_ID == PID].reset_index(drop=True)
ctch = gpd.read_file(next((R / '01_BHSI_v1_Frozen/source_snapshot/data').rglob('Wild_Beaver_Catchments_England_*.geojson'))).to_crs(27700)
cpoly = ctch[ctch.CaBA_ID == PID].geometry.buffer(0).union_all()
RES = 10.0; MARGIN = 3000.0
bx = cpoly.bounds
x0 = np.floor((bx[0] - MARGIN) / RES) * RES; y1 = np.ceil((bx[3] + MARGIN) / RES) * RES
x1 = np.ceil((bx[2] + MARGIN) / RES) * RES; y0 = np.floor((bx[1] - MARGIN) / RES) * RES
H, Wd = int((y1 - y0) / RES), int((x1 - x0) / RES)
TR = Affine(RES, 0, x0, 0, -RES, y1)
log(f'catchment {PID}: {len(el)} eligible fragments, {el.length_m.sum()/1000:.1f} km; raster {H}x{Wd} = {H*Wd/1e6:.1f} M px')

# ---- rasterise the two products ---------------------------------------------------------------------------------------
LE = R / '05_Experiments/BHSI_v2_P2B/data_raw/living_england_p4/extracted/Living_England_Habitat_Map_Phase_4.gpkg'
CLC = R / '05_Experiments/BHSI_v2_P2A/derived/clc2018_eea_recovered_3035.gpkg'
le = pyogrio.read_dataframe(LE, bbox=(x0, y0, x1, y1), columns=['a_pred'])
assert le.a_pred.notna().all(), 'LE segments without a primary class'
unk_le = set(le.a_pred) - set(keys_l); assert not unk_le, unk_le
lab_le = L.rasterise_polys(le.geometry.values[::-1], [keys_l.index(k) + 1 for k in le.a_pred.values[::-1]], TR, (H, Wd))
tr = Transformer.from_crs(27700, 3035, always_xy=True)
b3 = tr.transform_bounds(x0, y0, x1, y1, densify_pts=21)
clc = gpd.read_file(CLC, bbox=b3).to_crs(27700)
clc['Code_18'] = clc.Code_18.astype(str)
unk_c = set(clc.Code_18) - set(keys_c); assert not unk_c, unk_c
n_inv = int((~clc.geometry.is_valid).sum())
if n_inv: clc['geometry'] = shapely.make_valid(clc.geometry.values)
lab_c = L.rasterise_polys(clc.geometry.values[::-1], [keys_c.index(k) + 1 for k in clc.Code_18.values[::-1]], TR, (H, Wd))
log(f'LE segments {len(le)}, CORINE polygons {len(clc)} (invalid fixed {n_inv}); LE nodata px {(lab_le==0).sum()}, CORINE nodata px {(lab_c==0).sum()}')

# catchment mask (pixel centres) for patch statistics
cmask = rasterize([(cpoly, 1)], out_shape=(H, Wd), transform=TR, fill=0, dtype='uint8').astype(bool)

# ---- grain control (primary) and dose-response -------------------------------------------------------------------------
log('grain control LE-G25 (min 2500 px = 25 ha, disk radius 5 px, i.e. objects >= 110 m wide are retained; 90 m as sensitivity, 8-connected)')
lab_leg, gc_log = L.grain_control(lab_le, 2500, 5, max_cycles=5)
for g in gc_log: log('  cycle', g)
variants = {}
def run_variant(name, min_px, rad, cyc=3):
    if rad == 0: v = L.sieve_min_area(lab_le, min_px) if min_px > 0 else lab_le.copy()
    else: v, _ = L.grain_control(lab_le, min_px, rad, max_cycles=cyc)
    variants[name] = v
run_variant('sieve_1ha_only', 100, 0); run_variant('sieve_5ha_only', 500, 0); run_variant('sieve_25ha_only', 2500, 0); run_variant('sieve_100ha_only', 10000, 0)
run_variant('width110m_only', 0, 5, 1)
run_variant('full_25ha_90m', 2500, 4.5); run_variant('full_5ha_110m', 500, 5); run_variant('full_100ha_110m', 10000, 5)
log('idempotence control: apply the same G25 to rasterised CORINE')
lab_cg, cg_log = L.grain_control(lab_c, 2500, 5, max_cycles=3)

cat = {'C': lut_c[lab_c], 'LEn': lut_l[lab_le], 'LEg': lut_l[lab_leg]}
nat = {'C': lab_c, 'LEn': lab_le, 'LEg': lab_leg}
cat_var = {k: lut_l[v] for k, v in variants.items()}
cat_cg = lut_c[lab_cg]
ARMS = ['C', 'LEn', 'LEg']
KEYS = {'C': keys_c, 'LEn': keys_l, 'LEg': keys_l}
TAB = {'C': tc, 'LEn': tl, 'LEg': tl}

# ---- per-reach 40 m buffer counts on the common raster ----------------------------------------------------------------
geoms = el.geometry.values
nreach = len(el)
cnt = {a: np.zeros((nreach, len(KEYS[a]) + 1), np.int64) for a in ARMS}
nbuf = np.zeros(nreach, np.int64); union = np.zeros((H, Wd), bool)
pair = {('C', 'LEn'): np.zeros((nreach, 2), np.int64), ('C', 'LEg'): np.zeros((nreach, 2), np.int64), ('LEn', 'LEg'): np.zeros((nreach, 2), np.int64)}
for i, g in enumerate(geoms):
    b = g.buffer(40.0); mnx, mny, mxx, mxy = b.bounds
    c0 = int(np.floor((mnx - x0) / RES)); c1 = int(np.ceil((mxx - x0) / RES)); r0 = int(np.floor((y1 - mxy) / RES)); r1 = int(np.ceil((y1 - mny) / RES))
    wt = Affine(RES, 0, x0 + c0 * RES, 0, -RES, y1 - r0 * RES)
    m = rasterize([(b, 1)], out_shape=(r1 - r0, c1 - c0), transform=wt, fill=0, dtype='uint8').astype(bool)
    nbuf[i] = m.sum()
    union[r0:r1, c0:c1] |= m
    for a in ARMS: cnt[a][i] = np.bincount(nat[a][r0:r1, c0:c1][m], minlength=len(KEYS[a]) + 1)
    cs = {a: cat[a][r0:r1, c0:c1][m] for a in ARMS}
    for (p, q), arr in pair.items():
        both = (cs[p] > 0) & (cs[p] != W) & (cs[p] != U) & (cs[q] > 0) & (cs[q] != W) & (cs[q] != U)
        arr[i] = (int(both.sum()), int((both & (cs[p] == cs[q])).sum()))
log('reach buffers done; union support', int(union.sum()), 'px =', union.sum() * 1e-4, 'km2')

# centreline mask (all-touched), for comparison with the P2-B centreline statistic
cl = rasterize(((g, 1) for g in geoms), out_shape=(H, Wd), transform=TR, fill=0, dtype='uint8', all_touched=True).astype(bool)

# ---- exact-vector validation of the raster composition (native arms) --------------------------------------------------
rng = np.random.default_rng(20261108); vi = rng.choice(nreach, size=min(150, nreach), replace=False)
vt_c = shapely.STRtree(clc.geometry.values); vt_l = shapely.STRtree(le.geometry.values)
val = []
for i in vi:
    b = geoms[i].buffer(40.0)
    for a, tree, gg, kk, ky in (('C', vt_c, clc.geometry.values, clc.Code_18.values, keys_c), ('LEn', vt_l, le.geometry.values, le.a_pred.values, keys_l)):
        ix = tree.query(b, predicate='intersects'); ar = shapely.area(shapely.intersection(b, gg[ix]))
        ex = np.zeros(len(ky) + 1)
        for j, area in zip(ix, ar): ex[ky.index(kk[j]) + 1] += area
        ras = cnt[a][i] * RES * RES
        val.append({'reach': i, 'arm': a, 'buffer_area_m2': b.area, 'abs_diff_m2_total': float(np.abs(ex[1:] - ras[1:]).sum()), 'vector_covered_m2': float(ex.sum()), 'raster_covered_m2': float(ras.sum())})
V = pd.DataFrame(val); V['abs_diff_pct_of_buffer'] = 100 * V.abs_diff_m2_total / V.buffer_area_m2
V.to_csv(C2 / 'validation_raster_vs_vector.csv', index=False)

# ---- composition, scores ----------------------------------------------------------------------------------------------
def lo_hi(a):
    t = TAB[a]; lo = np.r_[np.nan, t.lo.values]; hi = np.r_[np.nan, t.hi.values]; wa = np.r_[False, (t.model_category == 'WATER').values]; un = np.r_[True, (t.model_category == 'UNK').values]
    return lo, hi, wa, un
reach = pd.DataFrame({'fragment_id': el.fragment_id, 'CaBA_ID': PID, 'length_m': el.length_m, 'buffer_px': nbuf})
for a in ARMS:
    lo, hi, wa, un = lo_hi(a); c = cnt[a]
    water = c[:, wa].sum(axis=1); land = nbuf - water; unk = c[:, un].sum(axis=1)       # label 0 (no coverage) counts as unknown
    known = land - unk
    lo0 = np.where(np.isnan(lo), 0, lo); hi0 = np.where(np.isnan(hi), 0, hi)
    s_lo = (c[:, 1:] * lo0[1:]).sum(axis=1) / np.where(land > 0, land, np.nan)
    s_hi = ((c[:, 1:] * hi0[1:]).sum(axis=1) + c[:, 0]) / np.where(land > 0, land, np.nan)   # unknown (incl. label 0) -> 1 at the upper bound
    reach[f'{a}_water_frac'] = water / nbuf; reach[f'{a}_unknown_frac_of_land'] = unk / np.where(land > 0, land, np.nan); reach[f'{a}_land_px'] = land
    reach[f'{a}_score_lo'] = s_lo; reach[f'{a}_score_hi'] = s_hi
    cc = np.zeros((nreach, NC + 1), np.int64)
    for k, tcat in enumerate(TAB[a].model_category.values): cc[:, IDX[tcat]] += c[:, k + 1]
    cc[:, 0] = c[:, 0]
    for j, cn in enumerate(L.CATS): reach[f'{a}_cat_{cn}_px'] = cc[:, j + 1]
    woody = cc[:, [IDX[x] for x in L.WOODY]].sum(axis=1)
    reach[f'{a}_woody_share_of_land'] = woody / np.where(land > 0, land, np.nan)
for (p, q), arr in pair.items():
    reach[f'{p}_{q}_common_land_px'] = arr[:, 0]; reach[f'{p}_{q}_disagree_frac'] = 1 - arr[:, 1] / np.where(arr[:, 0] > 0, arr[:, 0], np.nan)
mid = shapely.line_interpolate_point(geoms, 0.5, normalized=True)
reach['x'] = shapely.get_x(mid); reach['y'] = shapely.get_y(mid)
reach.to_csv(C2 / 'pilot_reach_table.csv', index=False)
zero_den = {a: int((reach[f'{a}_land_px'] == 0).sum()) for a in ARMS}
zero_den_km = {a: float(reach.length_m[reach[f'{a}_land_px'] == 0].sum() / 1000) for a in ARMS}

# long comparison table: native class level and model-category level, pooled over the union support (each pixel once) and per-reach length-weighted
rows = []
def pooled_counts(a):
    return np.bincount(nat[a][union], minlength=len(KEYS[a]) + 1)
for a in ARMS:
    c = pooled_counts(a); lo, hi, wa, un = lo_hi(a); t = TAB[a]
    land = c.sum() - c[wa].sum(); tot = c.sum()
    cw = np.zeros(NC + 1)
    for k, tcat in enumerate(t.model_category.values): cw[IDX[tcat]] += c[k + 1]
    for k, key in enumerate(KEYS[a]):
        if c[k + 1] == 0: continue
        rows.append({'arm': a, 'level': 'native_class', 'key': key, 'name': t.class_name[k], 'model_category': t.model_category[k], 'water_sub': t.water_sub[k], 'is_interval': bool(t.is_interval[k]), 'lo': t.lo[k], 'hi': t.hi[k],
                     'pooled_area_ha': c[k + 1] * 0.01, 'pct_of_buffer_area': 100 * c[k + 1] / tot, 'pct_of_land': np.nan if wa[k + 1] else 100 * c[k + 1] / land})
    if c[0]: rows.append({'arm': a, 'level': 'native_class', 'key': '(no coverage)', 'name': 'no source polygon', 'model_category': 'UNK', 'water_sub': '', 'is_interval': False, 'lo': 0.0, 'hi': 1.0, 'pooled_area_ha': c[0] * 0.01, 'pct_of_buffer_area': 100 * c[0] / tot, 'pct_of_land': 100 * c[0] / land})
    for j, cn in enumerate(L.CATS):
        if cw[j + 1] == 0: continue
        rows.append({'arm': a, 'level': 'model_category', 'key': cn, 'name': cn, 'model_category': cn, 'water_sub': '', 'is_interval': cn in L.INTERVAL_CAT, 'lo': np.nan, 'hi': np.nan, 'pooled_area_ha': cw[j + 1] * 0.01,
                     'pct_of_buffer_area': 100 * cw[j + 1] / tot, 'pct_of_land': np.nan if cn == 'WATER' else 100 * cw[j + 1] / land})
    w = reach.length_m.values; ok = reach[f'{a}_land_px'].values > 0
    for j, cn in enumerate(L.CATS):
        if cn == 'WATER': continue
        sh = reach[f'{a}_cat_{cn}_px'].values / np.where(reach[f'{a}_land_px'].values > 0, reach[f'{a}_land_px'].values, np.nan)
        rows.append({'arm': a, 'level': 'model_category_reach_length_weighted_mean', 'key': cn, 'name': cn, 'model_category': cn, 'is_interval': cn in L.INTERVAL_CAT, 'pct_of_land': 100 * np.nansum(sh * w) / w[ok].sum()})
pd.DataFrame(rows).round(5).to_csv(C2 / 'P2C2_LANDCOVER_COMPARISON.csv', index=False)

# ---- pixel-level agreement on the union support and on the centreline -------------------------------------------------
def confusion(p, q, mask, cp=None, cq=None):
    cp = cat[p] if cp is None else cp; cq = cat[q] if cq is None else cq
    a = cp[mask].astype(np.int64); b = cq[mask].astype(np.int64)
    return np.bincount(a * (NC + 1) + b, minlength=(NC + 1) ** 2).reshape(NC + 1, NC + 1)
def summarise(Mx):
    names = ['(none)'] + L.CATS
    both_land = [i for i in range(1, NC + 1) if i not in (W, U)]
    sub = Mx[np.ix_(both_land, both_land)]; n = sub.sum(); agree = np.trace(sub)
    pa = sub.sum(1) / n; pb = sub.sum(0) / n; pe = (pa * pb).sum()
    wd_c = Mx[W, :].sum(); wd_l = Mx[:, W].sum(); both_w = Mx[W, W]
    tot = Mx.sum()
    wood = [IDX[x] - 1 for x in L.WOODY]; gi = [both_land.index(IDX[x]) for x in L.WOODY]
    wsub = np.array([[sub[np.ix_(gi, gi)].sum(), sub[np.ix_(gi, [k for k in range(len(both_land)) if k not in gi])].sum()], [sub[np.ix_([k for k in range(len(both_land)) if k not in gi], gi)].sum(), sub[np.ix_([k for k in range(len(both_land)) if k not in gi], [k for k in range(len(both_land)) if k not in gi])].sum()]])
    return {'n_total_px': int(tot), 'n_common_known_land_px': int(n), 'agreement': float(agree / n), 'kappa': float((agree / n - pe) / (1 - pe)), 'woody_binary_agreement': float(np.trace(wsub) / wsub.sum()),
            'water_in_first_only_pct': float(100 * (wd_c - both_w) / tot), 'water_in_second_only_pct': float(100 * (wd_l - both_w) / tot), 'water_in_both_pct': float(100 * both_w / tot),
            'unknown_or_nocov_in_either_pct_of_non_water': float(100 * (Mx[U, :].sum() + Mx[:, U].sum() - Mx[U, U] + Mx[0, :].sum() + Mx[:, 0].sum() - Mx[0, 0]) / max(1, tot - wd_c - wd_l + both_w))}
agree = {}; confs = {}
for p, q in [('C', 'LEn'), ('C', 'LEg'), ('LEn', 'LEg')]:
    for scope, mask in (('buffer_union', union), ('centreline', cl)):
        Mx = confusion(p, q, mask); confs[(p, q, scope)] = Mx
        agree[f'{p}|{q}|{scope}'] = summarise(Mx)
for (p, q, scope), Mx in confs.items():
    names = ['(none)'] + L.CATS
    pd.DataFrame(Mx, index=[f'{p}:{n}' for n in names], columns=[f'{q}:{n}' for n in names]).to_csv(C2 / f'confusion_{p}_{q}_{scope}.csv')
# per-category correspondence (row-normalised, CORINE as the row)
pc = []
for q in ('LEn', 'LEg'):
    Mx = confs[('C', q, 'buffer_union')]
    for i, cn in enumerate(L.CATS):
        r = Mx[i + 1]; tot_r = r.sum()
        if tot_r == 0 or cn in ('WATER',): continue
        pc.append({'comparison': f'C vs {q}', 'corine_category': cn, 'corine_px': int(tot_r), 'pct_same_category_in_other': 100 * r[i + 1] / tot_r, 'pct_water_in_other': 100 * r[W] / tot_r, 'pct_woody_in_other': 100 * r[[IDX[x] for x in L.WOODY]].sum() / tot_r})
pd.DataFrame(pc).round(3).to_csv(C2 / 'corine_category_correspondence.csv', index=False)

# ---- dose-response and idempotence ------------------------------------------------------------------------------------
dr = []
def agree_with_c(catx, mask):
    a = cat['C'][mask]; b = catx[mask]; ok = (a > 0) & (a != W) & (a != U) & (b > 0) & (b != W) & (b != U)
    return float((a[ok] == b[ok]).mean()), int(ok.sum())
for name, cx in [('LEn (native)', cat['LEn'])] + [(k, v) for k, v in cat_var.items()] + [('LEg (25 ha + 100 m, primary)', cat['LEg'])]:
    ag, n = agree_with_c(cx, union); agc, _ = agree_with_c(cx, cl)
    wt = float((cx[union] == W).mean())
    dr.append({'le_variant': name, 'agreement_with_corine_buffer': ag, 'agreement_with_corine_centreline': agc, 'water_pct_of_buffer': 100 * wt, 'common_px': n})
pd.DataFrame(dr).round(5).to_csv(C2 / 'grain_dose_response.csv', index=False)
# idempotence: how much does G25 change CORINE itself?
chg = float(((lab_cg != lab_c) & (lab_c > 0)).sum() / (lab_c > 0).sum()); chg_u = float(((lab_cg != lab_c) & union).sum() / union.sum())
# patch statistics inside the catchment polygon
ps = {}
for name, lab in (('CORINE', lab_c), ('LE native', lab_le), ('LE-G25', lab_leg), ('CORINE after G25', lab_cg)):
    a = L.patch_stats(lab, 100.0, cmask); ar = cmask.sum() * 100.0
    ps[name] = {'n_patches': int(len(a)), 'patches_per_100km2': float(len(a) / (ar / 1e8)), 'median_patch_ha': float(np.median(a) / 1e4), 'p10_ha': float(np.percentile(a, 10) / 1e4), 'p90_ha': float(np.percentile(a, 90) / 1e4),
                'share_of_area_in_patches_lt_25ha_pct': float(100 * a[a < 2.5e5].sum() / a.sum()), 'narrow_fraction_r5_pct': float(100 * L.narrow_fraction(np.where(cmask, lab, 0).astype(np.uint8), 5))}
    log('patch stats', name, ps[name])
pd.DataFrame(ps).T.round(4).to_csv(C2 / 'patch_statistics.csv')

# ---- spatial structure of disagreement (Moran's I, k=8 nearest reaches, 999 permutations, seeded) ----------------------------
def moran(xy, v, w, k=8, nperm=999, seed=1):
    ok = np.isfinite(v); xy, v = xy[ok], v[ok]
    tree = cKDTree(xy); _, nb = tree.query(xy, k=k + 1); nb = nb[:, 1:]
    z = v - v.mean(); I = lambda zz: (len(zz) / (k * len(zz))) * (zz[:, None] * zz[nb]).sum() / (zz ** 2).sum() * 1.0
    obs = I(z); rng = np.random.default_rng(seed); perm = np.array([I(rng.permutation(z)) for _ in range(nperm)])
    return float(obs), float((1 + (perm >= obs).sum()) / (nperm + 1))
sp = {}
xy = reach[['x', 'y']].values
for col in ['C_LEn_disagree_frac', 'C_LEg_disagree_frac', 'C_score_lo', 'LEn_score_lo']:
    v = reach[col].values.astype(float); I, p = moran(xy, v, None); sp[col] = {'morans_I_knn8': I, 'p_perm_999': p}
reach['grid5km'] = (np.floor(reach.x / 5000).astype(int).astype(str) + '_' + np.floor(reach.y / 5000).astype(int).astype(str))
g = reach.groupby('grid5km').apply(lambda d: pd.Series({'km': d.length_m.sum() / 1000, 'disagree_C_LEn': np.average(d.C_LEn_disagree_frac.fillna(0), weights=d.length_m), 'disagree_C_LEg': np.average(d.C_LEg_disagree_frac.fillna(0), weights=d.length_m),
                                                         'woody_C': np.nanmean(d.C_woody_share_of_land), 'woody_LEn': np.nanmean(d.LEn_woody_share_of_land), 'woody_LEg': np.nanmean(d.LEg_woody_share_of_land)}))
g.round(4).to_csv(C2 / 'spatial_disagreement_by_5km_cell.csv')
# dominant CORINE category -> disagreement
dom = reach[[f'C_cat_{c}_px' for c in L.CATS if c not in ('WATER', 'UNK')]].idxmax(axis=1).str.replace('C_cat_', '').str.replace('_px', '')
dd = reach.assign(dominant_corine_category=dom).groupby('dominant_corine_category').apply(lambda d: pd.Series({'reaches': len(d), 'km': d.length_m.sum() / 1000, 'disagree_C_LEn': np.average(d.C_LEn_disagree_frac.fillna(0), weights=d.length_m), 'disagree_C_LEg': np.average(d.C_LEg_disagree_frac.fillna(0), weights=d.length_m)}))
dd.round(4).to_csv(C2 / 'disagreement_by_dominant_corine_category.csv')

summary = {'provenance': prov, 'raster': {'rows': H, 'cols': Wd, 'res_m': RES, 'origin_x': x0, 'origin_y_top': y1, 'margin_m': MARGIN}, 'n_reaches': nreach, 'eligible_km': float(el.length_m.sum() / 1000),
           'union_support_km2': float(union.sum() * 1e-4), 'centreline_px': int(cl.sum()), 'le_segments': int(len(le)), 'clc_polygons': int(len(clc)), 'clc_invalid_fixed': n_inv,
           'le_nodata_px_in_domain': int((lab_le == 0).sum()), 'corine_nodata_px_in_domain': int((lab_c == 0).sum()),
           'zero_denominator_reaches': zero_den, 'zero_denominator_km': zero_den_km, 'validation_raster_vs_vector': V.groupby('arm').abs_diff_pct_of_buffer.agg(['mean', 'median', 'max']).to_dict(),
           'validation_raster_vs_vector_covered_ratio': V.assign(r=V.raster_covered_m2 / V.vector_covered_m2).groupby('arm').r.agg(['mean', 'min', 'max']).to_dict(),
           'agreement': agree, 'grain_control_cycles': gc_log, 'corine_G25_cycles': cg_log, 'corine_changed_by_G25_frac_domain': chg, 'corine_changed_by_G25_frac_buffer_union': chg_u,
           'patch_statistics': ps, 'spatial_autocorrelation': sp, 'seconds': time.time() - t0}
(C2 / 'pilot_summary.json').write_text(json.dumps(summary, indent=1, default=float) + '\n')
# grids for reproducibility checks (compressed): category rasters of the three arms
np.savez_compressed(C2 / 'pilot_category_rasters.npz', C=cat['C'], LEn=cat['LEn'], LEg=cat['LEg'], union=union, origin=np.array([x0, y1, RES]), cats=np.array(['(none)'] + L.CATS))
log('done', round(time.time() - t0), 's')
