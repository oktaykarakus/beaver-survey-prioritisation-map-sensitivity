"""P2-C3 national overlay library. Reuses the verified P2-C2 pipeline (p2c_lc: frozen class table, 10 m rasterisation, LE-G25 grain
control with the pilot parameters 2500 px / disk radius 5 px / max 5 cycles) on a DOMAIN, which is either
  * a national tile: a 50 km core square on a grid aligned at (0,0) plus a margin >= 3 km beyond every assigned reach buffer, or
  * a catchment domain (P2-C2 pilot method): catchment bounding box + 3 km.
Raster grid is the global 10 m grid aligned at 0, so native rasters are identical in any domain.

Per assigned UNIT (reach buffer) it stores native-class pixel counts for the three arms C (CORINE 2018 recovered), LEn (Living England
IV native), LEg (LE-G25). Units: B40 (primary: eligible fragment, 40 m buffer), B20, B100 (buffer-width sensitivity), S1000, S500
(standardised segments: fragments longer than the length are cut into ceil(L/len) equal parts, 40 m buffer; shorter fragments reuse
B40). For B40 also pairwise agreement counts and woody-binary agreement on common known land.
Pooled (each pixel once): over pixels of the union of ALL eligible 40 m buffers that lie in the tile core, a histogram by pixel
catchment (CaBA polygon, 0 = outside all) of the category triple (C, LEn, LEg), native-class counts per arm, and geometric water
sub-types per arm (P2-C2 evaluation rule). Nothing here is a score, ranking or allocation.
"""
import os, sys, json, time, hashlib
from pathlib import Path
os.environ['OGR_GEOJSON_MAX_OBJ_SIZE'] = '0'
import numpy as np, pandas as pd, geopandas as gpd, shapely, shapely.ops, pyogrio
from rasterio.transform import Affine
from rasterio.features import rasterize
from pyproj import Transformer
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'p2c'))
import p2c_lc as L

R = HERE.parents[1]
RES = 10.0; MARGIN = 3000.0; CORE = 50000.0
LE_PATH = R / '05_Experiments/BHSI_v2_P2B/data_raw/living_england_p4/extracted/Living_England_Habitat_Map_Phase_4.gpkg'
CLC_PATH = R / '05_Experiments/BHSI_v2_P2A/derived/clc2018_eea_recovered_3035.gpkg'
C1 = R / '05_Experiments/BHSI_v2_P2C/c1'
EL_PATH = C1 / 'p2c1_eligible_network.gpkg'; EX_PATH = C1 / 'p2c1_excluded_network.gpkg'
# Optional read-only local copy of the large inputs (the project volume is a USB disk). A cached file is used only if its sha256,
# verified once when the cache was built (cache_manifest.json), equals the frozen hash and its size equals the original's.
FROZEN_SHA = {'LE': 'ae47a170e3f8f0ee890b67fbb2926ac03737f9f327ebc1580e33543267d51c7f', 'CLC': 'bb68d31d7f8e49e0edaf4a1895752805206e0cdd08c307953b46d4fec22f86f1',
              'EL': '7a8beaa04483d3ad647f09ddeaddc682dd79351c9d04862077273aa187eacc25', 'EX': 'd7cdca002be47afdc41031706742345be27f35305153d79d536fccdc226a5990'}
if os.environ.get('P2C3_INPUT_CACHE'):
    _cd = Path(os.environ['P2C3_INPUT_CACHE']); _man = json.loads((_cd / 'cache_manifest.json').read_text())
    _p = {}
    for _k, _orig in (('LE', LE_PATH), ('CLC', CLC_PATH), ('EL', EL_PATH), ('EX', EX_PATH)):
        _c = _cd / _orig.name
        assert _man[_orig.name] == FROZEN_SHA[_k] and _c.stat().st_size == _orig.stat().st_size, f'cache mismatch {_orig.name}'
        _p[_k] = _c
    LE_PATH, CLC_PATH, EL_PATH, EX_PATH = _p['LE'], _p['CLC'], _p['EL'], _p['EX']
CW = R / '06_Results_Figures/BHSI_v2_P2B/P2B_ECOLOGICAL_CROSSWALK.csv'
FROZEN = R / '05_Experiments/BHSI_v2_P2C/c2/class_treatment_table_FROZEN.csv'
NC = len(L.CATS); IDX = {c: i + 1 for i, c in enumerate(L.CATS)}; W, U = IDX['WATER'], IDX['UNK']
WOODY_IDX = [IDX[x] for x in L.WOODY]
WSUB = ['RIVER_CHANNEL', 'RIVER_CHANNEL_EXCLUDED', 'OTHER_INLAND_LAKE', 'OTHER_INLAND_CANAL', 'COASTAL_TIDAL', 'OTHER_INLAND_OFFNETWORK']
LINE_CODE = {'ELIGIBLE': 1, 'GEO_WALES': 2, 'CATCH_BELOW_MIN': 2, 'FORM_LAKE': 3, 'FORM_CANAL': 4, 'FORM_TIDAL': 5, 'GEO_OUTSIDE_E_W': 5}
UNIT_KINDS = ['B40', 'B20', 'B100', 'S1000', 'S500']
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
CODE_HASH = hashlib.sha256((HERE / 'p2c3_overlay.py').read_bytes() + (HERE.parent / 'p2c/p2c_lc.py').read_bytes()).hexdigest()

