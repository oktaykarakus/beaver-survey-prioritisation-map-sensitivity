"""P2-C2 tests: grain-control invariants on synthetic rasters, frozen class/interval table checks, and invariants of the pilot outputs.
Run: PYTHONDONTWRITEBYTECODE=1 python -I test_p2c2.py   (file inserts its own directory on sys.path)"""
import sys, json, hashlib, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import p2c_lc as L

R = Path(__file__).resolve().parents[2]; C2 = R / '05_Experiments/BHSI_v2_P2C/c2'
CW = R / '06_Results_Figures/BHSI_v2_P2B/P2B_ECOLOGICAL_CROSSWALK.csv'


def synth():
    lab = np.ones((200, 400), np.uint8)
    lab[10:20, 10:350] = 2      # 10 px wide, 34 ha  -> kept at r=4.5 (>=9 px), removed at r=5 (needs 11 px)
    lab[50:52, 5:395] = 3       # 2 px wide          -> removed by width
    lab[80:90, 80:90] = 4       # 1 ha island        -> removed by sieve
    lab[100:111, 10:350] = 5    # 11 px wide, 37 ha  -> kept at r=5
    lab[:, 395:] = 0            # no-data margin
    return lab


class TestGrainControl(unittest.TestCase):
    def test_removes_small_and_narrow_keeps_large_wide(self):
        g, _ = L.grain_control(synth(), 2500, 5)
        self.assertEqual(int((g == 3).sum()), 0); self.assertEqual(int((g == 4).sum()), 0); self.assertEqual(int((g == 2).sum()), 0)
        self.assertGreater(int((g == 5).sum()), 3000)

    def test_ninety_metre_sensitivity_keeps_ten_pixel_strip(self):
        g, _ = L.grain_control(synth(), 2500, 4.5)
        self.assertGreater(int((g == 2).sum()), 3000); self.assertEqual(int((g == 3).sum()), 0)

    def test_no_new_classes_nodata_preserved_and_idempotent(self):
        s = synth(); g, _ = L.grain_control(s, 2500, 5)
        self.assertTrue(set(np.unique(g)) <= set(np.unique(s)))
        self.assertTrue(((g == 0) == (s == 0)).all())                       # no-data neither created nor filled
        g2, _ = L.grain_control(g, 2500, 5); self.assertLess(float((g2 != g).mean()), 0.005)   # converges to within tolerance; exact idempotence is not claimed
        self.assertTrue((L.grain_control(s, 2500, 5)[0] == g).all())         # deterministic

    def test_open_disk_geometry(self):
        m = np.zeros((40, 40), bool); m[10:21, 5:35] = True                 # 11 px tall strip
        o = L.open_disk(m, 5)
        self.assertTrue((o <= m).all()); self.assertTrue(o[15, 10:30].all())    # anti-extensive; the centre line survives
        self.assertFalse(o[10, 5]); self.assertTrue(o.sum() > 0.85 * m.sum())   # a disk cannot reach the rectangle's corners
        self.assertEqual(L.open_disk(m, 6).sum(), 0)                            # r=6 needs 13 px (2*floor(r)+1)


class TestClassTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.ct = L.class_table(CW)

    def test_complete(self):
        self.assertEqual((self.ct.source == 'CORINE').sum(), 44); self.assertEqual((self.ct.source == 'LE').sum(), 17)
        self.assertFalse(self.ct.model_category.isna().any())

    def test_intervals_exactly_the_declared_set(self):
        iv = self.ct[self.ct.is_interval]
        self.assertEqual(set(zip(iv.source, iv.class_key)), {('CORINE', k) for k in ('141', '142', '231', '241', '242', '243', '244', '321')} | {('LE', 'Acid, Calcareous, Neutral Grassland'), ('LE', 'Improved Grassland'), ('LE', 'Bracken')})
        self.assertTrue(((iv.lo <= iv.hi)).all()); self.assertEqual(set(zip(iv.lo, iv.hi)), {(0.1, 0.5), (0.0, 0.5)})

    def test_point_scores_match_crosswalk_values(self):
        import re
        cw = pd.read_csv(CW, dtype=str); n = 0
        for _, x in cw.iterrows():
            key = x.class_id if x.source == 'CORINE2018' else x.class_name
            r = self.ct[(self.ct.class_key == key)].iloc[0]
            if r.model_category in ('WATER', 'UNK') or r.is_interval: continue
            expected = float(x.phase1_score) if x.source == 'CORINE2018' else float(re.match(r'[-\d.]+', x.category_score_common_scheme).group())
            self.assertEqual(r.lo, expected, key); self.assertEqual(r.lo, r.hi); n += 1
        self.assertGreater(n, 40)

    def test_water_and_unknown(self):
        w = self.ct[self.ct.model_category == 'WATER']
        self.assertEqual(set(w.class_key[w.source == 'CORINE']), {'511', '512', '521', '522', '523'}); self.assertEqual(set(w.class_key[w.source == 'LE']), {'Water'})
        self.assertEqual(set(self.ct.class_key[self.ct.model_category == 'UNK']), {'Unclassified'})

    def test_frozen_copy_unchanged(self):
        f = pd.read_csv(C2 / 'class_treatment_table_FROZEN.csv', dtype={'class_key': str})
        self.assertTrue((f.class_key.values == self.ct.class_key.values).all()); self.assertTrue((f.model_category.values == self.ct.model_category.values).all())
        self.assertTrue(np.allclose(f.lo.fillna(-9), self.ct.lo.fillna(-9))); self.assertTrue(np.allclose(f.hi.fillna(-9), self.ct.hi.fillna(-9)))


