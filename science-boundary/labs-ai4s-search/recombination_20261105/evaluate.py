#!/usr/bin/env python3
"""Independent audit of elite-parent child outputs and source-orbit clustered comparisons."""
import argparse,csv,collections,json,pathlib,hashlib
import numpy as np

NAMES={0:"parent_copy",1:"uniform_crossover",2:"one_point_crossover",3:"aligned_uniform_crossover",
       4:"marginal_EDA",5:"random_tree_GOM_style",6:"population_MI_tree_GOM_style",7:"exact_autocorrelation_epistasis_tree_GOM_style"}
def exact(b):
    a=[1 if x=='1' else -1 for x in b];return sum(sum(a[i]*a[i+k] for i in range(len(a)-k))**2 for k in range(1,len(a)))
def orb(s):
    alt=lambda x:''.join(c if i%2==0 else ('0' if c=='1' else '1') for i,c in enumerate(x))
    neg=lambda x:''.join('0' if c=='1' else '1' for c in x)
    return sorted({t for x in (s,s[::-1]) for y in (x,alt(x)) for t in (y,neg(y))})
def read(p):
    with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def bootstrap(x,seed):
    x=np.asarray(x,float)
    if not len(x):return [None,None]
    rg=np.random.default_rng(seed)
    return list(map(float,np.quantile(x[rg.integers(len(x),size=(4000,len(x)))].mean(axis=1),[.025,.975])))
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--parents',type=pathlib.Path,required=True)
    p.add_argument('--summary',type=pathlib.Path,required=True)
    p.add_argument('--novel',type=pathlib.Path,required=True)
    p.add_argument('--out',type=pathlib.Path,required=True)
    args=p.parse_args()
    parents=read(args.parents);pmap={z['id']:z for z in parents}
    byN=collections.defaultdict(list)
    for p in parents:
        assert exact(p['bits'])==int(p['E']) and orb(p['bits'])[0]==p['canonical']
        byN[int(p['n'])].append(p)
    pool={n:{p['canonical'] for p in v} for n,v in byN.items()}
    rows=read(args.summary);nov=read(args.novel)
    keys=collections.defaultdict(dict);byMode=collections.defaultdict(list)
    for r in rows:
        n=int(r['N']);i=r['A_id'];j=r['B_id'];arm=int(r['arm']);rep=int(r['rep'])
        assert i in pmap and j in pmap and pmap[i]['n']==pmap[j]['n']==str(n)
        assert int(r['AE'])==int(pmap[i]['E']) and int(r['BE'])==int(pmap[j]['E'])
        assert int(r['bestE'])==exact(r['best_bits']) and orb(r['best_bits'])[0]==r['best_canonical']
        assert int(r['generations'])>=1 and int(r['repair_steps'])==64*int(r['generations'])
        assert float(r['elapsed_ms'])>=100.0
        assert float(r['model_ms'])+float(r['gen_ms'])+float(r['repair_ms'])<=float(r['elapsed_ms'])+1e-4
        assert int(r['new5'])<=int(r['new10'])<=int(r['generations'])
        if arm in [0,1,2,3,4]: assert int(r['gom_trials'])==int(r['gom_accept'])==0
        if arm>=5:assert int(r['gom_trials'])>=int(r['gom_accept'])
        key=(n,r['pair'],rep)
        assert arm not in keys[key]
        keys[key][arm]=r;byMode[(n,arm)].append(r)
    assert all(set(v)==set(NAMES) for v in keys.values())
    # Distinct child certificate per episode should be audited independently, never just count.
    seen=collections.defaultdict(set)
    for z in nov:
        n=int(z['N']);arm=int(z['arm']);rep=int(z['rep']);pair=z['pair']
        seq=z['bits'];E=int(z['E']);ca=z['canonical'];threshold=int(z['threshold'])
        assert len(seq)==n and E==exact(seq) and orb(seq)[0]==ca
        assert ca not in pool[n]
        assert threshold in (5,10)
        assert E<=int(min(int(x['best_known']) for x in byN[n])*(1+threshold/100)+1e-9)
        assert (n,pair,rep) in keys and arm in keys[(n,pair,rep)]
        token=(n,pair,rep,arm,ca)
        if threshold==5:
            assert token not in seen[5]
            seen[5].add(token)
        else:assert token not in seen[10];seen[10].add(token)
    # We store each new5 child once; it should appear in the unique new10 counts as well.
    for r in rows:
        n=int(r['N']);key=(n,r['pair'],int(r['rep']),int(r['arm']))
        n5=sum(z[:4]==key for z in seen[5])
        n10=sum(z[:4]==key for z in seen[5]|seen[10])
        assert n5==int(r['new5']) and n10==int(r['new10']),(key,n5,n10,r['new5'],r['new10'])
    output={'rows':len(rows),'paired_pair_rep_units':len(keys),'novel_certificate_rows':len(nov),
        'methods':NAMES,'lengths':{},'macro_limits':[
          'Known optimum archive sequences N<=60: strict global improvement is impossible',
          'GOMEA-style approximation uses a single FOS pass on uniform child, not the fully tuned published GOMEA optimizer',
          'EDA is independent-bit marginal model, not multivariate state-of-the-art',
          'Multiple source orbits at one length may belong to one shared discovery lineage',
          'Longer N92/99 parents already include the best known solution: rediscovery is not a new record',
          'Pair replicates are not independent parent families; source-length clustering is needed',
          'Repair is costed 64-step Tabu + steepest quench, same for all arms, not modern GPU MTS']}
    for n in sorted(byN):
        group=[(k,v) for k,v in keys.items() if k[0]==n]
        if not group:continue
        baseline=min(int(p['best_known']) for p in byN[n])
        nr={'parent_orbits':len(byN[n]),'pairs':len({k[1] for k,_ in group}),'reps_per_pair':len({k[2] for k,_ in group}),
            'parent_bestE':baseline,'methods':{}}
        for arm,name in NAMES.items():
            r=byMode[(n,arm)]
            vals=np.array([int(q['bestE']) for q in r])
            nov10=np.array([int(q['new10']) for q in r])
            totals=np.array([int(q['generations']) for q in r])
            times=np.array([float(q['elapsed_ms']) for q in r])/1000
            nr['methods'][name]={
             'mean_session_bestE':float(vals.mean()),'best_observedE':int(vals.min()),
             'mean_offspring_after_repair_E':float(np.mean([float(q['meanE']) for q in r])),
             'all_repaired_offspring':int(totals.sum()),'all_novel10_certificates_per_session':int(nov10.sum()),
             'all_novel5_certificates_per_session':int(sum(int(q['new5']) for q in r)),
             'unique_novel10_per_second':float(nov10.sum()/times.sum()),
             'generation_rate_per_second':float(totals.sum()/times.sum()),
             'sessions_with_novel10':int((nov10>0).sum()),
             'sessions_with_strict_energy_gain':int(sum(int(q['strict_gain'])>0 for q in r)),
             'mean_model_ms':float(np.mean([float(q['model_ms']) for q in r])),
             'mean_repair_ms':float(np.mean([float(q['repair_ms']) for q in r]))}
            if arm>0:
                diffs=[]
                for key,arr in group:
                    diffs.append(int(arr[0]['bestE'])-int(arr[arm]['bestE']))
                nr['methods'][name]['paired_bestE_gain_vs_copy']=float(np.mean(diffs))
                nr['methods'][name]['pair_rep_bootCI95_naive_not_independent']=bootstrap(diffs,seed=20261105+arm+n)
        # Marginal incremental value of exact autocorrelation interactivity over
        # MI-FOS and placebo FOS, from exactly matched same pair/rep.
        for candidate,reference,label in [(7,6,'exact_vs_MI'),(7,5,'exact_vs_random_FOS'),(6,5,'MI_vs_random_FOS')]:
            vals=[int(arr[reference]['bestE'])-int(arr[candidate]['bestE']) for _,arr in group]
            gains=[int(arr[candidate]['new10'])-int(arr[reference]['new10']) for _,arr in group]
            nr[label]={'mean_bestE_advantage':float(np.mean(vals)),
                       'mean_new10_certificate_advantage':float(np.mean(gains)),
                       'pair_rep_bootCI95_naive':bootstrap(vals,seed=8123+n+candidate),
                       'win_tie_loss':[int(sum(x>0 for x in vals)),int(sum(x==0 for x in vals)),int(sum(x<0 for x in vals))]}
        output['lengths'][str(n)]=nr
    args.out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print('PASS',len(rows),'complete costed treatments,',len(nov),'independently certified novel child records')
    for n,v in output['lengths'].items():
        print('N',n,'pairs',v['pairs'],'samples',v['reps_per_pair'])
        print('  exact-vs-MI',v['exact_vs_MI'],'per-method E/n10',
              {k:(round(m['mean_session_bestE'],2),m['all_novel10_certificates_per_session'])
               for k,m in v['methods'].items()})
if __name__=='__main__':main()
