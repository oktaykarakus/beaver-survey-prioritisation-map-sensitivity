"""P2-C3 reach composition and K1 scores from native-class pixel counts. Formulae are those of P2-C2 step 2 (p2c2_02_overlay.py):
  land = buffer px - water px;   unknown = LE Unclassified + no-coverage (label 0), kept in the land denominator;
  s_lo = sum(c_k * lo_k) / land  (unknown contributes 0);   s_hi = (sum(c_k * hi_k) + no-coverage px) / land  (unknown contributes 1).
Sensitivity 'conditional': unknown removed from the denominator, s = sum(c_k * end_k) / (land - unknown).
Zero land (water fraction 1): score undefined (NaN), reported. Woody share = (BLW + CON + SCR) / land (endpoint-free).
"""
import numpy as np, pandas as pd, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'p2c'))
import p2c_lc as L

IDX = {c: i + 1 for i, c in enumerate(L.CATS)}


def arm_vectors(ct, source):
    t = ct[ct.source == source].reset_index(drop=True)
    lo = np.r_[0.0, np.nan_to_num(t.lo.values.astype(float))]; hi = np.r_[1.0, np.nan_to_num(t.hi.values.astype(float))]
    wa = np.r_[False, (t.model_category == 'WATER').values]; un = np.r_[True, (t.model_category == 'UNK').values]
    catidx = np.r_[0, [IDX[c] for c in t.model_category]]
    return lo, hi, wa, un, catidx


def compose(cnt, ct, source, unknown='bounds'):
    """cnt: (n, K) native counts incl. label 0 in column 0. Returns DataFrame of composition and scores."""
    lo, hi, wa, un, catidx = arm_vectors(ct, source)
    cnt = cnt.astype(np.float64); n = cnt.shape[0]
    buf = cnt.sum(1); water = cnt[:, wa].sum(1); land = buf - water; unk = cnt[:, un].sum(1); nocov = cnt[:, 0]
    cat = np.zeros((n, len(L.CATS) + 1))
    for k in range(cnt.shape[1]): cat[:, catidx[k]] += cnt[:, k]
    num_lo = (cnt * np.where(wa, 0, lo)).sum(1); num_hi = (cnt * np.where(wa, 0, hi)).sum(1)
    with np.errstate(invalid='ignore', divide='ignore'):
        if unknown == 'bounds':
            s_lo = np.where(land > 0, num_lo / land, np.nan); s_hi = np.where(land > 0, num_hi / land, np.nan)
        else:
            known = land - unk
            nl = (cnt * np.where(wa | un, 0, lo)).sum(1); nh = (cnt * np.where(wa | un, 0, hi)).sum(1)
            s_lo = np.where(known > 0, nl / known, np.nan); s_hi = np.where(known > 0, nh / known, np.nan)
        woody = np.where(land > 0, cat[:, [IDX[x] for x in L.WOODY]].sum(1) / land, np.nan)
        out = pd.DataFrame({'buffer_px': buf, 'water_px': water, 'land_px': land, 'unknown_px': unk, 'nocov_px': nocov,
                            'water_frac': np.where(buf > 0, water / buf, np.nan), 'unknown_frac_of_land': np.where(land > 0, unk / land, np.nan),
                            's_lo': s_lo, 's_hi': s_hi, 'woody': woody})
    for c in L.CATS: out[f'cat_{c}'] = cat[:, IDX[c]]
    return out
