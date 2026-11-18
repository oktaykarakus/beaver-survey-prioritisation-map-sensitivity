"""P2-C1: build the England-only eligible river network from the corrected Phase 1 network (read-only input).

Usage: python -I p2c_01_eligible_network.py <out_dir>
Inputs (all read-only, hashed into the output manifest):
  05_Experiments/BHSI_v2_Phase1/native_001/canonical_native_rivers.gpkg   Phase 1 canonical pieces (94,162; 82,669.77 km)
  01_BHSI_v1_Frozen/source_snapshot/data/Rivers/Data/oprvrs_gb.gpkg         OS Open Rivers watercourse_link `form`
  05_Experiments/BHSI_v2_P2B/data_raw/ons_countries/ctry23_BFC_EW_27700.geojson   ONS Countries Dec 2023 BFC (England, Wales)
  Wild_Beaver_Catchments_England_*.geojson + catchments_107.csv             107 CaBA catchments (as in Phase 1)
Outputs in <out_dir>: eligible / excluded GeoPackages, catchment table, reconciliation, reason register, checks.
No land-cover value or suitability score is read anywhere in this script.
"""
import os, sys, json, time, hashlib
from pathlib import Path
os.environ['OGR_GEOJSON_MAX_OBJ_SIZE'] = '0'
import numpy as np, pandas as pd, geopandas as gpd, shapely, pyogrio
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p2c_net as N

R = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1]).resolve()
if R / '05_Experiments' not in OUT.parents and OUT != R / '05_Experiments':
    raise ValueError('output must be inside 05_Experiments/')
OUT.mkdir(parents=True, exist_ok=True)
t0 = time.time()
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(16 << 20), b''): h.update(b)
    return h.hexdigest()

D = R / '01_BHSI_v1_Frozen/source_snapshot/data'
P1 = R / '05_Experiments/BHSI_v2_Phase1/native_001/canonical_native_rivers.gpkg'
OSG = D / 'Rivers/Data/oprvrs_gb.gpkg'
ONS = R / '05_Experiments/BHSI_v2_P2B/data_raw/ons_countries/ctry23_BFC_EW_27700.geojson'
CAB = next(D.rglob('Wild_Beaver_Catchments_England_*.geojson'))
C107 = R / '05_Experiments/P1_5_Portability/script/catchments_107.csv'
inputs = {k: {'path': str(v.relative_to(R)), 'sha256': sha(v)} for k, v in dict(phase1_network=P1, os_open_rivers=OSG, ons_countries=ONS, caba_catchments=CAB, catchments_107=C107).items()}
log('inputs hashed')

# ---- load -------------------------------------------------------------------------------------------------------
r = gpd.read_file(P1)
assert r.crs.to_epsg() == 27700 and len(r) == 94162 and r.piece_id.is_unique
assert r.geometry.notna().all() and r.geometry.is_valid.all() and (r.geometry.length > 0).all()
form = pyogrio.read_dataframe(OSG, layer='watercourse_link', read_geometry=False, columns=['id', 'form'])
assert form.id.is_unique
r = r.merge(form, on='id', how='left', validate='m:1')
assert r.form.notna().all() and set(r.form) <= N.KNOWN_FORMS, set(r.form)
total_in_m = float(r.length_m.sum())
ct = gpd.read_file(ONS).set_crs(27700, allow_override=True)
ENG = ct.geometry[ct.CTRY23NM == 'England'].iloc[0]; WAL = ct.geometry[ct.CTRY23NM == 'Wales'].iloc[0]
cat = gpd.read_file(CAB).to_crs(27700); cat.geometry = cat.geometry.buffer(0)
base = pd.read_csv(C107).set_index('CaBA_ID'); ids = list(base.index)
cat = cat.set_index('CaBA_ID').loc[ids]
assert len(ids) == 107 and set(r.CaBA_ID) <= set(ids)

# ---- geometric split (E2) ---------------------------------------------------------------------------------------
log('splitting by country (England precedence on shared border)')
parts, n_cut = N.classify_and_split(r.geometry.values, ENG, WAL)
log('pieces cut at a country boundary:', n_cut)
rows = []
for i, ps in enumerate(parts):
    p = r.iloc[i]
    for k, (geo, g) in enumerate(ps):
        rows.append((p.piece_id, k, int(p.source_row), int(p.id) if str(p.id).isdigit() else p.id, int(p.CaBA_ID), p.form, geo, g, float(p.length_m)))
