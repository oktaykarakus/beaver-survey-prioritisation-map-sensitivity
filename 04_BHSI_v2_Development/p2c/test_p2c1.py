"""P2-C1 tests: unit tests of the split/reason logic on synthetic geometry, and invariants of the saved outputs (read-only).
Run: PYTHONDONTWRITEBYTECODE=1 python -I -m unittest test_p2c1   (cwd = this directory)"""
import sys, json, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, pandas as pd, shapely
from shapely.geometry import box, LineString
import p2c_net as N

R = Path(__file__).resolve().parents[2]; C1 = R / '05_Experiments/BHSI_v2_P2C/c1'


class TestSplit(unittest.TestCase):
    E = box(0, 0, 100, 100); W = box(100, 0, 200, 100)       # England | Wales share the border x=100

    def test_crossing_line_is_cut_and_conserved(self):
        g = LineString([(50, 50), (250, 50)])                   # 50 in E, 100 in W, 50 outside
        out = N.split_line_by_regions(g, [('ENGLAND', self.E), ('WALES', self.W)])
        by = {}
        for n, p in out: by[n] = by.get(n, 0) + p.length
        self.assertAlmostEqual(by['ENGLAND'], 50); self.assertAlmostEqual(by['WALES'], 100); self.assertAlmostEqual(by['OTHER'], 50)
        self.assertAlmostEqual(sum(by.values()), g.length)

    def test_line_on_shared_border_counted_once_england_precedence(self):
        g = LineString([(100, 10), (100, 90)])
        out = N.split_line_by_regions(g, [('ENGLAND', self.E), ('WALES', self.W)])
        self.assertEqual(len(out), 1); self.assertEqual(out[0][0], 'ENGLAND'); self.assertAlmostEqual(out[0][1].length, 80)

    def test_reentrant_line_gives_separate_fragments(self):
        g = LineString([(10, 50), (150, 50), (90, 60), (90, 40)])
        parts, _ = N.classify_and_split(np.array([g], dtype=object), self.E, self.W)
        self.assertAlmostEqual(sum(p.length for _, p in parts[0]), g.length)
        self.assertGreaterEqual(len(parts[0]), 3)

    def test_fast_paths(self):
        gs = np.array([LineString([(10, 10), (20, 20)]), LineString([(110, 10), (120, 20)]), LineString([(500, 500), (510, 510)])], dtype=object)
        parts, n_cut = N.classify_and_split(gs, self.E, self.W)
        self.assertEqual([p[0][0] for p in parts], ['ENGLAND', 'WALES', 'OTHER']); self.assertEqual(n_cut, 0)


class TestReasons(unittest.TestCase):
    def test_precedence_and_all_reasons(self):
        self.assertEqual(N.reasons_for('ENGLAND', 'inlandRiver', True), [])
        self.assertEqual(N.reasons_for('WALES', 'canal', False), ['GEO_WALES', 'FORM_CANAL', 'CATCH_BELOW_MIN'])
        self.assertEqual(N.reasons_for('OTHER', 'tidalRiver', True), ['GEO_OUTSIDE_E_W', 'FORM_TIDAL'])
        self.assertEqual(N.reasons_for('ENGLAND', 'lake', True), ['FORM_LAKE'])
        order = [N.PRECEDENCE.index(c) for c in N.reasons_for('WALES', 'lake', False)]
        self.assertEqual(order, sorted(order))

    def test_unknown_form_is_rejected_not_defaulted(self):
        with self.assertRaises(ValueError): N.reasons_for('ENGLAND', 'mystery', True)


@unittest.skipUnless((C1 / 'p2c1_summary.json').exists(), 'C1 outputs not built')
class TestOutputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import geopandas as gpd
        cls.S = json.load(open(C1 / 'p2c1_summary.json'))
        cls.el = gpd.read_file(C1 / 'p2c1_eligible_network.gpkg'); cls.ex = gpd.read_file(C1 / 'p2c1_excluded_network.gpkg')
        cls.T = pd.read_csv(C1 / 'p2c1_catchment_eligibility.csv')
        cls.P1 = gpd.read_file(R / '05_Experiments/BHSI_v2_Phase1/native_001/canonical_native_rivers.gpkg', columns=['piece_id', 'length_m'], ignore_geometry=True)

    def test_conservation(self):
        tot = self.el.length_m.sum() + self.ex.length_m.sum()
        self.assertAlmostEqual(tot, self.P1.length_m.sum(), delta=1e-3)                  # metres on 8.3e7 m
        self.assertAlmostEqual(self.S['total_km'], self.P1.length_m.sum() / 1000, places=6)
        for pid, g in pd.concat([self.el, self.ex]).groupby('parent_piece_id').length_m: pass
        per = pd.concat([self.el, self.ex]).groupby('parent_piece_id').length_m.sum().reindex(self.P1.piece_id)
        self.assertTrue(per.notna().all()); self.assertLess(np.abs(per.values - self.P1.length_m.values).max(), 1e-4)

    def test_ids_unique_and_disjoint(self):
        a, b = set(self.el.fragment_id), set(self.ex.fragment_id)
        self.assertEqual(len(a), len(self.el)); self.assertEqual(len(b), len(self.ex)); self.assertFalse(a & b)

    def test_eligible_content(self):
        self.assertTrue((self.el.form == 'inlandRiver').all()); self.assertTrue((self.el.geo == 'ENGLAND').all())
        self.assertTrue(self.el.catchment_reportable.all()); self.assertTrue(self.el.geometry.is_valid.all())

    def test_excluded_all_have_reasons_with_precedence(self):
        self.assertTrue((self.ex.reason_primary != '').all())
        first = self.ex.reasons_all.str.split(';').str[0]
        self.assertTrue((first == self.ex.reason_primary).all())
        pos = self.ex.reasons_all.str.split(';').map(lambda l: [N.PRECEDENCE.index(c) for c in l])
        self.assertTrue(all(p == sorted(p) for p in pos))
        self.assertTrue(set(self.ex.reason_primary) <= set(N.PRECEDENCE))

    def test_catchment_table(self):
        T = self.T
        self.assertEqual(len(T), 107); self.assertTrue(T.CaBA_ID.is_unique)
        self.assertEqual(bool((T.reportable_ge10km == (T.km_england_inland_river >= 10)).all()), True)
        self.assertAlmostEqual(T.eligible_km.sum(), self.el.length_m.sum() / 1000, places=6)
        self.assertTrue(((T.eligible_km > 0) == T.reportable_ge10km).all())
        comp = T[['km_wales', 'km_outside_england_wales', 'km_england_tidal', 'km_england_canal', 'km_england_lake_link', 'km_england_inland_river']].sum(axis=1)
        self.assertLess((comp - T.phase1_total_km).abs().max(), 1e-5)
        self.assertEqual(int(T.reportable_ge10km.sum()), self.S['catchments_reportable'])

    def test_all_runtime_checks_passed(self):
        c = pd.read_csv(C1 / 'p2c1_checks.csv'); self.assertTrue(c.passed.all(), c[~c.passed])

    def test_p2b_reference_within_tolerance(self):
        self.assertLess(abs(self.S['eligible_km'] / 71632.7 - 1), 0.005)    # P2-B expected agreement within ~0.5%

    def test_determinism_rerun_hash_if_present(self):
        rr = R / '05_Experiments/BHSI_v2_P2C/verification/c1_rerun/p2c1_content_hash.txt'
        if not rr.exists(): self.skipTest('rerun not performed')
        self.assertEqual(rr.read_text(), (C1 / 'p2c1_content_hash.txt').read_text())


if __name__ == '__main__': unittest.main()
