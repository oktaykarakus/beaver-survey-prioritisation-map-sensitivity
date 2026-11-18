"""P2-C2 step 1: choose the pilot catchment BEFORE any CORINE-versus-Living-England comparison is computed.

PRE-SPECIFIED RULE (written before this script was run; the rule uses only: the P2-C1 eligibility table, catchment area, the P2-B
Living England *coverage* tables, and CORINE-only categories at eligible river midpoints. No Living England class, and no
CORINE/LE comparison of any kind, is read here).

Hard filters (all must hold):
  H1  P2-C1 status == ELIGIBLE (reportable and not flagged partial)
  H2  no Welsh length; outside-England/Wales length <= 1 % and England tidal length <= 1 % of the catchment network
      (no unresolved tidal or geographic eligibility ambiguity); eligible share >= 90 %
  H3  eligible length 600-1,600 km (substantial but manageable)
  H4  catchment area <= 2,500 km2 (raster size)
  H5  Living England coverage: no-segment share <= 0.5 % at random points and <= 0.5 % at river midpoints; CORINE no-match = 0
  H6  CORINE riparian-midpoint category shares (model categories) each >= 5 % of eligible length for woodland (BLW+CON+SCR),
      grassland (GRS) and agriculture (ARB+AGM)  -> 'meaningful woodland, agricultural and grassland variation'
Choice among survivors: the highest Shannon diversity (natural log) of CORINE model-category shares by length (a CORINE-only
quantity). Ties broken by smaller catchment id. The rule does not look at any source difference and cannot be tuned to one.

Usage: python -I p2c2_01_select_pilot.py <c1_dir> <out_dir>
"""
import os, sys, json, hashlib
from pathlib import Path
os.environ['OGR_GEOJSON_MAX_OBJ_SIZE'] = '0'
import numpy as np, pandas as pd, geopandas as gpd, shapely
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p2c_lc as L

R = Path(__file__).resolve().parents[2]
C1 = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
T = pd.read_csv(C1 / 'p2c1_catchment_eligibility.csv')
S = R / '05_Experiments/BHSI_v2_P2B/summaries'
rp = pd.read_csv(S / 'le_completeness_by_catchment_random_points.csv').set_index('CaBA_ID')
mp = pd.read_csv(S / 'le_gap_by_catchment_midpoints.csv').set_index('CaBA_ID')
T['le_nocov_pct_random_points'] = T.CaBA_ID.map(rp.le_unmatched_pct)
T['le_nocov_pct_midpoints'] = T.CaBA_ID.map(mp.unmatched_pct)
T['clc_nocov_pct_random_points'] = T.CaBA_ID.map(rp.clc_unmatched_pct)

pct = lambda c: 100 * T[c] / T.phase1_total_km
T['h1'] = T.status == 'ELIGIBLE'
T['h2'] = (T.km_wales == 0) & (pct('km_outside_england_wales') <= 1) & (pct('km_england_tidal') <= 1) & (T.eligible_share_pct >= 90)
T['h3'] = T.eligible_km.between(600, 1600)
T['h4'] = T.catchment_area_km2 <= 2500
T['h5'] = (T.le_nocov_pct_random_points <= 0.5) & (T.le_nocov_pct_midpoints <= 0.5) & (T.clc_nocov_pct_random_points == 0)
pre = T.h1 & T.h2 & T.h3 & T.h4 & T.h5