fr = gpd.GeoDataFrame(pd.DataFrame(rows, columns=['parent_piece_id', 'frag_k', 'source_row', 'os_id', 'CaBA_ID', 'form', 'geo', 'geometry', 'parent_length_m']), geometry='geometry', crs=27700)
fr['length_m'] = fr.geometry.length
fr['fragment_id'] = fr.parent_piece_id + '|' + fr.frag_k.astype(str)
fr['geo'] = fr.geo.map({'ENGLAND': 'ENGLAND', 'WALES': 'WALES', 'OTHER': 'OTHER'})
assert fr.fragment_id.is_unique

# ---- E1, E3 and reason codes ------------------------------------------------------------------------------------
e12 = (fr.geo == 'ENGLAND') & (fr.form == 'inlandRiver')
cat_km = fr.loc[e12].groupby('CaBA_ID').length_m.sum().reindex(ids).fillna(0) / 1000
reportable = cat_km >= N.MIN_CATCH_KM
fr['catchment_reportable'] = fr.CaBA_ID.map(reportable)
reasons = [N.reasons_for(g, f, ok) for g, f, ok in zip(fr.geo, fr.form, fr.catchment_reportable)]
fr['reasons_all'] = [';'.join(x) for x in reasons]
fr['reason_primary'] = [x[0] if x else '' for x in reasons]
fr['eligible'] = fr.reason_primary == ''
assert (fr.eligible == (e12 & fr.catchment_reportable)).all()   # reason codes agree with the rule definition
log('eligible km', fr.length_m[fr.eligible].sum() / 1000)

# ---- integrity checks -------------------------------------------------------------------------------------------
checks = []
def check(name, ok, value, tol=None):
    checks.append({'check': name, 'passed': bool(ok), 'value': value if isinstance(value, (int, float, str)) else json.dumps(value, default=float), 'tolerance': tol})
    log(('PASS ' if ok else 'FAIL ') + name, value)
sum_frag = float(fr.length_m.sum())
per_parent = fr.groupby('parent_piece_id').length_m.sum().reindex(r.piece_id.values)
dev = (per_parent.values - r.length_m.values)
check('length conservation, total (m)', abs(sum_frag - total_in_m) < 1e-3, sum_frag - total_in_m, '<1e-3 m on 82.7e6 m')
check('length conservation, max per-parent abs deviation (m)', np.abs(dev).max() < 1e-4, float(np.abs(dev).max()), '<1e-4 m')
check('every parent piece has >=1 fragment', per_parent.notna().all(), int(per_parent.isna().sum()))
check('fragment geometries valid, non-empty, LineString, positive', bool(fr.geometry.is_valid.all() and (~fr.geometry.is_empty).all() and (fr.geom_type == 'LineString').all() and (fr.length_m > 0).all()), len(fr))
check('fragment ids unique', fr.fragment_id.is_unique, len(fr))
chg = fr.groupby('parent_piece_id').CaBA_ID.nunique().max()
check('catchment id inherited unchanged (1 per parent)', chg == 1, int(chg))
# eligible fragments lie in England (closed polygon, 1 cm tolerance)
el = fr[fr.eligible]
shapely.prepare(ENG)
within = shapely.covers(ENG, el.geometry.values)       # prepared predicate; exact test
resid = 0.0
for g in el.geometry.values[~within]:                    # numerical noding noise: measure the length lying outside England
    b = g.bounds; win = shapely.clip_by_rect(ENG, b[0] - 50, b[1] - 50, b[2] + 50, b[3] + 50)
    resid += shapely.difference(g, win).length
check('eligible geometry inside England (length outside, m)', resid < 0.01, {'fragments_not_exactly_covered': int((~within).sum()), 'length_outside_m': resid}, '<0.01 m in total')
# catchment assignment: fragment midpoint falls in its catchment polygon (1 m tolerance)
mid = shapely.line_interpolate_point(fr.geometry.values, 0.5, normalized=True)
ok = np.zeros(len(fr), bool)
for cid, ix in fr.groupby('CaBA_ID').indices.items():
    poly = cat.geometry.loc[cid].buffer(1.0); shapely.prepare(poly)
    ok[ix] = shapely.contains(poly, mid[ix])
check('fragment midpoint inside assigned catchment polygon (1 m)', ok.mean() > 0.9999, {'inside_pct': float(100 * ok.mean()), 'outside_n': int((~ok).sum()), 'outside_km': float(fr.length_m[~ok].sum() / 1000)}, '>99.99%')
# no double counting: collinear overlap (to 5 mm) between different pieces, measured on the Phase 1 parents and on the fragments.
# Overlaps already present in the frozen Phase 1 network are inherited and flagged (never edited); P2-C1 must not create new ones.
def overlap_pairs(geoms, tol=0.005):
    tree = shapely.STRtree(geoms); a, b = tree.query(geoms, predicate='dwithin', distance=tol); m = a < b; a, b = a[m], b[m]
    buf = shapely.buffer(geoms[b], tol, cap_style='flat')
    ov = shapely.length(shapely.intersection(geoms[a], buf))
    k = ov > 0.5      # <0.5 m is junction geometry (flat-cap buffer catches the first mm of a touching neighbour)
    return a[k], b[k], ov[k], int(len(a))
