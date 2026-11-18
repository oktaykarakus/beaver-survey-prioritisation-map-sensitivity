"""Transparent indicator accounting. Unknown values remain unknown or explicit bounds."""
import numpy as np
import pandas as pd
from rasterio.mask import mask
import shapely
CORINE_HIGH={'311','313'}
CORINE_MID={'312','321','322','323','324','411','412'}
CORINE_LOW={'211','212','213','221','222','223','231','241','242','243','244'}
CORINE_ZERO={'111','112','121','122','123','124','131','132','133','141','142','331','332','333','334','335','421','422','423','511','512','521','522','523'}
def corine_score(code):
 s=pd.Series(code).astype(str).str.replace(r'\.0$','',regex=True)
 return np.select([s.isin(CORINE_HIGH),s.isin(CORINE_MID),s.isin(CORINE_LOW),s.isin(CORINE_ZERO)],[1.,.5,.1,0.],default=np.nan)
def geology_score(desc,strict=True):
 s=pd.Series(desc).fillna('').str.lower()
 out=np.select([s.str.contains('alluvium|clay|silt|mud'),s.str.contains('peat|diamicton|till|drift'),s.str.contains('sand|gravel|rock|stone|cliff')],[1.,.5,0.],default=np.nan if strict else 0.)
 if strict:out[s.str.contains('not mapped|unmapped|unknown')]=np.nan
 return out

def gradient_score(e0,e1,length):
 e0,e1,length=map(lambda x:np.asarray(x,dtype=float),(e0,e1,length))
 valid=np.isfinite(e0)&np.isfinite(e1)&np.isfinite(length)&(length>0)
 pct=np.full(len(length),np.nan);pct[valid]=abs(e1[valid]-e0[valid])/length[valid]*100
 score=np.select([pct<=6,(pct>6)&(pct<=12),(pct>12)&(pct<15),pct>=15],[1.,.5,.1,0.],default=np.nan)
 return pct,score

def climate_score(cold,warm):
 cold,warm=np.asarray(cold),np.asarray(warm);v=np.isfinite(cold)&np.isfinite(warm)
 return np.where(v,np.select([(cold>2)&(warm<15),cold<0],[1.,.1],default=.5),np.nan)

def extract_temperature(src,geom):
 arr,tr=mask(src,[geom],crop=True,filled=False)
 data=arr.compressed();data=data[np.isfinite(data)]
 if len(data)==0:return {'mean_c':np.nan,'valid_pixels':0,'reason':'no_valid_pixels'}
 return {'mean_c':float(data.mean()*src.scales[0]+src.offsets[0]),'valid_pixels':len(data),'reason':'observed'}

def interval_linear(lo,hi,coef,intercept=0):
 lo,hi,coef=np.asarray(lo,float),np.asarray(hi,float),np.asarray(coef,float)
 if np.any(lo>hi+1e-10):raise ValueError('reversed bounds')
 return np.where(coef>=0,lo,hi)@coef+intercept,np.where(coef>=0,hi,lo)@coef+intercept

def rank_envelope(lo,hi):
 """Conservative possible rank range (rank1 is highest). Strict superiority, ties share minimum rank."""
 lo,hi=np.asarray(lo),np.asarray(hi)
 best=1+(lo[None,:]>hi[:,None]+1e-12).sum(axis=1)
 possible=(hi[None,:]>lo[:,None]+1e-12);np.fill_diagonal(possible,False)
 worst=1+possible.sum(axis=1)
 return best,worst

def composition(buffer,polygons,scores):
 """Known weighted numerator + known area; union priority resolves real overlaps deterministically."""
 total=float(buffer.area);used=None;known=weighted=raw=0.
 for poly,score in zip(polygons,scores):
  cut=buffer.intersection(poly);raw+=cut.area
  fresh=cut if used is None else cut.difference(used)
  used=cut if used is None else used.union(cut)
  if np.isfinite(score):known+=fresh.area;weighted+=fresh.area*score
 covered=0. if used is None else used.area
 return {'known_fraction':min(1.,known/total),'mapped_fraction':min(1.,covered/total),'lower':weighted/total,'upper':(weighted+total-known)/total,'overlap_area':max(0.,raw-covered)}

def linear_point(values,coef,intercept=0.):
 """Exclude zero-weight constructs explicitly; retain missingness in every retained construct."""
 values,coef=np.asarray(values,float),np.asarray(coef,float);keep=coef!=0
 return values[:,keep]@coef[keep]+intercept
