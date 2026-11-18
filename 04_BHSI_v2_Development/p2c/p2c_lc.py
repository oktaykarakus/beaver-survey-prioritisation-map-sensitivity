"""P2-C2 library: frozen crosswalk tables, 10 m rasterisation, 25 ha grain control, riparian composition on a common raster support.

All class->category->interval decisions are read from the frozen P2B_ECOLOGICAL_CROSSWALK.csv; nothing is re-mapped here.
Interval endpoints (frozen P2B protocol 3.3; K1 levels only, no new numbers):
    GRS    grassland / pasture                 [0.1, 0.5]   (CORINE 231, 321; LE Acid/Calcareous/Neutral and Improved grassland)
    AGM    heterogeneous agriculture           [0.1, 0.5]   (CORINE 241-244)
    URBVEG green urban / sport and leisure     [0.0, 0.5]   (CORINE 141, 142)
    RGH    bracken only (LE Bracken)           [0.1, 0.5]   (heath, CORINE 322/323 stay at the point value 0.5)
Point categories: BLW 1.0, CON 0.5, SCR 0.5, RGH(heath) 0.5, WET 0.5, ARB 0.1, URB/MIN/COA/BARE 0.0.
Water (CORINE 511/512/521/522/523, LE Water) is removed from numerator and denominator (rule R-W). LE Unclassified is UNKNOWN
(bounds [0,1], carried inside the denominator, never imputed).
"""
import re
import numpy as np, pandas as pd
from scipy import ndimage as ndi

POINT = {'BLW': 1.0, 'CON': 0.5, 'SCR': 0.5, 'RGH': 0.5, 'WET': 0.5, 'ARB': 0.1, 'URB': 0.0, 'MIN': 0.0, 'COA': 0.0, 'BARE': 0.0}
INTERVAL_CAT = {'GRS': (0.1, 0.5), 'AGM': (0.1, 0.5), 'URBVEG': (0.0, 0.5)}
BRACKEN = (0.1, 0.5)
WATER_SUB = {'511': 'WATER_CHANNEL', '512': 'WATER_OTHER_INLAND', '521': 'WATER_COASTAL_TIDAL', '522': 'WATER_COASTAL_TIDAL', '523': 'WATER_COASTAL_TIDAL'}
WOODY = ('BLW', 'CON', 'SCR')            # K3 woody share, protocol 3.2 (broadleaf+mixed [merged in BLW] + coniferous + scrub)
CATS = ['BLW', 'CON', 'SCR', 'GRS', 'RGH', 'WET', 'AGM', 'ARB', 'URB', 'URBVEG', 'MIN', 'COA', 'BARE', 'UNK', 'WATER']  # model categories; index = position


def class_table(crosswalk_csv):
    """One row per (source, class_key) with category, interval endpoints and water sub-type. Raises if anything is unmapped."""
    cw = pd.read_csv(crosswalk_csv, dtype=str)
    rows = []
    for _, x in cw.iterrows():
        src = 'CORINE' if x.source == 'CORINE2018' else 'LE'
        key = x.class_id if src == 'CORINE' else x.class_name
        cat = x.ecological_category
        water = cat == 'WATER_EXCLUDED'
        unk = cat == 'UNK'
        if water:
            mcat, lo, hi = 'WATER', np.nan, np.nan
        elif unk:
            mcat, lo, hi = 'UNK', 0.0, 1.0
        else:
            mcat = cat
            if cat in INTERVAL_CAT: lo, hi = INTERVAL_CAT[cat]
            elif cat == 'RGH' and key == 'Bracken': lo, hi = BRACKEN
            elif cat in POINT: lo = hi = POINT[cat]
            else: raise ValueError(f'unmapped category {cat} for {src} {key}')
        rows.append(dict(source=src, class_key=key, class_name=x.class_name, category=cat, model_category=mcat, lo=lo, hi=hi,
                         is_interval=bool(not water and not unk and hi > lo), water_sub=WATER_SUB.get(key, 'WATER_UNDIFFERENTIATED') if water else ''))
    return pd.DataFrame(rows)


def label_maps(ct, source):
    """Return (labels list, lut_class->model-category index, class_key list). Label 0 is reserved for no data / no coverage."""
    t = ct[ct.source == source].reset_index(drop=True)
    keys = list(t.class_key)
    lut = np.zeros(len(keys) + 1, np.uint8)
    for i, c in enumerate(t.model_category): lut[i + 1] = CATS.index(c) + 1      # category label 0 = no data
    return keys, lut, t


