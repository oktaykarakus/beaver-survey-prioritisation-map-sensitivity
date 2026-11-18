"""P2-B: summaries of (i) OS Open Rivers `form` by catchment (eligibility inputs, no suitability),
(ii) land-cover class under river-piece midpoints, (iii) LE completeness and (iv) CORINE x LE cross-tabulation
(descriptive; documents crosswalk ambiguity only). Read-only inputs. Outputs: 05_Experiments/BHSI_v2_P2B/summaries/.
"""
from pathlib import Path
import json
import numpy as np, pandas as pd, geopandas as gpd, pyogrio

R = Path(__file__).resolve().parents[2]
S = R / '05_Experiments/BHSI_v2_P2B'; OUT = S / 'summaries'; OUT.mkdir(parents=True, exist_ok=True)
D = R / '01_BHSI_v1_Frozen/source_snapshot/data'
OS = next((D / 'Rivers').rglob('oprvrs_gb.gpkg'))
res = {}
# ---- network form by catchment
form = pyogrio.read_dataframe(OS, layer='watercourse_link', read_geometry=False, columns=['id', 'form'])
riv = gpd.read_file(R / '05_Experiments/BHSI_v2_Phase1/native_001/canonical_native_rivers.gpkg', columns=['piece_id', 'id', 'CaBA_ID', 'length_m'], ignore_geometry=True)
riv = riv.merge(form, on='id', how='left')
assert riv.form.notna().all()
names = pd.read_csv(R / '05_Experiments/P1_5_Portability/script/catchments_107.csv').set_index('CaBA_ID').CaBA_Catch
tot = riv.groupby('form').length_m.sum() / 1000
res['national_km_by_form'] = tot.round(2).to_dict(); res['national_pct_by_form'] = (100 * tot / tot.sum()).round(3).to_dict()
cf = riv.pivot_table(index='CaBA_ID', columns='form', values='length_m', aggfunc='sum', fill_value=0) / 1000
for c in ['inlandRiver', 'tidalRiver', 'lake', 'canal']:
    if c not in cf: cf[c] = 0.0
cf['total_km'] = cf[['inlandRiver', 'tidalRiver', 'lake', 'canal']].sum(axis=1)
for c in ['tidalRiver', 'lake', 'canal']: cf[f'pct_{c}'] = 100 * cf[c] / cf.total_km
cf.insert(0, 'CaBA_Catch', names.reindex(cf.index).values)
cf.round(3).to_csv(OUT / 'network_form_by_catchment.csv')
res['catchments_tidal_pct_gt_20'] = cf.loc[cf.pct_tidalRiver > 20, ['CaBA_Catch', 'pct_tidalRiver']].round(1).to_dict('records')
res['catchments_tidal_pct_gt_5'] = int((cf.pct_tidalRiver > 5).sum()); res['catchments_with_any_tidal'] = int((cf.tidalRiver > 0).sum())
res['catchments_all_inland_pct_ge_90'] = int((100 * cf.inlandRiver / cf.total_km >= 90).sum())

# ---- points
P = pd.read_csv(S / 'coverage_sampling/point_samples.csv.gz', low_memory=False)
P['le'] = P['le'].fillna('<<none>>'); P['clc'] = P.clc.fillna('<<none>>').astype(str).str.replace(r'\.0$', '', regex=True)
rnd = P[P.kind == 'random']; mid = P[P.kind == 'midpoint'].merge(riv[['piece_id', 'form']], on='piece_id', how='left')
res['n_random'] = len(rnd); res['n_mid'] = len(mid)
res['le_random_unmatched_pct'] = float(100 * (rnd['le'] == '<<none>>').mean()); res['clc_random_unmatched_pct'] = float(100 * (rnd.clc == '<<none>>').mean())
res['le_mid_unmatched_pct_by_length'] = float(100 * mid.length_m[mid['le'] == '<<none>>'].sum() / mid.length_m.sum())
res['clc_mid_unmatched_pct_by_length'] = float(100 * mid.length_m[mid.clc == '<<none>>'].sum() / mid.length_m.sum())
cc = rnd.groupby('CaBA_ID').apply(lambda x: pd.Series({'n': len(x), 'le_unmatched_pct': 100 * (x['le'] == '<<none>>').mean(),
        'le_unclassified_pct': 100 * (x['le'] == 'Unclassified').mean(), 'clc_unmatched_pct': 100 * (x.clc == '<<none>>').mean()}))
