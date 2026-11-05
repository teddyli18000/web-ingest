#!/usr/bin/env python3
"""Independent eightfold alignment and post-repair LABS novelty verifier.

Do not confuse model-free orientation planning with direct third-target oracle;
no training/target-C labels are available to the C++ generator. Same
full-session time and common repair for all methods.
"""
import argparse,csv,collections,json,pathlib
import numpy as np
NAMES={0:'minimum_hamming_alignment',1:'fresh_random_alignment_each_child',
       2:'minimum_mean_raw_crossE_of_16_per_orientation',
       3:'minimum_best_steepest_quench_of_2_per_orientation',
       4:'maximum_hamming_alignment',5:'minimum_best_raw_crossE_of_16_per_orientation',
       6:'parent_copy_and_common_repair'}
def read(p):
    with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def E(s):
    a=[1 if z=='1' else -1 for z in s]
    return sum(sum(a[i]*a[i+k] for i in range(len(a)-k))**2 for k in range(1,len(a)))
def orb(s):
    def inv(t):return ''.join('1' if z=='0' else '0' for z in t)
    def alt(t):return ''.join(z if i%2==0 else inv(z) for i,z in enumerate(t))
    return sorted({z for t in (s,s[::-1]) for v in (t,alt(t)) for z in (v,inv(v))})
