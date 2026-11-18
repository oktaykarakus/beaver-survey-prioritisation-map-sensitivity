"""Primary two-term candidate: buffer canonical clipped parents before any geology overlay."""
from pathlib import Path
import argparse,json,time,hashlib
import numpy as np,pandas as pd,geopandas as gpd,shapely,rasterio
from indicators import corine_score,gradient_score,composition,rank_envelope
from geometry import canonical_clip
R=Path(__file__).resolve().parents[2];D=R/'01_BHSI_v1_Frozen/source_snapshot/data';cfg=json.load(Path(__file__).with_name('protocol_lock.json').open())
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();O=a.output.resolve()
if R/'05_Experiments' not in O.parents:raise ValueError('Research experiment output required')
if O.exists() and any(O.iterdir()):raise FileExistsError('Use a new output directory')
O.mkdir(parents=True,exist_ok=True);start=time.time();checks=[]
for name in ['build_native_candidate.py','geometry.py','indicators.py']:(O/('executed_'+name)).write_bytes(Path(__file__).with_name(name).read_bytes())
def check(name,ok,value):
 checks.append({'check':name,'passed':bool(ok),'value':str(value)});pd.DataFrame(checks).to_csv(O/'native_checks.csv',index=False)
 if not ok:raise AssertionError((name,value))
def src(pattern):
 x=list(D.rglob(pattern));assert len(x)==1;return x[0]
def log(*x):print(time.strftime('%H:%M:%S'),*x,flush=True)
base=pd.read_csv(R/'05_Experiments/P1_5_Portability/script/catchments_107.csv').set_index('CaBA_ID');ids=base.index
catch=gpd.read_file(src('Wild_Beaver_Catchments_England_*.geojson')).to_crs(27700);catch.geometry=catch.geometry.buffer(0);catch=catch.set_index('CaBA_ID').loc[ids].reset_index()
raw=gpd.read_file(src('oprvrs_gb.gpkg'),layer='watercourse_link',columns=['id','geometry']).to_crs(27700);raw['source_row']=np.arange(len(raw));raw=raw[['source_row','id','geometry']]
log('canonical clip');r,audit=canonical_clip(raw,catch);r['length_m']=r.geometry.length;r['piece_id']=[f'native:{int(a)}:{int(b)}:{i}' for i,(a,b) in enumerate(zip(r.source_row,r.CaBA_ID))]
check('native length equals source union',abs(r.length_m.sum()-audit['union_expected_m'])<1e-5,audit);check('native unique positive pieces',r.piece_id.is_unique and (r.length_m>0).all(),len(r))
starts=np.array([g.coords[0][:2] for g in r.geometry]);ends=np.array([g.coords[-1][:2] for g in r.geometry])
with rasterio.open(src('merged_terrain50.tif')) as dtm:
 e0=np.array([v[0] for v in dtm.sample(starts,masked=True)],dtype=float);e1=np.array([v[0] for v in dtm.sample(ends,masked=True)],dtype=float)
 outside=((starts[:,0]<dtm.bounds.left)|(starts[:,0]>=dtm.bounds.right)|(starts[:,1]<dtm.bounds.bottom)|(starts[:,1]>=dtm.bounds.top)|(ends[:,0]<dtm.bounds.left)|(ends[:,0]>=dtm.bounds.right)|(ends[:,1]<dtm.bounds.bottom)|(ends[:,1]>=dtm.bounds.top));e0[outside]=np.nan;e1[outside]=np.nan
