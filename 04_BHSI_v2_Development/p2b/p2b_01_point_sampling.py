"""P2-B evidence script: point-sample CORINE 2018 (recovered) and Living England Phase IV.

Purpose (data-feasibility only; NO suitability scoring, NO ranking):
  (a) completeness of Living England over the 107 catchments,
  (b) which LE / CORINE classes sit under river-piece midpoints (water representation),
  (c) a descriptive CORINE x LE class cross-tabulation to document crosswalk ambiguity.
The cross-tabulation documents ambiguity. It is NOT used to set or tune any score.
Inputs are opened read-only. Outputs go to 05_Experiments/BHSI_v2_P2B/coverage_sampling/.
Run:  <frozen venv>/bin/python -I p2b_01_point_sampling.py
"""
from pathlib import Path
import json, time, hashlib
import numpy as np, pandas as pd, geopandas as gpd, shapely, pyogrio
from shapely.geometry import Point

R = Path(__file__).resolve().parents[2]
OUT = R / '05_Experiments/BHSI_v2_P2B/coverage_sampling'
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20261107
PTS_PER_KM2 = 2.0
LE = R / '05_Experiments/BHSI_v2_P2B/data_raw/living_england_p4/extracted/Living_England_Habitat_Map_Phase_4.gpkg'
CLC = R / '05_Experiments/BHSI_v2_P2A/derived/clc2018_eea_recovered_3035.gpkg'
RIV = R / '05_Experiments/BHSI_v2_Phase1/native_001/canonical_native_rivers.gpkg'
CATCH = list((R / '01_BHSI_v1_Frozen/source_snapshot/data').rglob('Wild_Beaver_Catchments_England_*.geojson'))
assert len(CATCH) == 1
t0 = time.time()
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)

catch = gpd.read_file(CATCH[0]).to_crs(27700)
catch['geometry'] = catch.geometry.buffer(0)
ids = pd.read_csv(R / '05_Experiments/P1_5_Portability/script/catchments_107.csv').CaBA_ID.values
catch = catch.set_index('CaBA_ID').loc[ids].reset_index()
assert len(catch) == 107 and catch.geometry.is_valid.all()

# ---- random area-proportional points inside each catchment (seeded)
rng = np.random.default_rng(SEED)
rows = []
for cid, g in zip(catch.CaBA_ID, catch.geometry):
    n = int(np.ceil(g.area / 1e6 * PTS_PER_KM2))
    minx, miny, maxx, maxy = g.bounds
    got = []
    while len(got) < n:
        m = max(2000, 3 * (n - len(got)))
        x = rng.uniform(minx, maxx, m); y = rng.uniform(miny, maxy, m)
        ok = shapely.contains_xy(g, x, y)
        got.extend(zip(x[ok], y[ok]))
    for x, y in got[:n]: rows.append((cid, 'random', x, y))
rnd = pd.DataFrame(rows, columns=['CaBA_ID', 'kind', 'x', 'y'])
log('random points', len(rnd))

# ---- river-piece midpoints (read-only from Phase 1 output)
riv = gpd.read_file(RIV, columns=['piece_id', 'CaBA_ID', 'length_m'])
mid = shapely.line_interpolate_point(riv.geometry.values, 0.5, normalized=True)
mp = pd.DataFrame({'CaBA_ID': riv.CaBA_ID.values, 'kind': 'midpoint', 'x': shapely.get_x(mid), 'y': shapely.get_y(mid),
                   'piece_id': riv.piece_id.values, 'length_m': riv.length_m.values})
pts = pd.concat([rnd, mp], ignore_index=True)
pts['pid'] = np.arange(len(pts))
log('total points', len(pts))
gp = gpd.GeoDataFrame(pts, geometry=gpd.points_from_xy(pts.x, pts.y), crs=27700)


def first_hit(pt_xy, poly_geoms, values):
    """Value of the first polygon (lowest index) that intersects each point; NaN if none. STRtree on points, prepared polygons."""
    pts_g = shapely.points(pt_xy[:, 0], pt_xy[:, 1])
    tree = shapely.STRtree(pts_g)
    pi, gi = tree.query(poly_geoms, predicate='intersects')   # pi: polygon idx, gi: point idx
    out = np.full(len(pt_xy), -1, dtype=np.int64)
    order = np.argsort(-pi, kind='stable')                     # write highest polygon index first so lowest wins
    out[gi[order]] = pi[order]
    res = np.full(len(pt_xy), None, dtype=object)
    hit = out >= 0
    res[hit] = np.asarray(values, dtype=object)[out[hit]]
    return res

# ---- CORINE (recovered) sample
clc = gpd.read_file(CLC, columns=['Code_18']).to_crs(27700)
pts['clc']=first_hit(pts[['x','y']].values, clc.geometry.values, clc.Code_18.values)
log('CORINE sampled; unmatched', int(pts.clc.isna().sum()))

# ---- Living England sample in 50 km tiles (bbox read uses the GPKG R-tree)
T = 50_000
pts['tx'] = (pts.x // T).astype(int); pts['ty'] = (pts.y // T).astype(int)
pts['le'] = None; pts['le_src'] = np.nan; pts['le_prob'] = np.nan
for (tx, ty), sub in pts.groupby(['tx', 'ty']):
    bb = (tx * T - 10, ty * T - 10, (tx + 1) * T + 10, (ty + 1) * T + 10)
    seg = gpd.read_file(LE, bbox=bb, columns=['a_pred', 'a_prob', 'srccode'], engine='pyogrio')
    xy = sub[['x', 'y']].values
    for col, src in (('le', 'a_pred'), ('le_src', 'srccode'), ('le_prob', 'a_prob')):
        pts.loc[sub.index, col] = first_hit(xy, seg.geometry.values, seg[src].values)
    log('tile', tx, ty, 'pts', len(sub), 'segments', len(seg))

keep = ['pid', 'CaBA_ID', 'kind', 'x', 'y', 'piece_id', 'length_m', 'clc', 'le', 'le_src', 'le_prob']
pts[keep].to_csv(OUT / 'point_samples.csv.gz', index=False)
(OUT / 'sampling_run.json').write_text(json.dumps({
    'seed': SEED, 'points_per_km2': PTS_PER_KM2, 'n_random': int((pts.kind == 'random').sum()),
    'n_midpoints': int((pts.kind == 'midpoint').sum()), 'seconds': time.time() - t0,
    'le_unmatched_random': int(((pts.kind == 'random') & pts['le'].isna()).sum()),
    'le_unmatched_midpoint': int(((pts.kind == 'midpoint') & pts['le'].isna()).sum()),
    'clc_unmatched_random': int(((pts.kind == 'random') & pts.clc.isna()).sum()),
    'clc_unmatched_midpoint': int(((pts.kind == 'midpoint') & pts.clc.isna()).sum()),
    'sampling_only_no_suitability': True}, indent=2) + '\n')
log('DONE', time.time() - t0)