_G = {}
def load_common():
    """Load once per process: class tables, eligible + excluded network, catchment polygons."""
    if _G: return _G
    ct = L.class_table(CW)
    fr = pd.read_csv(FROZEN, dtype={'class_key': str})
    assert (fr.class_key.values == ct.class_key.values).all() and (fr.model_category.values == ct.model_category.values).all(), 'class table differs from frozen'
    kc, lc, tc = L.label_maps(ct, 'CORINE'); kl, ll, tl = L.label_maps(ct, 'LE')
    el = gpd.read_file(EL_PATH, columns=['fragment_id', 'parent_piece_id', 'CaBA_ID', 'length_m'])
    ex = gpd.read_file(EX_PATH, columns=['fragment_id', 'reason_primary'])
    poly = gpd.read_file(next((R / '01_BHSI_v1_Frozen/source_snapshot/data').rglob('Wild_Beaver_Catchments_England_*.geojson'))).to_crs(27700)
    poly['geometry'] = poly.geometry.buffer(0); poly = poly.sort_values('CaBA_ID').reset_index(drop=True)
    assert poly.CaBA_ID.max() < 255
    b = el.geometry.bounds
    el['cx'] = (b.minx + b.maxx) / 2; el['cy'] = (b.miny + b.maxy) / 2
    el['half_ext'] = np.maximum(b.maxx - b.minx, b.maxy - b.miny) / 2
    _G.update(dict(ct=ct, keys={'C': kc, 'LE': kl}, lut={'C': lc, 'LE': ll}, el=el, ex=ex, poly=poly,
                   el_tree=shapely.STRtree(el.geometry.values), ex_tree=shapely.STRtree(ex.geometry.values)))
    return _G


def tile_plan():
    """Deterministic national tiling: 50 km cores aligned at 0; a reach belongs to the tile containing its bbox centre; margin = 3 km +
    largest assigned half-extent + 100 m buffer, rounded up to 10 m."""
    G = load_common(); el = G['el']
    ix = np.floor(el['cx'] / CORE).astype(int); iy = np.floor(el['cy'] / CORE).astype(int)
    rows = []
    for (i, j), g in el.groupby([ix, iy]).groups.items():
        m = MARGIN + float(el.half_ext[g].max()) + 100.0 + RES
        m = float(np.ceil(m / RES) * RES)
        rows.append(dict(tile=f't{i:03d}_{j:03d}', ti=i, tj=j, core_x0=i * CORE, core_y0=j * CORE, core_x1=(i + 1) * CORE, core_y1=(j + 1) * CORE,
                         margin_m=m, n_reaches=len(g), eligible_km=float(el.length_m[g].sum() / 1000)))
    P = pd.DataFrame(rows)
    P['domain_mpx'] = ((CORE + 2 * P.margin_m) / RES) ** 2 / 1e6
    return P.sort_values('tile').reset_index(drop=True), ix, iy


def segments(geom, length, seg):
    if length <= seg: return None
    n = int(np.ceil(length / seg))
    return [shapely.ops.substring(geom, k / n, (k + 1) / n, normalized=True) for k in range(n)]


