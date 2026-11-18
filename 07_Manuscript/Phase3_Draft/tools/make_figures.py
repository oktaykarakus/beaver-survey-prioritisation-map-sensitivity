"""Manuscript V01 figures. Adapted from the verified P2-C3 figure code (04_BHSI_v2_Development/p2c3/p2c3_06_figures.py): same
data sources and numbers; in-plot titles replaced by panel letters (captions live in the manuscript); new Fig. 1 (study region).
Reads only saved, verified P2-C3 outputs; writes PDF (vector) + PNG (300 dpi) to ../figures/. P2-C3 files are not modified.
Usage (frozen venv): python -I -B make_figures.py [FigureName ...]"""
import os, sys, json
from pathlib import Path
os.environ['OGR_GEOJSON_MAX_OBJ_SIZE'] = '0'
import numpy as np, pandas as pd, geopandas as gpd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

R = Path(__file__).resolve().parents[3]; AN = R / '05_Experiments/BHSI_v2_P2C3/analysis'; DEL = R / '06_Results_Figures/BHSI_v2_P2C3'
OUT = Path(__file__).resolve().parents[1] / 'figures'; OUT.mkdir(exist_ok=True)
S1, S2, S3, S4 = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
INK, INK2, MUTED, GRID, AXIS, SURF = '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7', '#ffffff'
SEQ = LinearSegmentedColormap.from_list('seq', ['#f0efec', '#cde2fb', '#86b6ef', '#3987e5', '#256abf', '#104281', '#0d366b'])
DIV = LinearSegmentedColormap.from_list('div', ['#2a78d6', '#86b6ef', '#f0efec', '#f2a48d', '#e34948'])
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8, 'axes.edgecolor': AXIS, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2,
                     'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF,
                     'axes.titlesize': 9, 'axes.titleweight': 'bold', 'axes.titlecolor': INK, 'axes.titlelocation': 'left', 'pdf.fonttype': 42})
ARMC = {'C': S1, 'LEg': S2, 'LEn': S3}; ARML = {'C': 'CORINE 2018', 'LEg': 'Living England, grain-controlled', 'LEn': 'Living England, native'}
REP = json.load(open(AN / 'rep/rep_summary.json')); AL = json.load(open(AN / 'alloc/alloc_summary.json'))
NAMES = {'C_lo': 'CORINE lo', 'C_hi': 'CORINE hi', 'LEg_lo': 'LE-G lo', 'LEg_hi': 'LE-G hi', 'LEn_lo': 'LE-N lo', 'LEn_hi': 'LE-N hi', 'woody_C': 'Woody (CORINE)', 'woody_LEg': 'Woody (LE-G)', 'woody_LEn': 'Woody (LE-N)'}
poly = gpd.read_file(next((R / '01_BHSI_v1_Frozen/source_snapshot/data').rglob('Wild_Beaver_Catchments_England_*.geojson'))).to_crs(27700)
CT = pd.read_csv(AN / 'rep/catchment_representation.csv')


ONLY = set(sys.argv[1:])   # optional figure names to write (e.g. Fig3_spatial_redistribution); default writes all


def save(fig, name):
    if ONLY and name not in ONLY:
        plt.close(fig); return
    for ext in ('pdf', 'png'): fig.savefig(OUT / f'{name}.{ext}', dpi=300, bbox_inches='tight')
    plt.close(fig)


# ---- Fig 1: study region and representation differences ----
el = gpd.read_file(R / '05_Experiments/BHSI_v2_P2C/c1/p2c1_eligible_network.gpkg', columns=['fragment_id'])
fig = plt.figure(figsize=(7.2, 4.6)); a1 = fig.add_axes([0.0, 0.0, 0.46, 1.0]); a2 = fig.add_axes([0.62, 0.1, 0.37, 0.82])
pm = poly.merge(CT[['CaBA_ID', 'agree_C_LEg']], on='CaBA_ID', how='left')
pm[pm.agree_C_LEg.isna()].plot(ax=a1, color='#f0efec', edgecolor=SURF, lw=0.3)
pm.dropna(subset=['agree_C_LEg']).plot(ax=a1, column='agree_C_LEg', cmap=SEQ, vmin=0.2, vmax=0.9, edgecolor=SURF, lw=0.3, legend=True,
                                      legend_kwds={'shrink': 0.45, 'label': 'Category agreement, CORINE vs LE-G', 'location': 'bottom', 'pad': 0.0})
