"""P2-C3 preflight catchment selection. Geometry only (no land cover); rules in 06_Results_Figures/BHSI_v2_P2C3/P2C3_PREFLIGHT_SELECTION.md.
Usage: python -I p2c3_00_select_preflight.py <out_dir>"""
import os, sys, json
from pathlib import Path
os.environ['OGR_GEOJSON_MAX_OBJ_SIZE'] = '0'
import numpy as np, pandas as pd, geopandas as gpd, shapely

R = Path(__file__).resolve().parents[2]; OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
assert (R / '06_Results_Figures/BHSI_v2_P2C3/P2C3_PREFLIGHT_SELECTION.md').exists(), 'rules must be recorded first'
C1 = R / '05_Experiments/BHSI_v2_P2C/c1'
el = gpd.read_file(C1 / 'p2c1_eligible_network.gpkg')
ex = gpd.read_file(C1 / 'p2c1_excluded_network.gpkg')
cat = pd.read_csv(C1 / 'p2c1_catchment_eligibility.csv')
rep = set(cat.CaBA_ID[cat.reportable_ge10km.astype(bool)])
ct = gpd.read_file(R / '05_Experiments/BHSI_v2_P2B/data_raw/ons_countries/ctry23_BFC_EW_27700.geojson').set_crs(27700, allow_override=True)
eng = ct.geometry[ct.CTRY23NM == 'England'].iloc[0]; wal = ct.geometry[ct.CTRY23NM == 'Wales'].iloc[0]
border = shapely.intersection(eng.boundary, wal.buffer(1.0))           # E-W land boundary as a line set
poly = gpd.read_file(next((R / '01_BHSI_v1_Frozen/source_snapshot/data').rglob('Wild_Beaver_Catchments_England_*.geojson'))).to_crs(27700)
poly['geometry'] = poly.geometry.buffer(0)


def km_within(geoms, target, d):
    """Eligible length lying within distance d of target (length of intersection with target buffer)."""
    zone = shapely.buffer(target, d); shapely.prepare(zone)
    return shapely.length(shapely.intersection(geoms, zone)) / 1000.0


el['km_near_border'] = km_within(el.geometry.values, border, 1000.0)
near_other = np.zeros(len(el))
for cid, g in el.groupby('CaBA_ID').groups.items():
    others = poly.geometry[poly.CaBA_ID != cid].union_all()
    near_other[g] = km_within(el.geometry.values[g], others, 100.0)
el['km_near_other_catchment'] = near_other
coast = ex[ex.reason_primary.isin(['GEO_OUTSIDE_E_W', 'FORM_TIDAL'])].geometry.union_all()
el['km_near_tidal'] = km_within(el.geometry.values, coast, 1000.0)
T = el.groupby('CaBA_ID')[['km_near_border', 'km_near_other_catchment', 'km_near_tidal', 'length_m']].sum()
T['eligible_km'] = T.pop('length_m') / 1000; T = T[T.index.isin(rep)]
T = T.join(cat.set_index('CaBA_ID').CaBA_Catch)
chosen = {}
def pick(slot, col):
    c = T[~T.index.isin(chosen.values())].sort_values([col], ascending=False, kind='mergesort')
    top = c[c[col] == c[col].max()].index.min(); chosen[slot] = int(top)
pick('P1_cross_border', 'km_near_border'); pick('P2_internal_boundary', 'km_near_other_catchment'); pick('P3_coastal_edge', 'km_near_tidal')
T.round(4).to_csv(OUT / 'preflight_selection_candidates.csv')
res = {'chosen': chosen, 'names': {k: str(T.CaBA_Catch[v]) for k, v in chosen.items()}, 'metrics': {k: {c: round(float(T.loc[v, c]), 3) for c in T.columns if c != 'CaBA_Catch'} for k, v in chosen.items()},
       'reproducibility_case': 19}
(OUT / 'preflight_selection.json').write_text(json.dumps(res, indent=1) + '\n'); print(json.dumps(res, indent=1))
