"""Unit/integration tests: P2-C3 overlay invariants (synthetic geometry + saved national outputs when present)."""
import sys, json, unittest
from pathlib import Path
import numpy as np, shapely
sys.path.insert(0, str(Path(__file__).resolve().parent))

R = Path(__file__).resolve().parents[2]; OV = R / '05_Experiments/BHSI_v2_P2C3/overlay'; AN = R / '05_Experiments/BHSI_v2_P2C3/analysis'


class TestGeometry(unittest.TestCase):
    def test_buffer_matches_pilot_quad_segs(self):
        # regression for preflight run 1: P2-C2 used BaseGeometry.buffer (quad_segs=16); shapely.buffer defaults to 8
        g = shapely.LineString([(0, 0), (300, 40), (500, -20)])
        self.assertEqual(shapely.buffer(g, 40.0, quad_segs=16).area, g.buffer(40.0).area)
        src = (Path(__file__).resolve().parent / 'p2c3_overlay.py').read_text()
        self.assertNotIn('shapely.buffer(g, wbuf)', src); self.assertIn('quad_segs=16', src)

    def test_segments_conserve_length(self):
        import p2c3_overlay as O
        g = shapely.LineString([(0, 0), (1234.5, 0), (1234.5, 987.6)]); L = g.length
        for sl in (500.0, 1000.0):
            s = O.segments(g, L, sl); self.assertEqual(len(s), int(np.ceil(L / sl))); self.assertAlmostEqual(sum(x.length for x in s), L, places=6)
            self.assertTrue(np.allclose([x.length for x in s], L / len(s)))
        self.assertIsNone(O.segments(g, L, 5000.0))


@unittest.skipUnless((AN / 'assemble_checks.json').exists(), 'national outputs not yet assembled')
class TestNationalOutputs(unittest.TestCase):
    def test_assembly_checks(self):
        c = json.loads((AN / 'assemble_checks.json').read_text())
        self.assertTrue(c['unique'] and c['set_equal_C1']); self.assertEqual(c['catchments'], 105); self.assertLess(abs(c['eligible_km_diff_vs_71629.864']), 1e-6)
        for k in ('B20', 'B100', 'S1000', 'S500'): self.assertLess(abs(c[f'{k}_km_diff']), 1e-6)

    def test_tiles_share_code_hash_and_converged(self):
        hs = set()
        for p in sorted((OV / 'tiles').glob('*.npz')):
            m = json.loads(str(np.load(p)['meta_json'])); hs.add(m['code_hash']); self.assertLessEqual(len(m['grain_control_cycles']), 5)
        self.assertEqual(len(hs), 1)

    def test_scores_bounded_and_ordered(self):
        import pandas as pd
        T = pd.read_parquet(AN / 'reach_table_B40.parquet')
        for a in ('C', 'LEg', 'LEn'):
            lo, hi = T[f'{a}_s_lo'], T[f'{a}_s_hi']; ok = lo.notna()
            self.assertTrue(((lo[ok] >= -1e-12) & (hi[ok] <= 1 + 1e-12) & (lo[ok] <= hi[ok] + 1e-12)).all())
            self.assertTrue((T[f'{a}_land_px'] + T[f'{a}_water_px'] == T.buffer_px).all())
            self.assertTrue((lo.isna() == (T[f'{a}_land_px'] == 0)).all())

    def test_pooled_pixels_counted_once(self):
        Z = np.load(AN / 'pooled.npz'); t = Z['pool_triple'].sum()
        for a in ('C', 'LEn', 'LEg'): self.assertEqual(Z[f'pool_native_{a}'].sum(), t)


if __name__ == '__main__':
    unittest.main()