def rasterise_polys(geoms, values, transform, shape, nodata=0):
    from rasterio.features import rasterize
    return rasterize(((g, int(v)) for g, v in zip(geoms, values)), out_shape=shape, transform=transform, fill=nodata, all_touched=False, dtype='uint8')


# ---- grain control -------------------------------------------------------------------------------------------------
def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return (x * x + y * y) <= r * r


def open_disk(m, r):
    """Binary opening by a Euclidean disk of radius r pixels, via distance transforms (exact, linear time):
    erosion keeps pixels whose nearest background pixel is farther than r; dilation re-grows by r. The image border is background."""
    mp = np.pad(m, 1, constant_values=False)
    er = ndi.distance_transform_edt(mp) > r
    if not er.any(): return np.zeros_like(m, dtype=bool)
    return (ndi.distance_transform_edt(~er) <= r)[1:-1, 1:-1] & m


def width_open_fill(lab, radius_px):
    """Impose a minimum width: per class morphological opening with a disk of `radius_px`; pixels that lose their class are
    given the label of the nearest retained pixel (Euclidean). No-data (0) stays 0. Deterministic."""
    if radius_px <= 0: return lab.copy()
    keep = np.zeros_like(lab)
    for c in np.unique(lab):
        if c == 0: continue
        m = lab == c
        # open on a padded window of the class bounding box (large speed-up), then write back
        sl = ndi.find_objects(m.astype(np.uint8))[0]
        pad = int(np.ceil(radius_px)) + 2
        sl = tuple(slice(max(0, s.start - pad), min(n, s.stop + pad)) for s, n in zip(sl, lab.shape))
        op = open_disk(m[sl], radius_px)
        keep[sl][op] = c
    holes = (lab > 0) & (keep == 0)
    if not holes.any(): return keep
    idx = ndi.distance_transform_edt(keep == 0, return_distances=False, return_indices=True)
    out = keep.copy()
    out[holes] = keep[idx[0][holes], idx[1][holes]]
    return out


def sieve_min_area(lab, min_px, connectivity=8):
    """GDAL sieve: connected same-label regions smaller than `min_px` are merged into their largest neighbour. No-data is masked."""
    from rasterio.features import sieve
    mask = (lab > 0).astype(np.uint8)
    return sieve(lab, size=int(min_px), mask=mask, connectivity=connectivity)


def grain_control(lab, min_px=2500, radius_px=5.0, max_cycles=6):
    """25 ha / 100 m generalisation (a symmetric disk on a 10 m grid retains objects >= 2*floor(r)+1 pixels wide: r=5 -> 110 m [primary, protocol value]; r=4.5 -> 90 m [bracketing sensitivity]; exactly 100 m cannot be represented): repeat (width opening + fill, then sieve) until neither step changes more than 0.01 % of
    the pixels, or `max_cycles`. Returns (labels, per-cycle log)."""
    cur = lab.copy(); log = []
    n = max(1, int((lab > 0).sum()))
    for k in range(1, max_cycles + 1):
        a = width_open_fill(cur, radius_px)
        b = sieve_min_area(a, min_px) if min_px > 0 else a
        ch_w = float((a != cur).sum()) / n; ch_s = float((b != a).sum()) / n; ch = float((b != cur).sum()) / n
        log.append({'cycle': k, 'frac_changed_by_width_step': ch_w, 'frac_changed_by_sieve_step': ch_s, 'frac_changed_vs_previous': ch})
        cur = b
        if ch < 1e-4: break
    return cur, log


def patch_stats(lab, px_area_m2=100.0, mask=None):
    """Connected-component (8-neighbour) patch statistics of a label raster, region restricted by `mask`."""
    n_tot = 0; areas = []
    st = np.ones((3, 3), int)
    for c in np.unique(lab):
        if c == 0: continue
        m = lab == c
        if mask is not None: m = m & mask
        cc, n = ndi.label(m, structure=st)
        if n: areas.append(np.bincount(cc.ravel())[1:] * px_area_m2)
    a = np.concatenate(areas) if areas else np.array([])
    return a


def narrow_fraction(lab, radius_px):
    """Share of mapped pixels that would be removed by a width opening (a 'width violation' measure)."""
    if radius_px <= 0: return 0.0
    k = width_open_fill(lab, radius_px)
    return float(((lab > 0) & (k != lab)).sum() / max(1, (lab > 0).sum()))


# ---- composition ----------------------------------------------------------------------------------------------------
