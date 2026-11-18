"""Canonical river pieces, independent of thematic overlays."""
import numpy as np,pandas as pd,geopandas as gpd,shapely

def canonical_clip(raw,catch):
 x=gpd.overlay(raw,catch[['CaBA_ID','geometry']],how='intersection',keep_geom_type=True).explode(index_parts=False,ignore_index=True)
 x=x.loc[x.geometry.length>0].reset_index(drop=True);before=float(x.geometry.length.sum());boundary=0
 mask_keep=np.ones(len(x),dtype=bool);replacement=[];overlap_excess=0.;length_array=x.geometry.length.values
 for sr,locs in x.groupby('source_row',sort=False).indices.items():
  if len(locs)==1:continue
  group=x.iloc[locs].copy();total=float(length_array[locs].sum());union=shapely.union_all(group.geometry.values);excess=total-union.length;overlap_excess+=excess
  if excess<=max(1e-7,total*1e-10):continue
  boundary+=1;mask_keep[locs]=False;used=None
  for _,row in group.sort_values('CaBA_ID',kind='stable').iterrows():
   g=row.geometry if used is None else row.geometry.difference(used);used=row.geometry if used is None else used.union(row.geometry)
   if not g.is_empty:
    if g.geom_type=='LineString':parts=[g]
    elif g.geom_type=='MultiLineString':parts=list(g.geoms)
    else:parts=[p for p in getattr(g,'geoms',[]) if p.geom_type=='LineString']
    for part in parts:
     if part.length>1e-8:q=row.to_dict();q['geometry']=part;replacement.append(q)
 x=gpd.GeoDataFrame(pd.concat([x.loc[mask_keep].copy(),gpd.GeoDataFrame(replacement,geometry='geometry',crs=raw.crs)] if replacement else [x.loc[mask_keep].copy()],ignore_index=True),geometry='geometry',crs=raw.crs)
 return x,{'before_length_m':before,'union_expected_m':before-overlap_excess,'shared_source_rows':boundary,'removed_shared_m':before-x.geometry.length.sum()}