@unittest.skipUnless((C2 / 'pilot_summary.json').exists(), 'pilot outputs not built')
class TestPilotOutputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.S = json.load(open(C2 / 'pilot_summary.json')); cls.reach = pd.read_csv(C2 / 'pilot_reach_table.csv'); cls.comp = pd.read_csv(C2 / 'P2C2_LANDCOVER_COMPARISON.csv')

    def test_selection_documented_first_and_unchanged(self):
        sel = R / '06_Results_Figures/BHSI_v2_P2C/P2C2_PILOT_SELECTION.md'
        self.assertEqual(hashlib.sha256(sel.read_bytes()).hexdigest(), self.S['provenance']['pilot_selection_md_sha256'])
        self.assertEqual(self.S['provenance']['pilot_catchment'], json.load(open(C2 / 'pilot_selection.json'))['chosen_CaBA_ID'])

    def test_class_table_unchanged_since_overlay(self):
        self.assertEqual(hashlib.sha256((C2 / 'class_treatment_table_FROZEN.csv').read_bytes()).hexdigest(), self.S['provenance']['class_table_sha256'])

    def test_reach_length_matches_eligible(self):
        self.assertAlmostEqual(self.reach.length_m.sum() / 1000, self.S['eligible_km'], places=6)

    def test_scores_bounded_and_ordered(self):
        for a in ('C', 'LEn', 'LEg'):
            ok = self.reach[f'{a}_land_px'] > 0
            lo, hi = self.reach.loc[ok, f'{a}_score_lo'], self.reach.loc[ok, f'{a}_score_hi']
            self.assertTrue(((lo >= -1e-12) & (hi <= 1 + 1e-12) & (lo <= hi + 1e-12)).all())

    def test_category_pixels_sum_to_buffer(self):
        for a in ('C', 'LEn', 'LEg'):
            cols = [c for c in self.reach.columns if c.startswith(f'{a}_cat_')]
            self.assertTrue((self.reach[cols].sum(axis=1) + 0 <= self.reach.buffer_px).all())
            land = self.reach[f'{a}_land_px']; wat = self.reach[f'{a}_cat_WATER_px']
            self.assertTrue((land + wat == self.reach.buffer_px).all())

    def test_composition_percent_of_land_sums_to_100(self):
        for a in ('C', 'LEn', 'LEg'):
            for lvl in ('native_class', 'model_category'):
                d = self.comp[(self.comp.arm == a) & (self.comp.level == lvl) & self.comp.pct_of_land.notna()]
                self.assertAlmostEqual(d.pct_of_land.sum(), 100, places=3)

    def test_raster_support_agrees_with_exact_vector_overlay(self):
        for arm, v in self.S['validation_raster_vs_vector_covered_ratio']['mean'].items(): self.assertAlmostEqual(v, 1.0, delta=0.01)
        for arm, v in self.S['validation_raster_vs_vector']['mean'].items(): self.assertLess(v, 6.0)   # % of buffer area misallocated, mean over 150 reaches

    def test_agreement_in_unit_interval(self):
        for k, v in self.S['agreement'].items(): self.assertTrue(0 <= v['agreement'] <= 1 and -1 <= v['kappa'] <= 1, k)

    def test_confusion_totals_consistent(self):
        a = pd.read_csv(C2 / 'confusion_C_LEn_buffer_union.csv', index_col=0).values.sum(); b = pd.read_csv(C2 / 'confusion_C_LEg_buffer_union.csv', index_col=0).values.sum()
        self.assertEqual(a, b)

    def test_zero_denominator_reported(self):
        self.assertIn('zero_denominator_reaches', self.S)
        for a, n in self.S['zero_denominator_reaches'].items(): self.assertEqual(n, int((self.reach[f'{a}_land_px'] == 0).sum()))

    def test_grain_control_converged_and_min_patch_met(self):
        last = self.S['grain_control_cycles'][-1]['frac_changed_vs_previous']; self.assertLess(last, 1e-3)
        self.assertLess(self.S['patch_statistics']['LE-G25']['share_of_area_in_patches_lt_25ha_pct'], 1.0)


if __name__ == '__main__': unittest.main()
