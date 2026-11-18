"""P2-C3 overlay driver (checkpointed, restartable).
  plan <out_dir>                                   write tile_plan.csv and reach->tile assignment
  tiles <out_dir> <workers> [tile ...]             run tiles (all if none given); an existing npz with the same code hash is skipped
  catchment <out_dir> <CaBA_ID>                    untiled run of one catchment (P2-C2 pilot domain: bbox + 3 km)
  rerun <out_dir> <tile> <dest_npz>                run one tile again to a separate file (determinism check)"""
import os, sys, json, time, traceback
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p2c3_overlay as O


def log(out, *a):
    s = time.strftime('%Y-%m-%d %H:%M:%S ') + ' '.join(str(x) for x in a)
    print(s, flush=True)
    with open(Path(out) / 'overlay_run.log', 'a') as f: f.write(s + '\n')


def plan(out):
    P, ix, iy = O.tile_plan(); el = O.load_common()['el']
    P.to_csv(Path(out) / 'tile_plan.csv', index=False)
    A = pd.DataFrame({'fragment_id': el.fragment_id, 'tile': [f't{i:03d}_{j:03d}' for i, j in zip(ix, iy)], 'CaBA_ID': el.CaBA_ID, 'length_m': el.length_m})
    A.to_csv(Path(out) / 'reach_tile_assignment.csv', index=False)
    return P, A


def _tile_job(args):
    out, row = args
    try:
        G = O.load_common(); el = G['el']
        A = pd.read_csv(Path(out) / 'reach_tile_assignment.csv', usecols=['tile'])
        idx = np.flatnonzero(A.tile.values == row['tile'])
        m = row['margin_m']
        dom = (row['core_x0'] - m, row['core_y0'] - m, row['core_x1'] + m, row['core_y1'] + m)
        core = (row['core_x0'], row['core_y0'], row['core_x1'], row['core_y1'])
        meta = O.run_domain(row['tile'], dom, core, idx, Path(out) / 'tiles' / f"{row['tile']}.npz")
        return row['tile'], 'ok', meta['timing_s']['total'], meta['n_reaches']
    except Exception:
        return row['tile'], 'FAIL ' + traceback.format_exc(), 0, 0


def done_ok(p):
    if not p.exists(): return False
    try: return json.loads(str(np.load(p)['meta_json']))['code_hash'] == O.CODE_HASH
    except Exception: return False


def tiles(out, workers, names):
    P = pd.read_csv(Path(out) / 'tile_plan.csv')
    if names: P = P[P.tile.isin(names)]
    todo = [r for _, r in P.sort_values('domain_mpx', ascending=False).iterrows() if not done_ok(Path(out) / 'tiles' / f"{r['tile']}.npz")]
    log(out, f'tiles requested {len(P)}, to run {len(todo)}, workers {workers}, code {O.CODE_HASH[:12]}')
    if not todo: return
    import multiprocessing as mp
    with mp.get_context('spawn').Pool(workers) as pool:
        for name, st, sec, n in pool.imap_unordered(_tile_job, [(str(out), r.to_dict()) for r in todo]):
            log(out, name, st if st == 'ok' else st[:2000], f'{sec:.0f}s', n)


def catchment(out, cid):
    G = O.load_common(); el = G['el']; poly = G['poly']
    idx = np.flatnonzero(el.CaBA_ID.values == cid)
    bx = poly.geometry[poly.CaBA_ID == cid].union_all().bounds
    R = O.RES; M = O.MARGIN
    dom = (np.floor((bx[0] - M) / R) * R, np.floor((bx[1] - M) / R) * R, np.ceil((bx[2] + M) / R) * R, np.ceil((bx[3] + M) / R) * R)
    meta = O.run_domain(f'catchment_{cid}', dom, bx, idx, Path(out) / f'catchment_{cid}.npz')
    log(out, f'catchment {cid} done', meta['timing_s'], meta['shape'])


if __name__ == '__main__':
    cmd, out = sys.argv[1], Path(sys.argv[2]); (out / 'tiles').mkdir(parents=True, exist_ok=True)
    if cmd == 'plan': P, A = plan(out); print(P.describe().T[['count', 'mean', 'min', 'max']]); print('tiles', len(P), 'total Mpx', P.domain_mpx.sum())
    elif cmd == 'tiles': tiles(out, int(sys.argv[3]), sys.argv[4:])
    elif cmd == 'catchment': catchment(out, int(sys.argv[3]))
    elif cmd == 'rerun':
        P = pd.read_csv(out / 'tile_plan.csv'); row = P[P.tile == sys.argv[3]].iloc[0].to_dict()
        G = O.load_common(); A = pd.read_csv(out / 'reach_tile_assignment.csv', usecols=['tile']); idx = np.flatnonzero(A.tile.values == row['tile']); m = row['margin_m']
        O.run_domain(row['tile'], (row['core_x0'] - m, row['core_y0'] - m, row['core_x1'] + m, row['core_y1'] + m), (row['core_x0'], row['core_y0'], row['core_x1'], row['core_y1']), idx, Path(sys.argv[4]))