# CORINE-only category composition at eligible fragment midpoints, for catchments passing H1-H5
ct = L.class_table(R / '06_Results_Figures/BHSI_v2_P2B/P2B_ECOLOGICAL_CROSSWALK.csv')
cm = ct[ct.source == 'CORINE'].set_index('class_key').model_category
el = gpd.read_file(C1 / 'p2c1_eligible_network.gpkg', columns=['fragment_id', 'CaBA_ID', 'length_m'])
el = el[el.CaBA_ID.isin(T.CaBA_ID[pre])].copy()
mids = gpd.GeoDataFrame(el[['CaBA_ID', 'length_m']], geometry=shapely.line_interpolate_point(el.geometry.values, 0.5, normalized=True), crs=27700).to_crs(3035)
b = mids.total_bounds
clc = gpd.read_file(R / '05_Experiments/BHSI_v2_P2A/derived/clc2018_eea_recovered_3035.gpkg', bbox=tuple(b + np.array([-1e3, -1e3, 1e3, 1e3])), columns=['Code_18'])
j = gpd.sjoin(mids, clc, how='left', predicate='within').drop_duplicates(subset=None)
j = j[~j.index.duplicated(keep='first')]
j['cat'] = j.Code_18.astype(str).map(cm)
shares = j.groupby(['CaBA_ID', 'cat']).length_m.sum().unstack(fill_value=0)
nomatch = j.groupby('CaBA_ID').apply(lambda d: d.cat.isna().mean())
# land categories only (water excluded, rule R-W)
land = shares.drop(columns=[c for c in ['WATER'] if c in shares.columns])
sh = land.div(land.sum(axis=1), axis=0)
div = -(sh.where(sh > 0) * np.log(sh.where(sh > 0))).sum(axis=1)
D = pd.DataFrame({'woody_pct': 100 * sh[[c for c in ['BLW', 'CON', 'SCR'] if c in sh]].sum(axis=1), 'grass_pct': 100 * sh.get('GRS', 0), 'agri_pct': 100 * sh[[c for c in ['ARB', 'AGM'] if c in sh]].sum(axis=1),
                  'shannon_corine_categories': div, 'clc_midpoint_nomatch_frac': nomatch, 'water_pct_of_midpoints': 100 * shares.get('WATER', 0) / shares.sum(axis=1)})
T = T.merge(D, left_on='CaBA_ID', right_index=True, how='left')
T['h6'] = (T.woody_pct >= 5) & (T.grass_pct >= 5) & (T.agri_pct >= 5)
T['passes_all'] = pre & T.h6
cand = T[T.passes_all].sort_values(['shannon_corine_categories', 'CaBA_ID'], ascending=[False, True])
chosen = cand.iloc[0]
cols = ['CaBA_ID', 'CaBA_Catch', 'eligible_km', 'eligible_share_pct', 'catchment_area_km2', 'km_wales', 'km_england_tidal', 'km_outside_england_wales', 'le_nocov_pct_random_points', 'le_nocov_pct_midpoints',
        'woody_pct', 'grass_pct', 'agri_pct', 'shannon_corine_categories', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'passes_all']
T[cols].sort_values(['passes_all', 'shannon_corine_categories'], ascending=False).round(4).to_csv(OUT / 'pilot_selection_candidates_all107.csv', index=False)
res = {'rule': 'p2c2_01_select_pilot.py header', 'n_catchments': int(len(T)), 'n_pass_h1': int(T.h1.sum()), 'n_pass_h1_h5': int(pre.sum()), 'n_pass_all': int(T.passes_all.sum()),
       'chosen_CaBA_ID': int(chosen.CaBA_ID), 'chosen_name': chosen.CaBA_Catch, 'chosen_row': {k: (float(v) if isinstance(v, (np.floating, float)) else (bool(v) if isinstance(v, (np.bool_, bool)) else (int(v) if isinstance(v, np.integer) else v))) for k, v in chosen[cols].items()},
       'runner_up': cand.iloc[1][['CaBA_ID', 'CaBA_Catch', 'shannon_corine_categories']].astype(str).to_dict() if len(cand) > 1 else None,
       'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(OUT / 'pilot_selection.json').write_text(json.dumps(res, indent=1) + '\n')
print(json.dumps({k: v for k, v in res.items() if k != 'chosen_row'}, indent=1)); print(cand[cols[:14]].head(8).to_string())
