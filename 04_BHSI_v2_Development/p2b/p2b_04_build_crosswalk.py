"""P2-B Task B: build the frozen-candidate ecological crosswalk table (P2B_ECOLOGICAL_CROSSWALK.csv).
Judgements are written here explicitly (reviewable). Empirical columns come from the descriptive CORINE x LE
cross-tabulation of 274,100 seeded random points (summaries/crosstab_*). The cross-tabulation documents
ambiguity only; it was NOT used to choose or tune any category or score. No suitability model is run.
Existing Phase 1 class scores (indicators.py: 1.0/0.5/0.1/0.0) are the only numerical values referenced.
"""
from pathlib import Path
import csv, json
import pandas as pd

R = Path(__file__).resolve().parents[2]
S = R / '05_Experiments/BHSI_v2_P2B/summaries'
OUT = R / '06_Results_Figures/BHSI_v2_P2B/P2B_ECOLOGICAL_CROSSWALK.csv'
cnt = pd.read_csv(S / 'crosstab_clc_by_le_counts.csv', index_col=0); cnt.index = cnt.index.astype(str)
row = (100 * cnt.div(cnt.sum(axis=1), axis=0)); col = (100 * cnt.div(cnt.sum(axis=0), axis=1))
HIGH = {'311', '313'}; MID = {'312', '321', '322', '323', '324', '411', '412'}
LOW = {'211', '212', '213', '221', '222', '223', '231', '241', '242', '243', '244'}
def p1(code): return '1.0' if code in HIGH else '0.5' if code in MID else '0.1' if code in LOW else '0.0'