el.plot(ax=a1, color=INK, lw=0.08, alpha=0.6)
a1.set_axis_off(); a1.set_title('a', loc='left')
comp = REP['pooled_composition']; cats = ['BLW', 'CON', 'SCR', 'GRS', 'RGH', 'WET', 'AGM', 'ARB', 'URB', 'URBVEG', 'COA', 'UNK']
lab = {'BLW': 'Broadleaf/mixed wood', 'CON': 'Conifer', 'SCR': 'Scrub', 'GRS': 'Grassland/pasture*', 'RGH': 'Heath/bracken', 'WET': 'Wetland/bog', 'AGM': 'Heterog. agriculture*',
       'ARB': 'Arable', 'URB': 'Urban', 'URBVEG': 'Green urban*', 'COA': 'Coastal', 'UNK': 'Unknown/no data'}
y = np.arange(len(cats)); h = 0.26
for k, a in enumerate(['C', 'LEg', 'LEn']):
    a2.barh(y + (k - 1) * h, [comp[a][f'{c}_pct_land'] for c in cats], height=h - 0.03, color=ARMC[a], label=ARML[a], edgecolor=SURF, lw=0.4)
a2.set_yticks(y, [lab[c] for c in cats]); a2.invert_yaxis(); a2.set_xlabel('% of riparian land (40 m buffers)')
a2.xaxis.grid(True, color=GRID, lw=0.5); a2.set_axisbelow(True); a2.legend(frameon=False, loc='lower right', fontsize=7); a2.set_title('b', loc='left')
save(fig, 'Fig1_study_region_representation')

# ---- Fig 2: grain control ----
pt = REP['pooled_partition']
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.4), gridspec_kw={'width_ratios': [1, 1.1], 'wspace': 0.3})
left = 0
for k, nm, c in (('GRAIN_RESOLVED', 'Resolved by grain control', S1), ('RESID_STRUCTURAL', 'Structural (no LE counterpart)', S4), ('RESID_OTHER', 'Unattributed', MUTED)):
    v = pt[f'{k}_pct_native_disagreement']; a1.barh([0], [v], left=left, color=c, edgecolor=SURF, lw=1.2, height=0.5, label=f'{nm}: {v:.1f}%'); left += v
gi = pt['GRAIN_INTRODUCED_pct_native_disagreement']
a1.barh([-0.65], [gi], color=S2, height=0.3, edgecolor=SURF, label=f'Introduced by grain control: {gi:.1f}%')
# Net reduction = resolved minus introduced; stated as a summary under the bars, not beside the introduced bar it is not.
a1.text(0, -1.12, f'Net reduction in disagreement: {pt["NET_EXPLAINED_pct_native_disagreement"]:.1f}%', ha='left', va='center', fontsize=7.5, color=INK, fontweight='bold')
a1.legend(frameon=False, loc='upper left', bbox_to_anchor=(0, 1.04), fontsize=7)
a1.set_xlim(0, 100); a1.set_ylim(-1.3, 1.35); a1.set_yticks([]); a1.spines['left'].set_visible(False)
a1.set_xlabel('Share of native CORINE–LE disagreement\n(pooled pixels, %)'); a1.set_title('a', loc='left')
a2.plot([0, 1], [0, 1], color=AXIS, lw=0.8)
a2.scatter(CT.agree_C_LEn, CT.agree_C_LEg, s=10 + CT.eligible_km / 70, color=S1, alpha=0.75, edgecolor=SURF, lw=0.5)
a2.set_xlim(0.1, 0.9); a2.set_ylim(0.1, 0.9); a2.set_xlabel('Agreement, CORINE vs LE native'); a2.set_ylabel('Agreement, CORINE vs LE grain-controlled')
a2.grid(True, color=GRID, lw=0.5); a2.set_axisbelow(True); a2.set_title('b', loc='left')
save(fig, 'Fig2_grain_control')