pa, pb, pov, npairs_p = overlap_pairs(r.geometry.values)
fa, fb, fov, npairs_f = overlap_pairs(fr.geometry.values)
parent_overlap_m = float(pov.sum()); frag_overlap_m = float(fov.sum())
fr['inherited_overlap_flag'] = False
fr.loc[np.unique(np.r_[fa, fb]), 'inherited_overlap_flag'] = True
elig_pairs = fr.eligible.values[fa] & fr.eligible.values[fb]
pd.DataFrame({'fragment_a': fr.fragment_id.values[fa], 'fragment_b': fr.fragment_id.values[fb], 'overlap_m': fov, 'form_a': fr.form.values[fa], 'form_b': fr.form.values[fb],
              'both_eligible': elig_pairs, 'parent_a': fr.parent_piece_id.values[fa], 'parent_b': fr.parent_piece_id.values[fb]}).to_csv(OUT / 'p2c1_inherited_overlaps.csv', index=False)
check('no NEW collinear overlap created by P2-C1 (fragment overlap - Phase 1 parent overlap, m; 5 mm buffer, pairs >0.5 m)', frag_overlap_m - parent_overlap_m < 0.05,
      {'parent_overlap_m': parent_overlap_m, 'parent_pairs': int(len(pa)), 'fragment_overlap_m': frag_overlap_m, 'fragment_pairs': int(len(fa)), 'of_which_both_eligible_m': float(fov[elig_pairs].sum()), 'candidate_pairs_checked': npairs_f})
check('eligible length >= 95% of P2B midpoint reference 71,632.7 km (NO-GO trigger is >5% change)', abs(fr.length_m[fr.eligible].sum() / 1000 / 71632.7 - 1) < 0.05, float(fr.length_m[fr.eligible].sum() / 1000))

# ---- fragments at borders: detect zig-zag from rivers that follow the national border ---------------------------------
short = fr.length_m < 1.0
border_note = {'fragments_lt_1m': int(short.sum()), 'km_fragments_lt_1m': float(fr.length_m[short].sum() / 1000), 'pieces_cut': int(n_cut),
               'pieces_with_gt1_fragment': int((fr.groupby('parent_piece_id').size() > 1).sum())}

# ---- outputs ----------------------------------------------------------------------------------------------------
fr['length_km'] = fr.length_m / 1000
cols = ['fragment_id', 'parent_piece_id', 'frag_k', 'source_row', 'os_id', 'CaBA_ID', 'form', 'geo', 'catchment_reportable', 'eligible', 'reason_primary', 'reasons_all', 'inherited_overlap_flag', 'length_m', 'geometry']
_ord = {p: i for i, p in enumerate(r.piece_id)}
fr = fr.assign(_o=fr.parent_piece_id.map(_ord)).sort_values(['_o', 'frag_k'], kind='stable').drop(columns='_o').reset_index(drop=True)
elig = fr[fr.eligible][cols[:-3] + ['inherited_overlap_flag', 'length_m', 'geometry']].drop(columns=['reason_primary', 'reasons_all', 'eligible'])
excl = fr[~fr.eligible][cols]
elig.to_file(OUT / 'p2c1_eligible_network.gpkg', layer='eligible', driver='GPKG')
excl.to_file(OUT / 'p2c1_excluded_network.gpkg', layer='excluded', driver='GPKG')
log('geopackages written', len(elig), len(excl))