r['gradient_pct'],r['gradient_score']=gradient_score(e0,e1,r.length_m);check('native gradient finite',r.gradient_score.notna().all(),int(r.gradient_score.isna().sum()))
cor=gpd.read_file(src('U2018_CLC2018_V2020_20u1.gpkg')).to_crs(27700)[['Code_18','geometry']];cor['lc_score']=corine_score(cor.Code_18)
buffers=r[['geometry']].copy();buffers.geometry=buffers.geometry.buffer(cfg['buffer_m']);buffers['rid']=np.arange(len(r));log('independent parent CORINE buffers',len(r))
j=gpd.sjoin(buffers,cor,how='left',predicate='intersects');jj=j.loc[j.index_right.notna()].copy();right=cor.geometry.loc[jj.index_right.astype(int)].values;area=shapely.area(shapely.intersection(jj.geometry.values,right));jj['area']=area;jj['known_area']=np.where(jj.lc_score.notna(),area,0.);jj['weighted']=area*jj.lc_score.fillna(0.)
sums=jj.groupby('rid')[['area','known_area','weighted']].sum().reindex(range(len(r))).fillna(0);ba=buffers.geometry.area.values
r['lc_known_fraction']=np.clip(sums.known_area.values/ba,0,1);r['lc_mapped_fraction']=np.clip(sums.area.values/ba,0,1);r['lc_lower']=sums.weighted.values/ba;r['lc_upper']=r.lc_lower+1-r.lc_known_fraction
bad=np.where(sums.area.values>ba*(1+1e-8))[0]
for ix in bad:
 g=jj.loc[jj.rid==ix].sort_values('index_right');co=composition(buffers.geometry.iloc[ix],list(cor.geometry.loc[g.index_right.astype(int)]),g.lc_score.values)
 for col,key in [('lc_known_fraction','known_fraction'),('lc_mapped_fraction','mapped_fraction'),('lc_lower','lower'),('lc_upper','upper')]:r.loc[ix,col]=co[key]
check('native area fractions valid',((r.lc_lower>=-1e-8)&(r.lc_upper<=1+1e-8)&(r.lc_lower<=r.lc_upper+1e-8)).all(),{'overlap_buffers_resolved':len(bad),'unknown_buffers':int((r.lc_known_fraction<1-1e-8).sum())});r['lc_lower']=r.lc_lower.clip(0,1);r['lc_upper']=r.lc_upper.clip(0,1)
r.to_file(O/'canonical_native_rivers.gpkg',driver='GPKG');den=r.groupby('CaBA_ID').length_m.sum().reindex(ids)
def avg(col):return (r[col]*r.length_m).groupby(r.CaBA_ID).sum().reindex(ids)/den
f=pd.DataFrame({'CaBA_Catch':base.CaBA_Catch,'length_m':den,'corine_lower':avg('lc_lower'),'corine_upper':avg('lc_upper'),'corine_known':avg('lc_known_fraction'),'index_gradient':avg('gradient_score')});f['index_corine']=f.corine_lower/f.corine_known.replace(0,np.nan);f.to_csv(O/'native_catchment_features.csv')
check('native107 catchments',len(f)==107 and f.index.is_unique,len(f));check('native conditional corine observed somewhere in each catchment',f.index_corine.notna().all(),int(f.index_corine.isna().sum()))
rows=[]
for model,w in cfg['primary_models'].items():
 l=w[0]*f.corine_lower+w[1]*f.index_gradient;h=w[0]*f.corine_upper+w[1]*f.index_gradient;v=w[0]*f.index_corine+w[1]*f.index_gradient;best,worst=rank_envelope(l,h)
 for label,score in [('lower',l),('upper',h),('known_only_diagnostic',v)]:
  rank=score.rank(ascending=False,method='min')
  for i,cid in enumerate(ids):rows.append({'scenario':'native_direct','model':'native_'+model,'completion':label,'CaBA_ID':cid,'CaBA_Catch':base.loc[cid,'CaBA_Catch'],'score':score.loc[cid],'rank':int(rank.loc[cid]),'score_lower':l.loc[cid],'score_upper':h.loc[cid],'best_possible_rank':int(best[i]),'worst_possible_rank':int(worst[i])})
pd.DataFrame(rows).to_csv(O/'native_scores_and_ranks.csv',index=False)
(O/'run_complete.json').write_text(json.dumps({'success':True,'seconds':time.time()-start,'pieces':len(r),'length_km':r.length_m.sum()/1000,'lengthweighted_corine_unknown_fraction':float(np.average(1-r.lc_known_fraction,weights=r.length_m)),'audit':audit,'checks':len(checks),'all_pass':all(x['passed'] for x in checks),'not_ecologically_validated':True},indent=2)+'\n');log('COMPLETE',time.time()-start)