# ---- Fig 3: spatial redistribution of the 5% allocation ----
Z = np.load(AN / 'alloc/allocations_primary_5pct.npz')
elx = gpd.read_file(R / '05_Experiments/BHSI_v2_P2C/c1/p2c1_eligible_network.gpkg', columns=['fragment_id']).set_index('fragment_id').loc[Z['fragment_id']]
xc, xg = Z['A1__C_lo'], Z['A1__LEg_lo']
KM = pd.read_csv(AN / 'alloc/selected_km_by_catchment.csv'); k5 = KM[(KM.budget_pct == 5) & (KM.strategy == 'A1')]
dk = k5[k5.origin == 'LEg_lo'].set_index('CaBA_ID').selected_km - k5[k5.origin == 'C_lo'].set_index('CaBA_ID').selected_km
# Publication-scale legibility: equal map extents for both panels; reaches drawn at 1.2 pt with round caps so short
# reaches remain visible; single-scenario reaches drawn first and the larger 'Both' class on top so it is not hidden.
# The panel-b colour bar sits in an inset so both maps share an identical scale and position.
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 5.0), gridspec_kw={'wspace': 0.02})
x0, y0, x1, y1 = poly.total_bounds; pad = 0.02 * (x1 - x0)
for ax in (a1, a2):
    ax.set_xlim(x0 - pad, x1 + pad); ax.set_ylim(y0 - pad, y1 + pad); ax.set_aspect('equal'); ax.set_axis_off()
poly.boundary.plot(ax=a1, color=AXIS, lw=0.25)
for m, c, l in (((xc > 0) & (xg == 0), S1, 'CORINE only'), ((xg > 0) & (xc == 0), S2, 'LE-G only'), ((xc > 0) & (xg > 0), S3, 'Both')):
    elx[m].plot(ax=a1, color=c, lw=1.2, label=l, capstyle='round', joinstyle='round')
h_, l_ = a1.get_legend_handles_labels(); o_ = [l_.index(x) for x in ('CORINE only', 'LE-G only', 'Both')]
lg = a1.legend([h_[i] for i in o_], [l_[i] for i in o_], frameon=False, loc='upper center', bbox_to_anchor=(0.5, 0.0), ncol=3, fontsize=7,
               title='Selected under (lo endpoint)', title_fontsize=7)
for ln in lg.get_lines(): ln.set_linewidth(2.5)
a1.set_title('a', loc='left')
pm2 = poly.set_index('CaBA_ID').join(dk.rename('d')).dropna(subset=['d']); lim = float(np.nanmax(np.abs(pm2.d)))
cax = a2.inset_axes([0.46, 0.08, 0.42, 0.025])
pm2.plot(ax=a2, column='d', cmap=DIV, vmin=-lim, vmax=lim, edgecolor=SURF, lw=0.3, legend=True, cax=cax,
         legend_kwds={'orientation': 'horizontal', 'label': 'Selected km\n(LE-G lo minus CORINE lo)'})
cax.tick_params(labelsize=7); cax.xaxis.label.set_size(7)
a2.set_title('b', loc='left')
save(fig, 'Fig3_spatial_redistribution')

# ---- Fig 4: cross-scenario regret matrix (5%) ----
RG = pd.read_csv(DEL / 'P2C3_CROSS_SCENARIO_REGRET.csv'); sub = RG[RG.budget_pct == 5]
sc = ['C_lo', 'C_hi', 'LEg_lo', 'LEg_hi', 'LEn_lo', 'LEn_hi']
rows = [('A1', j) for j in sc] + [('R2', f'woody_{a}') for a in ('C', 'LEg', 'LEn')] + [('A2', 'C_lo'), ('A2', 'LEg_lo'), ('A3', 'C_lo'), ('A3', 'LEg_lo')]
Mx = np.array([[sub[(sub.strategy == s_) & (sub.origin == o) & (sub.target == t)].norm_regret.iloc[0] for t in sc] for s_, o in rows])
fig, ax = plt.subplots(figsize=(5.6, 5.6)); im = ax.imshow(np.clip(Mx, 0, 1), cmap=SEQ, vmin=0, vmax=1)
for i, (s_, o) in enumerate(rows):
    for j, t in enumerate(sc):
        v = Mx[i, j]; d = s_ == 'A1' and o == t
        ax.text(j, i, '—' if d else f'{v:.2f}', ha='center', va='center', fontsize=6.5, color='#ffffff' if (v > 0.55 and not d) else INK)