km = lambda m: float(m.sum() / 1000)
# catchment table (all 107)
def agg(sel): return fr[sel].groupby('CaBA_ID').length_m.sum().reindex(ids).fillna(0) / 1000
T = pd.DataFrame({'CaBA_ID': ids, 'CaBA_Catch': base.CaBA_Catch.values})
T['catchment_area_km2'] = (cat.geometry.area / 1e6).values
T['phase1_total_km'] = agg(fr.length_m > 0).values
T['km_wales'] = agg(fr.geo == 'WALES').values
T['km_outside_england_wales'] = agg(fr.geo == 'OTHER').values
eng = fr.geo == 'ENGLAND'
T['km_england_tidal'] = agg(eng & (fr.form == 'tidalRiver')).values
T['km_england_canal'] = agg(eng & (fr.form == 'canal')).values
T['km_england_lake_link'] = agg(eng & (fr.form == 'lake')).values
T['km_england_inland_river'] = agg(eng & (fr.form == 'inlandRiver')).values
T['reportable_ge10km'] = T.km_england_inland_river >= N.MIN_CATCH_KM
T['eligible_km'] = agg(fr.eligible).values
T['km_excluded_catchment_below_min'] = agg(eng & (fr.form == 'inlandRiver') & ~fr.catchment_reportable).values
T['eligible_share_pct'] = 100 * T.eligible_km / T.phase1_total_km
T['partial_coverage_flag_lt50pct'] = T.reportable_ge10km & (T.eligible_share_pct < 50)
T['n_eligible_fragments'] = fr[fr.eligible].groupby('CaBA_ID').size().reindex(ids).fillna(0).astype(int).values
T['status'] = np.where(~T.reportable_ge10km, 'NOT_ASSESSABLE (<10 km eligible)', np.where(T.partial_coverage_flag_lt50pct, 'ELIGIBLE_PARTIAL (<50% of network)', 'ELIGIBLE'))
ref = pd.read_csv(R / '05_Experiments/BHSI_v2_P2B/summaries/eligibility_components_by_catchment.csv').set_index('CaBA_ID')
T['p2b_midpoint_england_inland_km'] = ref.england_inland_km.reindex(ids).values
T['clip_minus_midpoint_km'] = T.km_england_inland_river - T.p2b_midpoint_england_inland_km
T['p2b_midpoint_wales_km'] = ref.wales_km.reindex(ids).values
T['wales_clip_minus_midpoint_km'] = T.km_wales - T.p2b_midpoint_wales_km
p1f = pd.read_csv(R / '05_Experiments/BHSI_v2_Phase1/native_001/native_catchment_features.csv').set_index('CaBA_ID')
T['phase1_native_length_km'] = (p1f.length_m / 1000).reindex(ids).values
T['total_minus_phase1_km'] = T.phase1_total_km - T.phase1_native_length_km
check('per-catchment total equals Phase 1 catchment length (max abs km)', T.total_minus_phase1_km.abs().max() < 1e-6, float(T.total_minus_phase1_km.abs().max()), '<1e-6 km')
check('catchment table partitions every catchment (components sum to total, max abs km)', (T[['km_wales', 'km_outside_england_wales', 'km_england_tidal', 'km_england_canal', 'km_england_lake_link', 'km_england_inland_river']].sum(axis=1) - T.phase1_total_km).abs().max() < 1e-6, float((T[['km_wales', 'km_outside_england_wales', 'km_england_tidal', 'km_england_canal', 'km_england_lake_link', 'km_england_inland_river']].sum(axis=1) - T.phase1_total_km).abs().max()))
T.round(6).to_csv(OUT / 'p2c1_catchment_eligibility.csv', index=False)

# reason register
reg = []
for code in N.PRECEDENCE:
    anyc = fr.reasons_all.str.split(';').map(lambda x: code in x)
    prim = fr.reason_primary == code
    reg.append({'precedence': N.PRECEDENCE.index(code) + 1, 'reason_code': code, 'fragments_primary': int(prim.sum()), 'km_primary': km(fr.length_m[prim]),
                'fragments_any': int(anyc.sum()), 'km_any_applicable': km(fr.length_m[anyc])})
reg.append({'precedence': 0, 'reason_code': '(eligible)', 'fragments_primary': int(fr.eligible.sum()), 'km_primary': km(fr.length_m[fr.eligible]), 'fragments_any': int(fr.eligible.sum()), 'km_any_applicable': km(fr.length_m[fr.eligible])})
G = pd.DataFrame(reg)
G['pct_of_network_primary'] = 100 * G.km_primary / (total_in_m / 1000)
G.round(6).to_csv(OUT / 'p2c1_exclusion_reason_register.csv', index=False)

# length reconciliation (stages)
ref_json = json.load(open(R / '05_Experiments/BHSI_v2_P2B/summaries/country_attribution.json'))
P2B = {'total': ref_json['total_km'], 'wales_all_forms': ref_json['km_by_country'].get('Wales'), 'eligible': ref_json['eligible_primary_km']}
L = []
def lr(stage, component, kmv, ref_km=None, tol_km=None, note=''):
    L.append({'stage': stage, 'component': component, 'km': kmv, 'pct_of_phase1_network': 100 * kmv / (total_in_m / 1000), 'p2b_midpoint_reference_km': ref_km,
              'difference_km': None if ref_km is None else kmv - ref_km, 'difference_pct_of_reference': None if ref_km in (None, 0) else 100 * (kmv - ref_km) / ref_km, 'note': note})
