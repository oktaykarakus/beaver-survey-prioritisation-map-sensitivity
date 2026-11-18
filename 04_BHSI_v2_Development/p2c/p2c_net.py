"""P2-C1 library: geometric country split, reason codes and catchment eligibility for river pieces.

Frozen rules (P2B_WATER_ESTUARY_RULES.md section 2):
  E1 OS Open Rivers `form` == 'inlandRiver'      (canal, lake, tidalRiver are reported, never silently dropped)
  E2 geometry lies in England (ONS Countries Dec 2023 BFC, clipped to MHW); Welsh and seaward/other parts are cut off
  E3 catchment holds >= MIN_CATCH_KM of fragments that satisfy E1 and E2 (threshold applied AFTER E1, E2)
Eligibility never depends on a land-cover value or a score.

Reason codes, precedence (primary reason = first applicable):
  1 GEO_WALES           fragment lies in Wales
  2 GEO_OUTSIDE_E_W     fragment lies in neither England nor Wales (seaward of mean high water, or other)
  3 FORM_TIDAL          OS form == tidalRiver
  4 FORM_CANAL          OS form == canal
  5 FORM_LAKE           OS form == lake  (link drawn through still water)
  6 CATCH_BELOW_MIN     catchment has < MIN_CATCH_KM of fragments passing E1 and E2
All applicable codes are recorded in `reasons_all` (';'-joined); `reason_primary` is the lowest-numbered one.
"""
import numpy as np
import shapely

MIN_CATCH_KM = 10.0
PRECEDENCE = ['GEO_WALES', 'GEO_OUTSIDE_E_W', 'FORM_TIDAL', 'FORM_CANAL', 'FORM_LAKE', 'CATCH_BELOW_MIN']
FORM_CODE = {'tidalRiver': 'FORM_TIDAL', 'canal': 'FORM_CANAL', 'lake': 'FORM_LAKE'}
KNOWN_FORMS = {'inlandRiver', 'tidalRiver', 'canal', 'lake'}
PAD = 50.0  # metres: window margin so that a clipped polygon window equals the full polygon around a line


def _line_parts(g):
    """Linear components of a geometry (drops points / polygons produced by touches)."""
    if g is None or g.is_empty:
        return []
    t = g.geom_type
    if t == 'LineString':
        return [g]
    if t == 'MultiLineString':
        return list(g.geoms)
    if t == 'GeometryCollection':
        out = []
        for p in g.geoms:
            out.extend(_line_parts(p))
        return out
    return []


def split_line_by_regions(line, regions, min_len=1e-9):
    """Sequentially split `line` by an ordered list of (name, polygon). Precedence = list order, so a line lying exactly
    on a shared border is assigned once, to the earlier region. The remainder goes to 'OTHER'.
    The polygons are first clipped to a window around the line (equal to the polygon inside the window), which is exact
    for a line inside the window and avoids operating on million-vertex polygons. Returns [(region, LineString), ...]."""
    b = line.bounds
    out = []
    rem = [line]
    for name, poly in regions:
        win = shapely.clip_by_rect(poly, b[0] - PAD, b[1] - PAD, b[2] + PAD, b[3] + PAD)
        nxt = []
        for r in rem:
            if win.is_empty:
                nxt.append(r)
                continue
            for p in _line_parts(shapely.intersection(r, win)):
                if p.length > min_len:
                    out.append((name, p))
            for p in _line_parts(shapely.difference(r, win)):
                if p.length > min_len:
                    nxt.append(p)
        rem = nxt
    for p in rem:
        out.append(('OTHER', p))
    return out


def classify_and_split(geoms, england, wales):
    """For every input line return a list of (region, LineString) with region in {'ENGLAND','WALES','OTHER'}.
    Fast paths use prepared-geometry predicates; only lines that cross a boundary are cut."""
    shapely.prepare(england)
    shapely.prepare(wales)
    in_e = shapely.contains(england, geoms)
    hit_e = shapely.intersects(england, geoms)
    hit_w = shapely.intersects(wales, geoms)
    in_w = shapely.contains(wales, geoms)
    res = [None] * len(geoms)
    n_cut = 0
    for i, g in enumerate(geoms):
        if in_e[i]:
            res[i] = [('ENGLAND', g)]
        elif not hit_e[i] and in_w[i]:
            res[i] = [('WALES', g)]
        elif not hit_e[i] and not hit_w[i]:
            res[i] = [('OTHER', g)]
        else:
            res[i] = split_line_by_regions(g, [('ENGLAND', england), ('WALES', wales)])
            n_cut += 1
    return res, n_cut


def reasons_for(geo, form, catchment_ok):
    """All applicable reason codes (precedence order) for one fragment."""
    r = []
    if geo == 'WALES':
        r.append('GEO_WALES')
    elif geo == 'OTHER':
        r.append('GEO_OUTSIDE_E_W')
    if form in FORM_CODE:
        r.append(FORM_CODE[form])
    elif form not in KNOWN_FORMS:
        raise ValueError(f'unexpected OS form {form!r}')
    if not catchment_ok:
        r.append('CATCH_BELOW_MIN')
    return r
