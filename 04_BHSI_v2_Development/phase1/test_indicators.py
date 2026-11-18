import unittest,numpy as np,pandas as pd
from shapely.geometry import box
from indicators import *
class ScientificInvariants(unittest.TestCase):
 def test_unmapped_is_not_moderate(self):
  self.assertTrue(np.isnan(geology_score(['DRIFT GEOLOGY NOT MAPPED'])[0]));self.assertEqual(geology_score(['DRIFT GEOLOGY NOT MAPPED'],False)[0],.5)
 def test_unknown_landcover_is_unknown(self):self.assertTrue(np.isnan(corine_score(['unexpected'])[0]))
 def test_composition_conserves_unknown(self):
  x=composition(box(0,0,10,10),[box(0,0,5,10)],[1.]);self.assertAlmostEqual(x['lower'],.5);self.assertAlmostEqual(x['upper'],1);self.assertAlmostEqual(x['known_fraction'],.5)
 def test_overlapping_polygons_not_double_counted(self):
  x=composition(box(0,0,10,10),[box(0,0,7,10),box(3,0,10,10)],[1.,0.]);self.assertAlmostEqual(x['known_fraction'],1);self.assertAlmostEqual(x['lower'],.7);self.assertAlmostEqual(x['overlap_area'],40)
 def test_area_composition_is_order_independent_when_disjoint(self):
  b=box(0,0,10,10);ps=[box(0,0,3,10),box(3,0,10,10)];self.assertEqual(composition(b,ps,[1.,0.]),composition(b,ps[::-1],[0.,1.]))
 def test_gradient_zero_elevation_valid_zero_length_unknown(self):
  pct,s=gradient_score([0,0,0],[6,0,1],[100,100,0]);np.testing.assert_allclose(s[:2],[1,1]);self.assertTrue(np.isnan(s[2]))
 def test_climate_missing_not_moderate(self):self.assertTrue(np.isnan(climate_score([np.nan],[12])[0]))
 def test_signed_interval_arithmetic(self):
  lo,hi=interval_linear([[0.,.2]],[[1.,.8]],[1.,-2.]);self.assertAlmostEqual(lo[0],-1.6);self.assertAlmostEqual(hi[0],.6)
 def test_rank_envelope_does_not_force_uncertain_order(self):
  b,w=rank_envelope([.1,.3,.9],[.7,.8,1.]);np.testing.assert_array_equal(b,[2,2,1]);np.testing.assert_array_equal(w,[3,3,1])
 def test_rank_envelope_exact_matches_min_ranks(self):
  x=np.array([.2,.8,.8,.1]);b,w=rank_envelope(x,x);np.testing.assert_array_equal(b,[3,1,1,4]);np.testing.assert_array_equal(b,w)
 def test_masked_raster_metadata_decode(self):
  from rasterio.io import MemoryFile
  from rasterio.transform import from_origin
  with MemoryFile() as mem:
   with mem.open(driver='GTiff',height=2,width=2,count=1,dtype='uint16',crs='EPSG:27700',transform=from_origin(0,2,1,1),nodata=0) as src:
    src.write(np.array([[2700,0],[2700,2700]],dtype='uint16'),1);src.scales=(.1,);src.offsets=(-273.15,)
    result=extract_temperature(src,box(0,0,2,2));self.assertEqual(result['valid_pixels'],3);self.assertAlmostEqual(result['mean_c'],-3.15)
 def test_all_nodata_remains_unknown(self):
  from rasterio.io import MemoryFile
  from rasterio.transform import from_origin
  with MemoryFile() as mem:
   with mem.open(driver='GTiff',height=1,width=1,count=1,dtype='uint16',crs='EPSG:27700',transform=from_origin(0,1,1,1),nodata=0) as src:
    src.write(np.zeros((1,1),dtype='uint16'),1);v=extract_temperature(src,box(0,0,1,1));self.assertTrue(np.isnan(v['mean_c']));self.assertEqual(v['reason'],'no_valid_pixels')
 def test_outside_raster_raises_instead_of_moderate_score(self):
  from rasterio.io import MemoryFile
  from rasterio.transform import from_origin
  with MemoryFile() as mem:
   with mem.open(driver='GTiff',height=1,width=1,count=1,dtype='uint16',crs='EPSG:27700',transform=from_origin(0,1,1,1),nodata=0) as src:
    with self.assertRaises(ValueError):extract_temperature(src,box(20,20,21,21))
 def test_zero_weight_excludes_unknown_construct(self):
  np.testing.assert_allclose(linear_point([[.7,np.nan]],[1.,0.]),[.7]);self.assertTrue(np.isnan(linear_point([[.7,np.nan]],[.5,.5])[0]))
 def test_boundary_allocation_preserves_crossing_pieces(self):
  import geopandas as gpd
  from shapely.geometry import LineString
  from geometry import canonical_clip
  raw=gpd.GeoDataFrame({'source_row':[0,1],'id':['cross','boundary']},geometry=[LineString([(0,5),(10,5)]),LineString([(5,0),(5,10)])],crs=27700)
  catch=gpd.GeoDataFrame({'CaBA_ID':[1,2]},geometry=[box(0,0,5,10),box(5,0,10,10)],crs=27700)
  x,audit=canonical_clip(raw,catch);self.assertAlmostEqual(x.geometry.length.sum(),20);self.assertEqual(len(x.loc[x.id=='cross']),2);self.assertEqual(set(x.loc[x.id=='boundary','CaBA_ID']),{1})
 def test_boundary_owner_does_not_depend_on_catchment_order(self):
  import geopandas as gpd
  from shapely.geometry import LineString
  from geometry import canonical_clip
  raw=gpd.GeoDataFrame({'source_row':[0],'id':['boundary']},geometry=[LineString([(5,0),(5,10)])],crs=27700)
  catch=gpd.GeoDataFrame({'CaBA_ID':[2,1]},geometry=[box(5,0,10,10),box(0,0,5,10)],crs=27700)
  x,_=canonical_clip(raw,catch);self.assertEqual(list(x.CaBA_ID),[1])
if __name__=='__main__':unittest.main(verbosity=2)
