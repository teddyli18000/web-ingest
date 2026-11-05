#!/usr/bin/env python3
"""Native MTS LABS trajectory mechanism diagnostics: distinguish true within-Tabu
paths from GA population-record jumps, keep run boundaries and odd/even parity.
"""
import argparse,csv,gzip,json,pathlib
import numpy as np,pandas as pd

def clean(v):
 if isinstance(v,np.generic):return v.item()
 if isinstance(v,dict):return {k:clean(w) for k,w in v.items()}
 if isinstance(v,list):return [clean(w) for w in v]
 return v

def classify_modes(df):
 od=df['deltaOdd'];ev=df['deltaEven'];g=df['gain']
 assert (od+ev==-g).all()
 imp=df[g>0].copy();o=imp['deltaOdd'];e=imp['deltaEven']
 imp['mode']=np.select([(o<0)&(e<0),(o>0)&(e<0),(o<0)&(e>0),(o==0)|(e==0)],
  ['both_improve','odd_cost_even_repair','even_cost_odd_repair','one_axis_flat'],default='other')
 imp['large_net_change']=(imp.hammingBest>=imp.N/4)
 imp['odd_cost_ratio']=np.where(o>0,(-e)/o,np.nan)
 return imp

def describe_group(df):
 x=classify_modes(df);modes=x['mode'].value_counts().to_dict()
 return dict(episodes=len(df),improvement_count=len(x),
  improvement_rate=float(len(x)/len(df)) if len(df) else None,
  modes={k:dict(count=int(v),frac=float(v/len(x))) for k,v in modes.items()},
  mean_success_hamming=float(x.hammingBest.mean()) if len(x) else None,
  med_success_hamming=float(x.hammingBest.median()) if len(x) else None,
  pct_net_change_ge_N_over4=float(x.large_net_change.mean()) if len(x) else None,
  mean_odd_cost_ratio=float(x.loc[x['mode']=='odd_cost_even_repair','odd_cost_ratio'].mean()) if (x['mode']=='odd_cost_even_repair').any() else None,
  ga_global_records=int(df.is_global_record.sum()),
  percent_of_successes_with_odd_increase=float((x.deltaOdd>0).mean()) if len(x) else None)

def record_transitions(df):
 out=[]
 for (n,seed),v in df.groupby(['N','seed']):
  v=v.sort_values('gen',kind='stable').reset_index(drop=True)
  for j in range(1,len(v)):
   a=v.iloc[j-1];b=v.iloc[j]
   h=sum(x!=y for x,y in zip(a.bits,b.bits))
   out.append(dict(N=int(n),seed=int(seed),earlier_E=int(a.E),later_E=int(b.E),
    global_gain=int(a.E-b.E),hamming=int(h),dodd=int(b.Dodd-a.Dodd),
    dEven=int(b.Eeven-a.Eeven),dOdd=int(b.Eodd-a.Eodd),
    time_delta_s=float(b.t-a.t),gen_delta=int(b.gen-a.gen),
    src_class=int(a.near),dst_class=int(b.near)))
 return pd.DataFrame(out)

def main():
 p=argparse.ArgumentParser();p.add_argument('episodes');p.add_argument('global_records');p.add_argument('--out',required=True)
 a=p.parse_args();out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 ep=pd.read_csv(a.episodes,sep='\t');record=pd.read_csv(a.global_records,sep='\t',dtype={'bits':str})
 assert len(ep)>0 and len(record)>0
 assert (ep.deltaOdd+ep.deltaEven==-ep.gain).all()
 assert (ep.DoddStart>=0).all() and (ep.DoddEnd>=0).all()
 assert (ep.N>1).all()
 stats={str(int(n)):describe_group(group) for n,group in ep.groupby('N')}
 per_run={f'{int(n)}_{int(seed)}':describe_group(group) for (n,seed),group in ep.groupby(['N','seed'])}
 frame=[]
 for (n,seed),v in ep.groupby(['N','seed']):
  ranks=v.startE.rank(method='first',pct=True)
  q=np.minimum((ranks*4).astype(int),3)
  for j in range(4):
   sub=v[q==j]
   if len(sub):
    one=describe_group(sub)
    frame.append(dict(N=int(n),seed=int(seed),quartile=j,
      median_startE=float(sub.startE.median()),improvement_rate=one['improvement_rate'],
      **{k:one['modes'].get(k,{}).get('frac',0.) for k in ('both_improve','odd_cost_even_repair','even_cost_odd_repair')}))
 if frame:pd.DataFrame(frame).to_csv(out/'quality_quartile_by_run.tsv',sep='\t',index=False)
 trans=record_transitions(record)
 if len(trans):trans.to_csv(out/'ga_record_jumps_not_paths.tsv',sep='\t',index=False)
 result=dict(source='original 2009-era unrestricted lMAts native code',
  episode_and_record_counts=dict(episodes=len(ep),records=len(record),record_jumps=len(trans)),
  by_length=stats,by_independent_run=per_run,
  interpretation=[
   'A GA record jump may arise from crossover of separate population lineages; it is NOT a physical path.',
   'The Hamming distance between TS_START and TS best is a NET coordinate change across a multi-flip trajectory, not a simultaneous flip.',
   'Odd/even tradeoffs are computed from exact LABS energy and parity-correct odd defect.',
   'Per-run and per-length output is observational; within-run episodes are not independent trials.',
   'Historical 2009 source is not the 2025 GPU-MTS at N92-100 record quality.'])
 (out/'mechanism_native.json').write_text(json.dumps(clean(result),ensure_ascii=False,indent=2)+'\n')
 print('PASS',len(ep),'episodes',len(record),'GA records',len(trans),'population jumps',flush=True)
 for n,x in stats.items():
  print('N',n,'episodes',x['episodes'],'improved',x['improvement_count'],
        'odd-cost-even-repair fraction',x['modes'].get('odd_cost_even_repair',{}).get('frac'),flush=True)

if __name__=='__main__':main()
