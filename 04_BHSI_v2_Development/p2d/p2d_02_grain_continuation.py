"""P2-D Task 4: bounded continuation of the frozen LE-G25 grain control for the 6 tiles that hit the 5-cycle cap in P2-C3.
The algorithm, parameters and stopping rule (<0.01% of domain pixels changed) are unchanged; only the cycle cap is raised from 5 to
12 for these tiles, so cycles 1-5 reproduce P2-C3 exactly and further cycles continue the same iteration. P2-C3 code is imported,
not edited: p2c3_overlay.run_domain calls p2c_lc.grain_control(..., max_cycles=5); a wrapper replaces that one argument.
Writes 05_Experiments/BHSI_v2_P2D/grain_continuation/<tile>.npz. Usage: python -I -B p2d_02_grain_continuation.py <workers>"""
import os, sys, json, time
from pathlib import Path
import numpy as np, pandas as pd
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / '04_BHSI_v2_Development/p2c3'))
TILES = ['t005_000', 't005_002', 't006_009', 't007_008', 't007_009', 't012_004']
OUT = R / '05_Experiments/BHSI_v2_P2D/grain_continuation'; CAP = 12


def job(t):
    import p2c3_overlay as O
    orig = O.L.grain_control
    O.L.grain_control = lambda lab, min_px=2500, radius_px=5.0, max_cycles=5: orig(lab, min_px, radius_px, max_cycles=CAP)
    P = pd.read_csv(R / '05_Experiments/BHSI_v2_P2C3/overlay/tile_plan.csv').set_index('tile'); A = pd.read_csv(R / '05_Experiments/BHSI_v2_P2C3/overlay/reach_tile_assignment.csv', usecols=['tile'])
    r = P.loc[t]; m = r.margin_m; idx = np.flatnonzero(A.tile.values == t)
    meta = O.run_domain(t, (r.core_x0 - m, r.core_y0 - m, r.core_x1 + m, r.core_y1 + m), (r.core_x0, r.core_y0, r.core_x1, r.core_y1), idx, OUT / f'{t}.npz')
    return t, [c['frac_changed_vs_previous'] for c in meta['grain_control_cycles']], meta['timing_s']['total']


if __name__ == '__main__':
    import multiprocessing as mp
    with mp.get_context('spawn').Pool(int(sys.argv[1])) as pool:
        for t, cyc, sec in pool.imap_unordered(job, TILES):
            print(time.strftime('%H:%M:%S'), t, 'cycles', len(cyc), [round(100 * c, 4) for c in cyc], f'{sec:.0f}s', flush=True)