# (code, name, category, comparability, evidence, ambiguity, primary_treatment, sensitivity_treatment)
W = 'WATER_EXCLUDED'
CLC = [
 ('111', 'Continuous urban fabric', 'URB', 'yes', 'E1,E2', 'none material', 'P1 score 0.0', 'none'),
 ('112', 'Discontinuous urban fabric', 'URB', 'partial', 'E1,E2', 'Includes gardens and trees; LE Built-up also includes gardens; 42% of points fall in non-urban LE classes (grass/woodland)', 'P1 score 0.0', 'Interval [0.0,0.5] for URB-VEG variant'),
 ('121', 'Industrial or commercial units', 'URB', 'yes', 'E1,E2', '55% of sample points fall in non-urban LE classes at 25 ha grain', 'P1 score 0.0', 'none'),
 ('122', 'Road and rail networks and associated land', 'URB', 'partial', 'E1,E2', 'Linear features below CORINE 100 m width rarely mapped; LE misses roads (NERR108 s4.1)', 'P1 score 0.0', 'none'),
 ('123', 'Port areas', 'URB', 'yes', 'E1,E2', 'Coastal; few inland reaches', 'P1 score 0.0', 'none'),
 ('124', 'Airports', 'URB', 'partial', 'E1,E2', 'Mostly grass-covered in LE (54%)', 'P1 score 0.0', 'Interval [0.0,0.5]'),
 ('131', 'Mineral extraction sites', 'MIN', 'partial', 'E1,E2', 'Heterogeneous in LE (grass 31%, woodland 12%, water 8%)', 'P1 score 0.0', 'none'),
 ('132', 'Dump sites', 'MIN', 'partial', 'E1,E2', 'Heterogeneous in LE', 'P1 score 0.0', 'none'),
 ('133', 'Construction sites', 'MIN', 'partial', 'E1,E2', 'Temporary land cover; 2018 vs 2020-21 change', 'P1 score 0.0', 'none'),
 ('141', 'Green urban areas', 'URBVEG', 'no', 'E1,E2', 'Vegetated by definition; P1 scored 0.0. LE: grass 31%, woodland 31%, improved grass 20%', 'P1 score 0.0 (frozen baseline)', 'Interval [0.0,0.5]'),
 ('142', 'Sport and leisure facilities', 'URBVEG', 'no', 'E1,E2', 'Vegetated pitches/parks; LE: grass 40%, improved 23%, woodland 19%; 1.7% of sample points', 'P1 score 0.0 (frozen baseline)', 'Interval [0.0,0.5]'),
 ('211', 'Non-irrigated arable land', 'ARB', 'yes', 'E1,E2,E3', 'LE arable is taken from RPA CROME 2019 (SrcCode 22), a third dataset; 60% of CORINE 211 points are LE arable, 19% grass, 10% improved grass', 'P1 score 0.1', 'none'),
 ('212', 'Permanently irrigated land', 'ARB', 'yes', 'E1', 'Not present in sample', 'P1 score 0.1', 'none'),
 ('213', 'Rice fields', 'ARB', 'yes', 'E1', 'Not present in England', 'P1 score 0.1', 'none'),
 ('221', 'Vineyards', 'ARB', 'partial', 'E1', 'Not present in sample', 'P1 score 0.1', 'none'),
 ('222', 'Fruit trees and berry plantations', 'ARB', 'partial', 'E1,E2', 'Woody orchards; LE has no orchard class', 'P1 score 0.1', 'none'),
 ('223', 'Olive groves', 'ARB', 'yes', 'E1', 'Not present in England', 'P1 score 0.1', 'none'),
 ('231', 'Pastures, meadows and other permanent grasslands under agricultural use', 'GRS', 'no', 'E1,E2,E3', 'CORINE separates pasture (231) from natural grassland (321). LE splits improved vs acid/calcareous/neutral instead, and NERR108 s4.1 reports over-mapping of semi-natural grassland replacing improved grassland in the south-west. Observed: 38% semi-natural, 33% improved. The sub-distinction is not transferable', 'Category GRS; common scheme uses interval [0.1,0.5] in both sources', 'Native CORINE control keeps P1 0.1; high bound 0.5'),
 ('241', 'Annual crops associated with permanent crops', 'AGM', 'partial', 'E1', 'Not present in sample', 'P1 score 0.1', 'Interval [0.1,0.5]'),
 ('242', 'Complex cultivation patterns', 'AGM', 'no', 'E1,E2', 'Mosaic below LE segment scale; LE: grass 48%, arable 12%, woodland 12%', 'P1 score 0.1', 'Interval [0.1,0.5]'),
 ('243', 'Agriculture with significant areas of natural vegetation', 'AGM', 'no', 'E1,E2', 'Mosaic; LE: grass 39%, woodland 24%, no LE class 11%', 'P1 score 0.1', 'Interval [0.1,0.5]'),
 ('244', 'Agro-forestry areas', 'AGM', 'no', 'E1', 'Not present in England sample', 'P1 score 0.1', 'Interval [0.1,0.5]'),
 ('311', 'Broad-leaved forest', 'BLW', 'yes', 'E1,E2,E3,E4', 'LE merges broadleaved, mixed and yew; 70% of CORINE 311 points are LE broadleaf/mixed, 10% grass, 7% conifer', 'P1 score 1.0', 'none'),
 ('312', 'Coniferous forest', 'CON', 'yes', 'E1,E2,E3', '61% LE conifer, 18% broadleaf/mixed; 10% no LE class (Wales/tidal edge)', 'P1 score 0.5', 'none'),
 ('313', 'Mixed forest', 'BLW', 'partial', 'E1,E2,E3', 'LE has no mixed class: mixed is merged with broadleaf. 54% LE broadleaf/mixed, 25% conifer. The broadleaf-versus-mixed distinction cannot be compared across sources', 'Category BLW (broadleaf+mixed); P1 score 1.0', 'Native CORINE control keeps 311 and 313 separate (both 1.0)'),
 ('321', 'Natural grasslands', 'GRS', 'no', 'E1,E2', 'See 231. Only 43% LE semi-natural grassland; 16% fen/marsh', 'Category GRS; common scheme uses interval [0.1,0.5]', 'Native CORINE control keeps P1 0.5'),
 ('322', 'Moors and heathland', 'RGH', 'partial', 'E1,E2', 'LE dwarf shrub heath 28%, grass 25%, fen/marsh 15%, bog 9%', 'P1 score 0.5', 'none'),
 ('323', 'Sclerophyllous vegetation', 'RGH', 'yes', 'E1', 'Not present in England', 'P1 score 0.5', 'none'),
 ('324', 'Transitional woodland-shrub', 'SCR', 'partial', 'E1,E2,E3', 'Temporary clear-cuts/regrowth/scrub; LE: bog 20%, conifer 19%, broadleaf 19%, no LE 12%. LE Scrub is a distinct, much smaller class', 'P1 score 0.5', 'none'),
 ('331', 'Beaches, dunes, sands', 'COA', 'partial', 'E1,E2', 'Coastal; ineligible tidal setting', 'P1 score 0.0', 'none'),
 ('332', 'Bare rocks', 'BARE', 'partial', 'E1,E2', 'Heterogeneous in LE', 'P1 score 0.0', 'none'),
 ('333', 'Sparsely vegetated areas', 'BARE', 'no', 'E1,E2', 'LE: fen/marsh 30%, bog 28%, grass 26%: upland vegetation, not bare ground', 'P1 score 0.0 (frozen baseline)', 'Interval [0.0,0.5]'),
 ('334', 'Burnt areas', 'BARE', 'yes', 'E1', 'Not present in England sample', 'P1 score 0.0', 'none'),
 ('335', 'Glaciers and perpetual snow', 'BARE', 'yes', 'E1', 'Not present in England', 'P1 score 0.0', 'none'),
 ('411', 'Inland marshes', 'WET', 'partial', 'E1,E2', 'LE: improved grass 26%, fen/marsh 25%, grass 23%', 'P1 score 0.5', 'none'),
 ('412', 'Peat bogs', 'WET', 'partial', 'E1,E2', 'LE bog 42%, dwarf shrub heath 31%', 'P1 score 0.5', 'none'),
 ('421', 'Salt marshes', 'COA', 'partial', 'E1,E2', 'LE saltmarsh 55%; 24% no LE class (seaward of MHWS)', 'P1 score 0.0', 'none'),
 ('422', 'Salines', 'COA', 'yes', 'E1', 'Not present in England', 'P1 score 0.0', 'none'),
 ('423', 'Intertidal flats', 'COA', 'no', 'E1,E2', '84% outside LE (LE ends at mean high water springs)', 'P1 score 0.0', 'none'),
 ('511', 'Water courses', W, 'no', 'E1,E2,E5', 'CORINE maps only rivers wider than its 100 m minimum width; 75% of sampled 511 points have no LE class. Channel representation differs by source (see water rules)', 'Excluded from numerator and denominator; water fraction recorded', 'S-W3: water scored 0.0 as in Phase 1'),
 ('512', 'Water bodies', W, 'partial', 'E1,E2,E5', '75% LE Water; 25 ha MMU vs 300 m2', 'Excluded from numerator and denominator; water fraction recorded', 'S-W3: water scored 0.0 as in Phase 1'),
 ('521', 'Coastal lagoons', W, 'partial', 'E1,E2', 'Tidal', 'Excluded as water', 'S-W3'),
 ('522', 'Estuaries', W, 'no', 'E1,E2,E5', '97% outside LE', 'Excluded as water; reach ineligible anyway (tidal)', 'S-W3'),
 ('523', 'Sea and ocean', W, 'no', 'E1,E2', '98% outside LE', 'Excluded as water', 'S-W3'),
]
LE = [
 ('Broadleaved, Mixed and Yew Woodland', 'Woodland', 'BLW', 'partial', 'E1,E2,E3,E4', 'Merges broadleaf, mixed and yew; mixed stands cannot be separated. Trained partly on NFI 2018', 'Category BLW; P1-equivalent score 1.0 via category', 'none'),
 ('Coniferous Woodland', 'Woodland', 'CON', 'yes', 'E1,E2,E3', 'Trained partly on NFI 2018', 'Category CON; P1-equivalent score 0.5 via category', 'none'),
 ('Scrub', 'Woodland', 'SCR', 'partial', 'E1,E2,E3', 'UKBAP lists scrub under Woodland; CORINE 324 is a temporary transitional class. Small area (0.65% of points)', 'Category SCR; P1-equivalent 0.5 via category', 'none'),
 ('Acid, Calcareous, Neutral Grassland', 'Grassland', 'GRS', 'no', 'E1,E2,E3', 'Documented over-mapping replacing improved grassland in the south-west (NERR108 s4.1)', 'Category GRS; interval [0.1,0.5] in common scheme', 'high/low bound'),
 ('Improved Grassland', 'Grassland', 'GRS', 'no', 'E1,E2,E3', 'See above; 33% of CORINE pasture points', 'Category GRS; interval [0.1,0.5] in common scheme', 'high/low bound'),
 ('Bracken', 'Grassland', 'RGH', 'no', 'E1,E2', 'UKBAP places bracken under Grassland, but it is not forage; no CORINE equivalent', 'Category RGH; interval [0.1,0.5]', 'high/low bound'),
 ('Dwarf Shrub Heath', 'Heath', 'RGH', 'partial', 'E1,E2', '28% of CORINE 322 points are LE heath', 'Category RGH; P1-equivalent 0.5', 'none'),
 ('Arable and Horticultural', 'Cropland', 'ARB', 'yes', 'E1,E2', 'Segments with at least 50% RPA CROME 2019 overlap are assigned arable (SrcCode 22); not an independent satellite classification', 'Category ARB; P1-equivalent 0.1', 'none'),
 ('Fen, Marsh and Swamp', 'Wetland', 'WET', 'partial', 'E1,E2', 'Documented over-mapping in the Lake District; 16% of CORINE natural grassland points', 'Category WET; P1-equivalent 0.5', 'none'),
 ('Bog', 'Wetland', 'WET', 'partial', 'E1,E2', '42% of CORINE 412 points are LE bog', 'Category WET; P1-equivalent 0.5', 'none'),
 ('Water', 'Freshwater', W, 'partial', 'E1,E2,E5', 'Bespoke layer (SumIR threshold + HAND + OS VectorMap proximity); thresholds set subjectively; maps channels wider than a few pixels', 'Excluded from numerator and denominator; water fraction recorded', 'S-W3: scored 0.0'),
 ('Built-up Areas and Gardens', 'Urban', 'URB', 'partial', 'E1,E2', 'Segment assigned if at least 33% OS VectorMap buildings (SrcCode 20); gardens included; roads often missed (NERR108 s4.1)', 'Category URB; P1-equivalent 0.0', 'none'),
 ('Coastal Saltmarsh', 'Coastal', 'COA', 'partial', 'E1,E2', 'From EA saltmarsh extent (SrcCode 21)', 'Category COA; P1-equivalent 0.0', 'none'),
 ('Coastal Sand Dunes', 'Coastal', 'COA', 'partial', 'E1,E2', 'Coastal', 'Category COA; P1-equivalent 0.0', 'none'),
 ('Bare Sand', 'Bare Ground', 'BARE', 'partial', 'E1,E2', 'NERR108 s4.1: some bare sand misclassified as other habitats', 'Category BARE; P1-equivalent 0.0', 'none'),
 ('Bare Ground', 'Bare Ground', 'BARE', 'partial', 'E1,E2', 'Bespoke coherence and NDVI thresholds', 'Category BARE; P1-equivalent 0.0', 'none'),
 ('Unclassified', 'Unclassified', 'UNK', 'no', 'E1,E2', 'Cloud or highly reflective urban areas flagged as cloud (SrcCode 99); 0.32% of sample', 'Unknown: bounds [0,1], excluded length reported (Phase 1 unknown policy)', 'none'),
]
CAT = {
 'BLW': 'Broadleaf and mixed woodland', 'CON': 'Coniferous woodland', 'SCR': 'Shrub and transitional woodland-scrub',
 'GRS': 'Grassland and pasture', 'ARB': 'Arable and cropland', 'AGM': 'Heterogeneous agriculture (mosaics, agro-forestry)',
 'WET': 'Wetland and peat', 'RGH': 'Heath, moor and rough vegetation', 'URB': 'Urban and artificial surfaces',
 'URBVEG': 'Vegetated urban (green urban, sport, leisure)', 'MIN': 'Extraction, dump and construction',
 'BARE': 'Bare and sparsely vegetated', 'COA': 'Coastal and intertidal land', W: 'Open water (river, lake, marine, estuary)', 'UNK': 'Unclassified or ambiguous'}
