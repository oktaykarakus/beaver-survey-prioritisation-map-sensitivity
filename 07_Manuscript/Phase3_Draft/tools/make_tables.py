"""Manuscript V01 tables (LaTeX), generated only from frozen/verified files. Writes ../tables/*.tex.
Table 1: ecological categories, member classes and K1 scores (frozen class table).  Table 2: decision metrics by budget.
Table 3: robustness at the 5% budget.  Usage: python3 make_tables.py"""
import json, csv
from pathlib import Path
R = Path(__file__).resolve().parents[3]; A = R / '05_Experiments/BHSI_v2_P2C3/analysis'; D = R / '06_Results_Figures/BHSI_v2_P2C3'
OUT = Path(__file__).resolve().parents[1] / 'tables'; OUT.mkdir(exist_ok=True)
AL = json.load(open(A / 'alloc/alloc_summary.json'))
RG = list(csv.DictReader(open(D / 'P2C3_CROSS_SCENARIO_REGRET.csv')))
def rg(b, st, o, t, col='norm_regret'):
    return [float(r[col]) for r in RG if float(r['budget_pct']) == b and r['strategy'] == st and r['origin'] == o and r['target'] == t][0]
f2 = lambda x: f'{x:.2f}'; f3 = lambda x: f'{x:.3f}'

# ---- Table 1 ----
ct = list(csv.DictReader(open(R / '05_Experiments/BHSI_v2_P2C/c2/class_treatment_table_FROZEN.csv')))
NAME = {'BLW': 'Broadleaf and mixed woodland', 'CON': 'Coniferous woodland', 'SCR': 'Scrub', 'RGH': 'Heath, moor and bracken', 'WET': 'Wetland and bog',
        'GRS': 'Grassland and pasture', 'AGM': 'Heterogeneous agriculture', 'ARB': 'Arable and permanent crops', 'URBVEG': 'Green urban and sport', 'URB': 'Built-up',
        'MIN': 'Mineral extraction and dumps', 'COA': 'Coastal', 'BARE': 'Bare ground and sand', 'UNK': 'Unclassified', 'WATER': 'Water'}
order = ['BLW', 'CON', 'SCR', 'RGH', 'WET', 'GRS', 'AGM', 'ARB', 'URBVEG', 'URB', 'MIN', 'COA', 'BARE', 'UNK', 'WATER']
rows = []
for c in order:
    m = [r for r in ct if r['model_category'] == c]
    cor = ', '.join(r['class_key'] for r in m if r['source'] == 'CORINE') or '--'
    le = '; '.join(r['class_key'] for r in m if r['source'] == 'LE') or '--'
    if c == 'WATER': sc = 'excluded'
    elif c == 'UNK': sc = '0 (lo) / 1 (hi)'
    else:
        vals = sorted({(r['lo'], r['hi']) for r in m})
        sc = ' or '.join(f'{float(lo):.1f}' if lo == hi else f'[{float(lo):.1f}, {float(hi):.1f}]' for lo, hi in vals)
    rows.append(f'{NAME[c]} & {cor} & {le.replace("&", "and")} & {sc} \\\\')
(OUT / 'table1_crosswalk.tex').write_text('\n'.join(rows) + '\n')

# ---- Table 2 (metrics as rows, budgets as columns) ----
cols = {}
for b in (1, 5, 10):
    B = AL[f'budget_{b}']; c = B['contrasts']['A1']
    rep = [rg(b, 'A1', o, t) for o, t in [('C_lo', 'LEg_lo'), ('C_lo', 'LEg_hi'), ('C_hi', 'LEg_lo'), ('C_hi', 'LEg_hi'), ('LEg_lo', 'C_lo'), ('LEg_lo', 'C_hi'), ('LEg_hi', 'C_lo'), ('LEg_hi', 'C_hi')]]
    amb = [rg(b, 'A1', o, t) for o, t in [('C_lo', 'C_hi'), ('C_hi', 'C_lo'), ('LEg_lo', 'LEg_hi'), ('LEg_hi', 'LEg_lo')]]
    a2 = [rg(b, 'A2', j, j, 'capture') for j in ('C_lo', 'LEg_lo')]; a3 = [rg(b, 'A3', j, j, 'capture') for j in ('C_lo', 'LEg_lo')]
    cols[b] = [f2(c['D_R']), f3(c['D_A']), f2(c['D_G']), f2(c['D_RN']), f2(c['grain_persistence_share']),
               f"{f2(sum(rep)/len(rep))} ({f2(min(rep))}--{f2(max(rep))})", f3(sum(amb)/len(amb)), f"{f2(B['core_share_of_budget'])} ({B['core_n_catchments_holding_50pct']})",
               f"{f2(a2[0])} / {f2(a2[1])}", f"{f2(a3[0])} / {f2(a3[1])}"]
names = ['Map-source turnover, $D_R$', 'Ambiguity turnover, $D_A$', 'Grain turnover, $D_G$', 'CORINE vs \\LEN\\ turnover, $D_{RN}$', 'Persistence, $D_R/D_{RN}$',
         'Cross-map regret, mean (range)', 'Endpoint regret, mean', 'Robust core (catchments holding half)', 'Catchment allocation capture (CORINE / \\LEG)', 'Stratified allocation capture (CORINE / \\LEG)']
lines = [f"{n} & {cols[1][i]} & {cols[5][i]} & {cols[10][i]} \\\\" for i, n in enumerate(names)]
(OUT / 'table2_budgets.tex').write_text('\n'.join(lines) + '\n')

# ---- Table 3 ----
rob = list(csv.DictReader(open(A / 'alloc/robustness_5pct.csv')))
lab = {'primary (B40 fragments)': 'Primary (reaches, 40 m buffer)', '20 m buffer': '20 m buffer', '100 m buffer': '100 m buffer', '1 km segments': '1 km segments',
       '500 m segments': '500 m segments', 'unknown conditional': 'Unknown land excluded from denominator', 'F-Z zero-land reaches dropped jointly': 'Zero-land reaches removed',
       'S-C2 partial-coverage catchments dropped': 'Partial-coverage catchments removed'}
bt = AL['bootstrap_5pct']
t3 = [f"{lab[r['variant']]} & {int(r['units']):,} & {f2(float(r['D_R']))} & {f3(float(r['D_A']))} & {f2(float(r['grain_persistence_share']))} & {f2(float(r['regret_C_lo_to_LEg_lo']))} / {f2(float(r['regret_LEg_lo_to_C_lo']))} & {f2(float(r['core_share']))} \\\\".replace(',', '{,}') for r in rob]
t3.append(f"Catchment bootstrap (2.5--97.5\\%) & -- & {f2(bt['D_R']['p2.5'])}--{f2(bt['D_R']['p97.5'])} & {f3(bt['D_A']['p2.5'])}--{f3(bt['D_A']['p97.5'])} & {f2(bt['grain_persistence_share']['p2.5'])}--{f2(bt['grain_persistence_share']['p97.5'])} & "
          f"{f2(bt['regret_C_lo_to_LEg_lo']['p2.5'])}--{f2(bt['regret_C_lo_to_LEg_lo']['p97.5'])} / {f2(bt['regret_LEg_lo_to_C_lo']['p2.5'])}--{f2(bt['regret_LEg_lo_to_C_lo']['p97.5'])} & {f2(bt['core_share']['p2.5'])}--{f2(bt['core_share']['p97.5'])} \\\\")
(OUT / 'table3_robustness.tex').write_text('\n'.join(t3) + '\n')
for p in sorted(OUT.glob('*.tex')): print('=====', p.name); print(p.read_text())