cc.insert(0, 'CaBA_Catch', names.reindex(cc.index).values); cc.round(3).to_csv(OUT / 'le_completeness_by_catchment_random_points.csv')
res['le_unmatched_pct_catchment_max'] = float(cc.le_unmatched_pct.max()); res['le_unclassified_pct_catchment_max'] = float(cc.le_unclassified_pct.max())
res['le_unclassified_pct_national_random'] = float(100 * (rnd['le'] == 'Unclassified').mean())
res['catchments_le_unmatched_gt_1pct'] = cc.loc[cc.le_unmatched_pct > 1, ['CaBA_Catch', 'le_unmatched_pct']].round(2).to_dict('records')
res['catchments_le_unclassified_gt_1pct'] = cc.loc[cc.le_unclassified_pct > 1, ['CaBA_Catch', 'le_unclassified_pct']].round(2).to_dict('records')
# ---- class under river midpoints, by OS form (length-weighted)
def lw_share(df, col):
    t = df.groupby(['form', col]).length_m.sum().reset_index()
    t['pct_of_form_length'] = 100 * t.length_m / t.groupby('form').length_m.transform('sum'); t['km'] = t.length_m / 1000
    return t.drop(columns='length_m')
a = lw_share(mid, 'le'); a.insert(0, 'product', 'LE_PhaseIV'); a = a.rename(columns={'le': 'class'})
b = lw_share(mid, 'clc'); b.insert(0, 'product', 'CORINE2018'); b = b.rename(columns={'clc': 'class'})
pd.concat([a, b]).round(3).to_csv(OUT / 'class_under_river_midpoints_by_osform.csv', index=False)
inl = mid[mid.form == 'inlandRiver']
res['inland_midpoint_le_water_pct_length'] = float(100 * inl.length_m[inl['le'] == 'Water'].sum() / inl.length_m.sum())
res['inland_midpoint_clc_water_pct_length'] = float(100 * inl.length_m[inl.clc.isin(['511', '512'])].sum() / inl.length_m.sum())
tid = mid[mid.form == 'tidalRiver']
res['tidal_midpoint_le_water_pct_length'] = float(100 * tid.length_m[tid['le'] == 'Water'].sum() / max(tid.length_m.sum(), 1))
res['tidal_midpoint_clc_marine_or_water_pct_length'] = float(100 * tid.length_m[tid.clc.isin(['511', '512', '521', '522', '523', '423'])].sum() / max(tid.length_m.sum(), 1))
# ---- cross-tab (random points): row-normalised distribution of LE classes within each CORINE code
X = pd.crosstab(rnd.clc, rnd['le']); X.to_csv(OUT / 'crosstab_clc_by_le_counts.csv')
Xr = (100 * X.div(X.sum(axis=1), axis=0)).round(2); Xr.to_csv(OUT / 'crosstab_clc_by_le_rowpct.csv')
Xc = (100 * X.div(X.sum(axis=0), axis=1)).round(2); Xc.to_csv(OUT / 'crosstab_clc_by_le_colpct.csv')
res['random_points_by_clc'] = rnd.clc.value_counts().to_dict(); res['random_points_by_le'] = rnd['le'].value_counts().to_dict()
# LE source code by class (what fraction of each LE class is vector/ancillary-classified)
src = rnd.assign(src=rnd.le_src).groupby(['le', 'src']).size().unstack(fill_value=0); src.to_csv(OUT / 'le_srccode_by_class_random_points.csv')
# probability distribution of RF-classified segments among river midpoints
rf = mid[mid.le_src == 1]
res['rf_prob_quantiles_under_river_midpoints'] = rf.le_prob.quantile([.1, .25, .5, .75, .9]).round(1).to_dict() if len(rf) else None
res['pct_mid_length_rf_prob_lt_50'] = float(100 * rf.length_m[rf.le_prob < 50].sum() / mid.length_m.sum())
(OUT / 'sampling_network_summary.json').write_text(json.dumps(res, indent=2, default=str) + '\n')
print(json.dumps(res, indent=1, default=str)[:9000])