CATSCORE = {  # score treatment in the COMMON category scheme (only existing Phase 1 levels are used)
 'BLW': '1.0', 'CON': '0.5', 'SCR': '0.5', 'GRS': 'interval[0.1,0.5]', 'ARB': '0.1', 'AGM': '0.1 (sens. interval[0.1,0.5])',
 'WET': '0.5', 'RGH': '0.5 (bracken interval[0.1,0.5])', 'URB': '0.0', 'URBVEG': '0.0 (sens. interval[0.0,0.5])', 'MIN': '0.0',
 'BARE': '0.0', 'COA': '0.0', W: 'excluded from denominator', 'UNK': 'unknown bounds [0,1]'}
rows = []
for code, name, cat, comp, ev, amb, prim, sens in CLC:
    n = int(cnt.loc[code].sum()) if code in cnt.index else 0
    top = '; '.join(f'{c} {v:.0f}%' for c, v in row.loc[code].sort_values(ascending=False).head(3).items() if v >= 1) if n else 'not sampled'
    rows.append(dict(source='CORINE2018', class_id=code, class_name=name, source_group='CLC level-3', phase1_score=p1(code),
        ecological_category=cat, category_label=CAT[cat], category_score_common_scheme=CATSCORE[cat], comparable_across_sources=comp,
        n_sample_points=n, top_classes_in_other_source_pct=top, evidence_ids=ev, ambiguity_or_information_loss=amb,
        primary_treatment=prim, sensitivity_treatment=sens))
