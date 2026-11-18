"""Unit tests: P2-C3 allocation, metrics and scoring invariants (synthetic data)."""
import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p2c3_alloc as A


def inst(n=400, seed=0):
    r = np.random.default_rng(seed)
    return r.uniform(1, 3000, n), r.uniform(0, 1, n), r.integers(1, 12, n), r.permutation(n)


class TestAllocation(unittest.TestCase):
    def test_budget_exact_and_one_partial(self):
        L, s, c, p = inst()
        for f in (0.01, 0.05, 0.10):
            B = f * L.sum()
            for x in (A.a1_reach(s, L, B, p), A.a2_catchment(s, L, c, B, p, np.arange(len(np.unique(c)))), A.a3_stratified(s, L, c, f, p), A.random_alloc(L, B, np.random.default_rng(1))):
                self.assertAlmostEqual((x * L).sum(), B, delta=1e-6)
                self.assertTrue(((x >= 0) & (x <= 1 + 1e-12)).all())
                self.assertLessEqual(((x > 0) & (x < 1)).sum(), len(np.unique(c)))

    def test_a1_is_lp_optimum(self):
        from scipy.optimize import linprog
        L, s, c, p = inst(60, 3); B = 0.07 * L.sum()
        lp = linprog(-(L * s), A_ub=[L], b_ub=[B], bounds=[(0, 1)] * len(L), method='highs')
        self.assertAlmostEqual(A.value(A.a1_reach(s, L, B, p), s, L), -lp.fun, places=6)

    def test_capture_endpoints(self):
        L, s, c, p = inst(); B = 0.05 * L.sum(); x = A.a1_reach(s, L, B, p); ov = A.value(x, s, L)
        cap, reg, ab, pr = A.capture(x, s, L, B, ov); self.assertAlmostEqual(cap, 1.0); self.assertAlmostEqual(reg, 0.0); self.assertAlmostEqual(ab, 0.0)
        caps = [A.capture(A.random_alloc(L, B, np.random.default_rng(k)), s, L, B, ov)[0] for k in range(400)]
        self.assertLess(abs(np.mean(caps)), 0.05)

    def test_constant_scores_regret_undefined(self):
        L, s, c, p = inst(); B = 0.05 * L.sum(); s = np.full_like(s, 0.3); x = A.a1_reach(s, L, B, p)
        self.assertTrue(np.isnan(A.capture(x, s, L, B, A.value(x, s, L))[0]))

    def test_nan_scores_are_zero_value(self):
        L, s, c, p = inst(); s[:50] = np.nan; B = 0.05 * L.sum(); x = A.a1_reach(s, L, B, p)
        self.assertTrue(np.isfinite(A.value(x, s, L))); self.assertEqual(x[:50][s[:50] != s[:50]].sum(), 0)

    def test_a2_whole_catchments_in_mean_order(self):
        L, s, c, p = inst(); B = 0.3 * L.sum(); x = A.a2_catchment(s, L, c, B, p, np.arange(len(np.unique(c))))
        ids = np.unique(c); mc = np.array([np.average(s[c == k], weights=L[c == k]) for k in ids]); sel = np.array([(x * L)[c == k].sum() / L[c == k].sum() for k in ids])
        o = np.argsort(-mc); filled = sel[o]
        self.assertTrue(np.all(np.diff(filled) <= 1e-12))          # non-increasing along the catchment ranking
        self.assertLessEqual(((filled > 1e-12) & (filled < 1 - 1e-12)).sum(), 1)

    def test_a3_fraction_per_catchment(self):
        L, s, c, p = inst(); x = A.a3_stratified(s, L, c, 0.05, p)
        for k in np.unique(c): self.assertAlmostEqual((x * L)[c == k].sum(), 0.05 * L[c == k].sum(), delta=1e-6)

    def test_deterministic_given_perm(self):
        L, s, c, p = inst(); s = np.round(s, 1); B = 0.05 * L.sum()
        self.assertTrue(np.array_equal(A.a1_reach(s, L, B, p), A.a1_reach(s, L, B, p)))

    def test_overlap_and_concentration(self):
        L, s, c, p = inst(); B = 0.05 * L.sum(); x = A.a1_reach(s, L, B, p)
        self.assertAlmostEqual(A.overlap(x, x, L, B)['replaced_fraction'], 0.0)
        y = A.a1_reach(-s, L, B, p); self.assertAlmostEqual(A.overlap(x, y, L, B)['replaced_fraction'], 1.0, places=6)
        k = A.concentration(np.ones(10)); self.assertAlmostEqual(k['effective_n_catchments'], 10); self.assertAlmostEqual(k['gini'], 0.0)
        self.assertAlmostEqual(A.redistribution(np.array([1., 0.]), np.array([0., 1.]), 1.0), 1.0)


class TestScores(unittest.TestCase):
    def test_compose_formula(self):
        import p2c3_scores as S
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'p2c')); import p2c_lc as L
        ct = L.class_table(Path(__file__).resolve().parents[2] / '06_Results_Figures/BHSI_v2_P2B/P2B_ECOLOGICAL_CROSSWALK.csv')
        keys = list(ct[ct.source == 'LE'].class_key)
        cnt = np.zeros((3, len(keys) + 1))
        cnt[0, keys.index('Broadleaved, Mixed and Yew Woodland') + 1] = 50; cnt[0, keys.index('Improved Grassland') + 1] = 30; cnt[0, keys.index('Water') + 1] = 20; cnt[0, 0] = 20
        cnt[1, keys.index('Water') + 1] = 10                       # zero land
        cnt[2, keys.index('Unclassified') + 1] = 10; cnt[2, keys.index('Arable and Horticultural') + 1] = 10
        o = S.compose(cnt, ct, 'LE')
        self.assertAlmostEqual(o.s_lo[0], (50 * 1.0 + 30 * 0.1) / 100); self.assertAlmostEqual(o.s_hi[0], (50 + 30 * 0.5 + 20) / 100)
        self.assertTrue(np.isnan(o.s_lo[1])); self.assertAlmostEqual(o.water_frac[1], 1.0)
        self.assertAlmostEqual(o.s_lo[2], 0.05); self.assertAlmostEqual(o.s_hi[2], 0.55); self.assertAlmostEqual(o.woody[0], 0.5)
        oc = S.compose(cnt, ct, 'LE', unknown='conditional'); self.assertAlmostEqual(oc.s_lo[2], 0.1); self.assertAlmostEqual(oc.s_lo[0], 53 / 80)


if __name__ == '__main__':
    unittest.main()