def hd(a,b):return sum(x!=y for x,y in zip(a,b))
def bootstrap_by_pair(vals,seed):
    r=np.random.default_rng(seed)
    d=np.asarray(vals,float)
    if len(d)==0:return [None,None]
    s=d[r.integers(len(d),size=(4000,len(d)))].mean(axis=1)
    return [float(x) for x in np.quantile(s,[.025,.975])]
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--parents',type=pathlib.Path,required=True)
    p.add_argument('--sessions',type=pathlib.Path,required=True)
    p.add_argument('--children',type=pathlib.Path,required=True)
    p.add_argument('--out',type=pathlib.Path,required=True)
    a=p.parse_args()
    pp=read(a.parents);rr=read(a.sessions);cc=read(a.children)
    pool={p['id']:p for p in pp}
    grouped=collections.defaultdict(list)
    for p in pp:
        n=int(p['n']);assert len(p['bits'])==n and E(p['bits'])==int(p['E'])
        assert orb(p['bits'])[0]==p['canonical']
        grouped[n].append(p)
    known={n:min(int(p['best_known']) for p in t) for n,t in grouped.items()}
    registry={n:set(p['canonical'] for p in t) for n,t in grouped.items()}
    allrows=collections.defaultdict(dict)
    for row in rr:
        n=int(row['N']);arm=int(row['arm']);rep=int(row['rep'])
        assert arm in NAMES and row['A_id'] in pool and row['B_id'] in pool
        A,B=pool[row['A_id']],pool[row['B_id']]
        assert int(A['n'])==int(B['n'])==n
        assert row['pair']==A['id']+'-'+B['id']
        assert E(row['bestBits'])==int(row['bestE'])
        assert orb(row['bestBits'])[0]==row['bestCanonical']
        dist=min(hd(row['bestBits'],q) for source in (A,B) for q in orb(source['bits']))
        assert int(row['bestNearestParent'])==dist
        assert int(row['repairMoves'])==64*int(row['generations'])
        assert float(row['elapsedMs'])>=120
        assert float(row['proposeMs'])+float(row['repairMs'])+float(row['modelMs'])<=float(row['elapsedMs'])+.05
        assert 0<=int(row['new5'])<=int(row['new10'])<=int(row['new15'])<=int(row['new20'])
        if arm in (0,1,4,6):
            assert int(row['modelCandidates'])==int(row['modelQuenches'])==0
        if arm in (2,5):
            assert int(row['modelCandidates'])>=16
            assert int(row['modelQuenches'])==0
        if arm==3:assert int(row['modelCandidates'])==int(row['modelQuenches'])
        if arm==6:assert int(row['prequenchCalls'])==0
        else: assert int(row['prequenchCalls'])==4*int(row['generations'])
        key=(n,row['pair'],rep)
        assert arm not in allrows[key]
        allrows[key][arm]=row
    assert all(set(arms)==set(NAMES) for arms in allrows.values())
    expectedPairs=sum(len(group)*(len(group)-1)//2 for group in grouped.values())
    assert len({(k[0],k[1]) for k in allrows})==expectedPairs
    counts=collections.defaultdict(lambda:collections.Counter())
    repair_stats=collections.defaultdict(list)
    uniqueness=collections.defaultdict(set)
    for c in cc:
        n=int(c['N']);k=(n,c['pair'],int(c['rep']))
        assert k in allrows and int(c['arm']) in allrows[k]
        r=allrows[k][int(c['arm'])]
        A,B=pool[r['A_id']],pool[r['B_id']]
        s=c['bits'];before=c['beforeBits'];ca=c['canonical']
        assert len(s)==len(before)==n
        assert E(s)==int(c['E']) and E(before)==int(c['beforeE'])
        assert orb(s)[0]==ca and ca not in registry[n]
        assert int(c['E'])<=int(known[n]*1.20+1e-8)
        d=min(hd(s,v) for source in (A,B) for v in orb(source['bits']))
        assert d==int(c['minParentDist'])
        ar=int(c['arm']);idx=int(c['chosenOrientIndex'])
        b_variants=orb(B['bits'])
        assert idx<len(b_variants)
        if ar==6:
            assert before in (A['bits'],B['bits'])
        else:
            Bseq=b_variants[idx];D=[i for i in range(n) if A['bits'][i]!=Bseq[i]]
            Q=[i for i in range(n) if A['bits'][i]==Bseq[i]]
            h=len(D)//2;rcons=4 if n<=47 else 8 if n==50 else 6
            assert sum(before[i]!=A['bits'][i] for i in D)==h
            assert sum(before[i]!=A['bits'][i] for i in Q)==rcons
            c_pre=sum(before[i]!=A['bits'][i] for i in Q)
            c_post=sum(s[i]!=A['bits'][i] for i in Q)
            d_post=sum(s[i]!=A['bits'][i] for i in D)
            repair_stats[(n,ar)].append({'pre_consensus':c_pre,'post_consensus':c_post,
                 'post_donor':d_post,'repair_flip_distance':hd(before,s)})
        key=(n,c['pair'],int(c['rep']),ar)
        assert ca not in uniqueness[key]
        uniqueness[key].add(ca)
        counts[key][5]+=int(int(c['E'])<=known[n]*1.05+1e-8)
        counts[key][10]+=int(int(c['E'])<=known[n]*1.10+1e-8)
        counts[key][15]+=int(int(c['E'])<=known[n]*1.15+1e-8)
        counts[key][20]+=1
    for r in rr:
        n=int(r['N']);k=(n,r['pair'],int(r['rep']),int(r['arm']))
        for t in (5,10,15,20):
            assert counts[k][t]==int(r[f'new{t}']),(k,t,counts[k][t],r[f'new{t}'])
    report={'certified':True,'session_count':len(rr),'source_orbits':len(pp),
            'parent_pair_count':expectedPairs,'full_session_replications':len(allrows),
            'novel_child_certificate_count':len(cc),
            'operators':NAMES,'by_length':{},'known_failure_modes':[
              'Full modern GOMEA and recent GPU-MTS are not reproduced here.',
              'N92 and N99 each contain only one source parent pair.',
              'Model preselection costs counted but 120ms per arm is a small native local-repair pilot budget.',
              'Multiple sessions within one parent pair share source information and are not independent parent families.',
              'A known third optimum that is in the parent registry never counts as a new source orbit.']}
    for n in sorted(grouped):
        subset=[(k,v) for k,v in allrows.items() if k[0]==n]
        d={'parent_pairs':len({k[1] for k,v in subset}),'replicate_sessions_per_arm':len(subset),
           'known_best_E':known[n],'arms':{},'paired':{}}
        for arm,name in NAMES.items():
            r=[v[arm] for k,v in subset]
            t=sum(float(x['elapsedMs']) for x in r)/1000
            n10=sum(int(x['new10']) for x in r)
            d['arms'][name]={'mean_session_best_postrepair_E':float(np.mean([int(x['bestE']) for x in r])),
            'mean_all_repaired_child_E':float(np.mean([float(x['meanRepairedE']) for x in r])),
            'best_observed_E':min(int(x['bestE']) for x in r),
            'novel5_events':sum(int(x['new5']) for x in r),
            'novel10_events':n10,
            'novel15_events':sum(int(x['new15']) for x in r),
            'novel20_events':sum(int(x['new20']) for x in r),
            'novel10_events_per_CPU_second':n10/t,
            'repaired_offspring':sum(int(x['generations']) for x in r),
            'average_model_ms':float(np.mean([float(x['modelMs']) for x in r])),
            'fraction_session_best_in_parent_registry':float(np.mean([x['bestCanonical'] in registry[n] for x in r])),
            'average_repair_flip_distance_of_novel_children':float(np.mean([z['repair_flip_distance'] for z in repair_stats[(n,arm)]])) if repair_stats[(n,arm)] else None}
        for arm,label in [(1,'random_orientation_vs_minHD'),(2,'mean_rawE_planned_vs_minHD'),(3,'prequench_planned_vs_minHD'),(4,'maxHD_vs_minHD'),(5,'best_rawE_planned_vs_minHD')]:
            deltas=[int(v[0]['bestE'])-int(v[arm]['bestE']) for k,v in subset]
            counts_novel=[int(v[arm]['new10'])-int(v[0]['new10']) for k,v in subset]
            perpair=collections.defaultdict(list)
            for (k,v),val in zip(subset,deltas):perpair[k[1]].append(val)
            d['paired'][label]={'mean_bestE_advantage':float(np.mean(deltas)),
               'mean_novel10_event_advantage':float(np.mean(counts_novel)),
               'bootstrap_CI95_by_pair_not_independent_lineages':bootstrap_by_pair(
                 [float(np.mean(v)) for v in perpair.values()],seed=20261105+arm*n),
               'session_win_tie_loss':[sum(x>0 for x in deltas),sum(x==0 for x in deltas),sum(x<0 for x in deltas)]}
        report['by_length'][str(n)]=d
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print('VERIFIED',len(rr),'complete source-parented fixed-time symmetry planning sessions,',
        len(cc),'independently scored novelty certificates')
    for n,z in report['by_length'].items():
        print('N',n,'pairs',z['parent_pairs'],'novel10',[z['arms'][name]['novel10_events'] for name in NAMES.values()],
              'mean E gains',[round(p['mean_bestE_advantage'],2) for p in z['paired'].values()])
if __name__=='__main__':main()