for name, grp, cat, comp, ev, amb, prim, sens in LE:
    n = int(cnt[name].sum()) if name in cnt.columns else 0
    top = '; '.join(f'{c} {v:.0f}%' for c, v in col[name].sort_values(ascending=False).head(3).items() if v >= 1) if n else 'not sampled'
    rows.append(dict(source='LivingEngland_PhaseIV', class_id=name, class_name=name, source_group=grp, phase1_score='n/a (not scored in Phase 1)',
        ecological_category=cat, category_label=CAT[cat], category_score_common_scheme=CATSCORE[cat], comparable_across_sources=comp,
        n_sample_points=n, top_classes_in_other_source_pct=top, evidence_ids=ev, ambiguity_or_information_loss=amb,
        primary_treatment=prim, sensitivity_treatment=sens))
df = pd.DataFrame(rows)
df.to_csv(OUT, index=False, quoting=csv.QUOTE_MINIMAL)
chk = {'rows': len(df), 'clc_rows': int((df.source == 'CORINE2018').sum()), 'le_rows': int((df.source != 'CORINE2018').sum()),
       'clc_codes_complete': sorted(df[df.source == 'CORINE2018'].class_id) == sorted(HIGH | MID | LOW | {'111','112','121','122','123','124','131','132','133','141','142','331','332','333','334','335','421','422','423','511','512','521','522','523'}),
       'le_classes_observed_all_mapped': set(cnt.columns) - {'<<none>>'} <= set(df.class_id)}
print(chk)
assert chk['clc_codes_complete'] and chk['le_classes_observed_all_mapped'] and chk['clc_rows'] == 44 and chk['le_rows'] == 17
(S / 'crosswalk_build_checks.json').write_text(json.dumps(chk, indent=1) + '\n')