def run_domain(name, dom, core, reach_idx, out_path, seed_log=None):
    """dom, core: (x0, y0, x1, y1) in metres (dom aligned to the 10 m grid). reach_idx: integer index into the eligible table of
    reaches assigned to this domain. Writes an npz (atomic) and returns a summary dict."""

    t0 = time.time(); G = load_common(); el = G['el']; tm = {}
    x0, y0, x1, y1 = dom
    H, Wd = int(round((y1 - y0) / RES)), int(round((x1 - x0) / RES)); TR = Affine(RES, 0, x0, 0, -RES, y1)
    # ---- rasterise (as P2-C2 step 2) ----
    kl, kc = G['keys']['LE'], G['keys']['C']; ll, lc = G['lut']['LE'], G['lut']['C']
    le = pyogrio.read_dataframe(LE_PATH, bbox=(x0, y0, x1, y1), columns=['a_pred'])
    assert le.a_pred.notna().all(); bad = set(le.a_pred) - set(kl); assert not bad, bad
    lab_le = L.rasterise_polys(le.geometry.values[::-1], [kl.index(k) + 1 for k in le.a_pred.values[::-1]], TR, (H, Wd)) if len(le) else np.zeros((H, Wd), np.uint8)
    n_le = len(le); del le
    tr = Transformer.from_crs(27700, 3035, always_xy=True)
    clc = gpd.read_file(CLC_PATH, bbox=tr.transform_bounds(x0, y0, x1, y1, densify_pts=21)).to_crs(27700)
    clc['Code_18'] = clc.Code_18.astype(str); bad = set(clc.Code_18) - set(kc); assert not bad, bad
    n_inv = int((~clc.geometry.is_valid).sum())
    if n_inv: clc['geometry'] = shapely.make_valid(clc.geometry.values)
    lab_c = L.rasterise_polys(clc.geometry.values[::-1], [kc.index(k) + 1 for k in clc.Code_18.values[::-1]], TR, (H, Wd))
    n_clc = len(clc); del clc
    tm['rasterise'] = time.time() - t0
    # ---- grain control (pilot parameters) ----
    t1 = time.time()
    lab_leg, gc_log = L.grain_control(lab_le, 2500, 5, max_cycles=5)
    tm['grain_control'] = time.time() - t1
    nat = {'C': lab_c, 'LEn': lab_le, 'LEg': lab_leg}
    cat = {'C': lc[lab_c], 'LEn': ll[lab_le], 'LEg': ll[lab_leg]}
    nk = {'C': len(kc) + 1, 'LEn': len(kl) + 1, 'LEg': len(kl) + 1}
    # ---- units ----
    t1 = time.time()
    sub = el.iloc[reach_idx]
    geoms = sub.geometry.values; lens = sub.length_m.values; fids = sub.fragment_id.values
    units = {'B40': (fids, geoms, 40.0), 'B20': (fids, geoms, 20.0), 'B100': (fids, geoms, 100.0)}
    for kind, sl in (('S1000', 1000.0), ('S500', 500.0)):
        ids, gs, par = [], [], []
        for f, g, l in zip(fids, geoms, lens):
            s = segments(g, l, sl)
            if s is None: continue
            for k, gg in enumerate(s): ids.append(f'{f}#{k}'); gs.append(gg)
        units[kind] = (np.array(ids, dtype=object), np.array(gs, dtype=object), 40.0)
    out = {}
    for kind, (ids, gs, wbuf) in units.items():
        n = len(ids)
        cnt = {a: np.zeros((n, nk[a]), np.int32) for a in nat}
        npx = np.zeros(n, np.int32)
        if kind == 'B40':
            pair = np.zeros((n, 3, 2), np.int32); wpair = np.zeros((n, 2, 2), np.int32)
        for i, g in enumerate(gs):
            b = shapely.buffer(g, wbuf, quad_segs=16); mnx, mny, mxx, mxy = b.bounds
            c0 = int(np.floor((mnx - x0) / RES)); c1 = int(np.ceil((mxx - x0) / RES)); r0 = int(np.floor((y1 - mxy) / RES)); r1 = int(np.ceil((y1 - mny) / RES))
            assert c0 >= 0 and r0 >= 0 and c1 <= Wd and r1 <= H, f'unit {ids[i]} outside domain'
            wt = Affine(RES, 0, x0 + c0 * RES, 0, -RES, y1 - r0 * RES)
            m = rasterize([(b, 1)], out_shape=(r1 - r0, c1 - c0), transform=wt, fill=0, dtype='uint8').astype(bool)
            npx[i] = m.sum()
            for a in nat: cnt[a][i] = np.bincount(nat[a][r0:r1, c0:c1][m], minlength=nk[a])
            if kind == 'B40':
                cs = {a: cat[a][r0:r1, c0:c1][m] for a in nat}
                kn = {a: (cs[a] > 0) & (cs[a] != W) & (cs[a] != U) for a in nat}
                wd = {a: np.isin(cs[a], WOODY_IDX) for a in nat}
                for k, (p, q) in enumerate((('C', 'LEn'), ('C', 'LEg'), ('LEn', 'LEg'))):
                    both = kn[p] & kn[q]; pair[i, k] = (both.sum(), (both & (cs[p] == cs[q])).sum())
                for k, (p, q) in enumerate((('C', 'LEn'), ('C', 'LEg'))):
                    both = kn[p] & kn[q]; wpair[i, k] = (both.sum(), (both & (wd[p] == wd[q])).sum())
        out[f'{kind}_ids'] = ids.astype(str); out[f'{kind}_npx'] = npx
        for a in nat: out[f'{kind}_cnt_{a}'] = cnt[a]
        if kind == 'B40': out['B40_pair'] = pair; out['B40_woodypair'] = wpair
    tm['units'] = time.time() - t1
    # ---- pooled pixel statistics on union(all eligible 40 m buffers) within the core ----
    t1 = time.time()
    cx0, cy0, cx1, cy1 = core
    ii = G['el_tree'].query(shapely.buffer(shapely.box(*core), 50.0), predicate='intersects')
    union = rasterize(((shapely.buffer(g, 40.0, quad_segs=16), 1) for g in el.geometry.values[ii]), out_shape=(H, Wd), transform=TR, fill=0, dtype='uint8').astype(bool) if len(ii) else np.zeros((H, Wd), bool)
    rc0 = int(round((cx0 - x0) / RES)); rc1 = int(round((cx1 - x0) / RES)); rr0 = int(round((y1 - cy1) / RES)); rr1 = int(round((y1 - cy0) / RES))
    coremask = np.zeros((H, Wd), bool); coremask[max(rr0, 0):min(rr1, H), max(rc0, 0):min(rc1, Wd)] = True
    pool = union & coremask
    poly = G['poly']
    pi = poly.sindex.query(shapely.box(x0, y0, x1, y1), predicate='intersects')
    clab = rasterize(((poly.geometry.iloc[k], int(poly.CaBA_ID.iloc[k])) for k in pi), out_shape=(H, Wd), transform=TR, fill=0, dtype='uint8') if len(pi) else np.zeros((H, Wd), np.uint8)
    pc = clab[pool].astype(np.int64)
    out['pool_triple'] = np.bincount(pc * 4096 + cat['C'][pool].astype(np.int64) * 256 + cat['LEn'][pool].astype(np.int64) * 16 + cat['LEg'][pool].astype(np.int64), minlength=256 * 4096).reshape(256, 4096).astype(np.int64)
    for a in nat: out[f'pool_native_{a}'] = np.bincount(pc * nk[a] + nat[a][pool], minlength=256 * nk[a]).reshape(256, nk[a]).astype(np.int64)
    # water sub-types (P2-C2 evaluation rule): network lines of every form, eligible drawn last (wins)
    jj = G['ex_tree'].query(shapely.box(x0, y0, x1, y1), predicate='intersects'); kk = G['el_tree'].query(shapely.box(x0, y0, x1, y1), predicate='intersects')
    lines = [(g, LINE_CODE[r]) for g, r in zip(G['ex'].geometry.values[jj], G['ex'].reason_primary.values[jj])] + [(g, 1) for g in el.geometry.values[kk]]
    lr = rasterize(lines, out_shape=(H, Wd), transform=TR, fill=0, dtype='uint8', all_touched=True) if lines else np.zeros((H, Wd), np.uint8)
    lpix = np.argwhere(lr > 0); ltree = cKDTree(lpix) if len(lpix) else None
    for a in nat:
        wm = cat[a] == W
        ws = np.zeros((256, len(WSUB) + 1), np.int64)
        sel = wm & pool
        if sel.any():
            comp, _ = ndi.label(wm, structure=np.ones((3, 3), int))
            touch = np.zeros(comp.max() + 1, bool); touch[np.unique(comp[(lr > 0) & wm])] = True; touch[0] = False
            pix = np.argwhere(sel); cpx = comp[sel]
            code = np.full(len(pix), 6, np.int64)                                          # OFFNETWORK
            on = touch[cpx]
            if on.any() and ltree is not None:
                _, nn = ltree.query(pix[on]); code[on] = lr[lpix[nn, 0], lpix[nn, 1]].astype(np.int64)
            np.add.at(ws, (clab[sel].astype(np.int64), code), 1)
        out[f'pool_water_{a}'] = ws
    tm['pooled'] = time.time() - t1
    tm['total'] = time.time() - t0
    meta = dict(name=name, dom=list(dom), core=list(core), shape=[H, Wd], n_reaches=int(len(reach_idx)), le_segments=n_le, clc_polygons=n_clc, clc_invalid_fixed=n_inv,
                le_nodata_px=int((lab_le == 0).sum()), clc_nodata_px=int((lab_c == 0).sum()), grain_control_cycles=gc_log, pool_px=int(pool.sum()),
                timing_s=tm, code_hash=CODE_HASH, keys_C=list(kc), keys_LE=list(kl))
    out['meta_json'] = np.array(json.dumps(meta, default=float))
    tmp = Path(str(out_path) + '.tmp.npz')
    np.savez_compressed(tmp, **out); os.replace(tmp, out_path)
    return meta


def array_hash(npz_path):
    """sha256 over the arrays (names and bytes) of an output npz, excluding timing-bearing metadata."""
    Z = np.load(npz_path, allow_pickle=False); h = hashlib.sha256()
    for k in sorted(Z.files):
        if k == 'meta_json': continue
        h.update(k.encode()); h.update(np.ascontiguousarray(Z[k]).tobytes())
    return h.hexdigest()