lr('0 input', 'Phase 1 canonical network (94,162 pieces)', total_in_m / 1000, P2B['total'], note='from native_001 gpkg; reference is the P2-B total')
lr('1 after geometric split', 'sum of all fragments', sum_frag / 1000, total_in_m / 1000, note='conservation: must equal input')
for g, lab in [('ENGLAND', 'England'), ('WALES', 'Wales'), ('OTHER', 'Outside England and Wales (seaward of MHW / other)')]:
    lr('1 country split', lab, km(fr.length_m[fr.geo == g]), P2B['wales_all_forms'] if g == 'WALES' else None, note='England has precedence on the shared border')
for f in ['inlandRiver', 'tidalRiver', 'canal', 'lake']:
    x = fr.length_m[(fr.geo == 'ENGLAND') & (fr.form == f)]
    refv = {'inlandRiver': ref_json['km_by_country_form'].get('England|inlandRiver'), 'tidalRiver': ref_json['km_by_country_form'].get('England|tidalRiver'),
            'canal': ref_json['km_by_country_form'].get('England|canal'), 'lake': ref_json['km_by_country_form'].get('England|lake')}[f]
    lr('2 England by OS form', f'England | {f}', km(x), refv)
lr('3 catchment threshold', 'England inlandRiver in catchments <10 km (excluded, CATCH_BELOW_MIN)', km(fr.length_m[(fr.reason_primary == 'CATCH_BELOW_MIN')]), None, note='Humber Estuary, Your Tidal Thames')
lr('4 result', 'ELIGIBLE network', km(fr.length_m[fr.eligible]), P2B['eligible'], note='verification reference, not a target')
lr('4 result', 'EXCLUDED network (all reasons)', km(fr.length_m[~fr.eligible]), total_in_m / 1000 - P2B['eligible'])
lr('4 result', 'eligible + excluded', km(fr.length_m), total_in_m / 1000, note='conservation')
pd.DataFrame(L).round(6).to_csv(OUT / 'p2c1_length_reconciliation.csv', index=False)

# welsh/cross-border focus
foc = T[T.CaBA_Catch.str.contains('Wye|Severn Uplands|Middle Dee|Tidal Dee|Teme', regex=True)][['CaBA_ID', 'CaBA_Catch', 'phase1_total_km', 'km_wales', 'p2b_midpoint_wales_km', 'wales_clip_minus_midpoint_km', 'km_england_inland_river', 'p2b_midpoint_england_inland_km', 'clip_minus_midpoint_km', 'eligible_km', 'eligible_share_pct', 'status']]
foc.round(3).to_csv(OUT / 'p2c1_cross_border_focus.csv', index=False)

summary = {'total_km': total_in_m / 1000, 'eligible_km': km(fr.length_m[fr.eligible]), 'eligible_pct': 100 * km(fr.length_m[fr.eligible]) / (total_in_m / 1000),
           'eligible_fragments': int(fr.eligible.sum()), 'excluded_fragments': int((~fr.eligible).sum()),
           'catchments_total': 107, 'catchments_reportable': int(T.reportable_ge10km.sum()), 'catchments_partial_flag': int(T.partial_coverage_flag_lt50pct.sum()),
           'not_assessable': T.loc[~T.reportable_ge10km, 'CaBA_Catch'].tolist(), 'border': border_note, 'inherited_overlap_m_total': frag_overlap_m, 'inherited_overlap_m_both_eligible': float(fov[elig_pairs].sum()),
           'sens_threshold_5km_catchments': int((cat_km >= 5).sum()), 'sens_threshold_25km_catchments': int((cat_km >= 25).sum()),
           'seconds': time.time() - t0, 'all_checks_pass': all(c['passed'] for c in checks), 'inputs': inputs}
(OUT / 'p2c1_summary.json').write_text(json.dumps(summary, indent=1, default=float) + '\n')
pd.DataFrame(checks).to_csv(OUT / 'p2c1_checks.csv', index=False)
# canonical content hash (determinism test): attribute table + WKB geometry, independent of GPKG container bytes
h = hashlib.sha256()
for gdf in (elig, excl):
    for fid, geo_wkb, ln in zip(gdf.fragment_id.values, shapely.to_wkb(gdf.geometry.values), gdf.length_m.values):
        h.update(f'{fid}|{ln:.9f}|'.encode()); h.update(geo_wkb)
(OUT / 'p2c1_content_hash.txt').write_text(h.hexdigest() + '\n')
log('done', round(time.time() - t0), 's; all checks pass:', summary['all_checks_pass'])