pref = {'A1': 'Reach: ', 'A2': 'Catchment: ', 'A3': 'Stratified: ', 'R2': ''}
ax.set_yticks(range(len(rows)), [pref[s_] + NAMES[o] for s_, o in rows]); ax.set_xticks(range(len(sc)), [NAMES[t] for t in sc], rotation=45, ha='right')
for v in (5.5, 8.5): ax.axhline(v, color=SURF, lw=2.5)
ax.axvline(3.5, color=SURF, lw=2.5)
for spn in ax.spines.values(): spn.set_visible(False)
ax.set_xlabel('Evaluated under scenario'); ax.set_ylabel('Allocation generated under')
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.set_label('Normalised regret (0 = scenario optimum, 1 = random)'); cb.outline.set_visible(False)
save(fig, 'Fig4_regret_matrix')

# ---- Fig 5: budget sensitivity ----
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.3)); b = [1, 5, 10]
for key, nm_, c in (('D_R', 'Map source (CORINE vs LE-G)', S1), ('D_A', 'Ambiguity endpoint (lo vs hi)', S2), ('D_G', 'Grain (LE-N vs LE-G)', S3), ('D_RN', 'CORINE vs LE-N', S4)):
    a1.plot(b, [AL[f'budget_{x}']['contrasts']['A1'][key] for x in b], color=c, lw=1.8, marker='o', ms=4, label=nm_, markeredgecolor=SURF)
a1.plot(b, [1 - x / 100 for x in b], color=MUTED, lw=0.9, ls='--', label='Random expectation')
a1.axhline(0.10, color=INK2, lw=0.7, ls=':'); a1.text(1.1, 0.115, '0.10 benchmark', va='bottom', fontsize=6.5, color=INK2)
a1.set_xticks(b, ['1%', '5%', '10%']); a1.set_xlabel('Survey budget (% of eligible length)'); a1.set_ylabel('Replaced fraction'); a1.set_ylim(0, 1)
a1.yaxis.grid(True, color=GRID, lw=0.5); a1.set_axisbelow(True); a1.legend(frameon=False, fontsize=6.5, loc='upper center', bbox_to_anchor=(0.5, -0.22), ncol=2); a1.set_title('a', loc='left')
for (o, t), nm_, c in ((('C_lo', 'LEg_lo'), 'CORINE lo → LE-G lo', S1), (('LEg_lo', 'C_lo'), 'LE-G lo → CORINE lo', S2), (('C_lo', 'C_hi'), 'CORINE lo → CORINE hi', S3), (('LEg_lo', 'LEg_hi'), 'LE-G lo → LE-G hi', S4)):
    a2.plot(b, [RG[(RG.budget_pct == x) & (RG.strategy == 'A1') & (RG.origin == o) & (RG.target == t)].norm_regret.iloc[0] for x in b], color=c, lw=1.8, marker='o', ms=4, label=nm_, markeredgecolor=SURF)
a2.set_xticks(b, ['1%', '5%', '10%']); a2.set_xlabel('Survey budget'); a2.set_ylabel('Normalised regret'); a2.set_ylim(0, None)
a2.yaxis.grid(True, color=GRID, lw=0.5); a2.set_axisbelow(True); a2.legend(frameon=False, fontsize=6.5, loc='upper center', bbox_to_anchor=(0.5, -0.22), ncol=2); a2.set_title('b', loc='left')
save(fig, 'Fig5_budget_sensitivity')

# ---- Fig S1: allocation overlap matrix (supplementary) ----
M = pd.read_csv(AN / 'alloc/replaced_fraction_matrix_5pct.csv', index_col=0); nm = [NAMES[i.split(':')[1]] for i in M.index]
fig, ax = plt.subplots(figsize=(5.4, 4.8)); im = ax.imshow(M.values.clip(0, 1), cmap=SEQ, vmin=0, vmax=1)
for i in range(len(M)):
    for j in range(len(M)):
        v = max(M.values[i, j], 0.0); ax.text(j, i, '—' if i == j else f'{v:.2f}', ha='center', va='center', fontsize=6.5, color='#ffffff' if v > 0.55 else INK)
ax.set_xticks(range(len(M)), nm, rotation=45, ha='right'); ax.set_yticks(range(len(M)), nm)
for spn in ax.spines.values(): spn.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.set_label('Replaced fraction of the 5% budget'); cb.outline.set_visible(False)
save(fig, 'FigS1_overlap_matrix')
print(sorted(p.name for p in OUT.iterdir()))
