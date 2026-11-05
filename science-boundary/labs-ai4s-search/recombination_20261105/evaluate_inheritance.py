#!/usr/bin/env python3
"""External verifier for forced two-parent inheritance and repair outcomes."""
import argparse,csv,collections,json,pathlib
import numpy as np
NAMES={0:'fresh_uniform_half_mix',1:'stationary_uniform_half_mask_walk',
       2:'strict_true_E_half_mask_swap',3:'signed_parent_spectrum_corridor_swap',
       4:'descent_aware_half_mask_swap_novelty_constraint'}
def read(p):
    with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def E(b):
    z=[1 if c=='1' else -1 for c in b];n=len(b)
    return sum(sum(z[i]*z[i+k] for i in range(n-k))**2 for k in range(1,n))
def orb(s):
    neg=lambda x:''.join('0' if q=='1' else '1' for q in x)
    alt=lambda x:''.join(q if i%2==0 else ('0' if q=='1' else '1') for i,q in enumerate(x))
    return sorted({t for x in (s,s[::-1]) for y in (x,alt(x)) for t in (y,neg(y))})
def hd(a,b):return sum(x!=y for x,y in zip(a,b))
def align(a,b):return min(orb(b),key=lambda x:(hd(a,x),x))
def odist(a,b):return min(hd(a,x) for x in orb(b))
def bootstrap(x,seed):
    rng=np.random.default_rng(seed);x=np.asarray(x,dtype=float)
    v=x[rng.integers(len(x),size=(3000,len(x)))].mean(axis=1)
    return list(np.quantile(v,[.025,.975]).astype(float))
def main():
    p=argparse.ArgumentParser();p.add_argument('--parents',type=pathlib.Path,required=True)
    p.add_argument('--rows',type=pathlib.Path,required=True)
    p.add_argument('--out',type=pathlib.Path,required=True)
    a=p.parse_args()
    source=read(a.parents)
    byId={z['id']:z for z in source};byN=collections.defaultdict(list)
    for z in source:byN[int(z['n'])].append(z)
    sourceorbits={n:{z['canonical'] for z in group} for n,group in byN.items()}
    rows=read(a.rows)
    pairs=collections.defaultdict(dict)
    for z in rows:
        n=int(z['N']);pair=z['pair'];A,B=[byId[x] for x in pair.split('-')]
        rep=int(z['rep']);mode=int(z['mode'])
        assert n==int(A['n'])==int(B['n'])
        bAlign=align(A['bits'],B['bits']);D=hd(A['bits'],bAlign);H=D//2
        assert int(z['D'])==D and int(z['H'])==H
        bm=z['mask_bits'];bq=z['quench_bits'];bf=z['final_bits']
        assert len(bm)==len(bq)==len(bf)==n
        assert E(bm)==int(z['mask_search_E'])
        assert E(bq)==int(z['quench_E'])
        assert E(bf)==int(z['final_E'])
        assert hd(bm,A['bits'])==H and hd(bm,bAlign)==D-H
        assert int(z['mask_distance_to_A'])==H and int(z['mask_distance_to_B'])==D-H
        assert int(z['final_min_orbit_distance'])==min(odist(bf,A['bits']),odist(bf,B['bits']))
        assert orb(bf)[0]==z['final_canonical']
        assert int(z['novel_strict'])==(int(z['final_E'])<min(int(A['E']),int(B['E'])))
        ref=min(int(y['E']) for y in byN[n])
        fresh=z['final_canonical'] not in sourceorbits[n]
        for pct in (5,10):
            expected=fresh and int(z['final_E'])<=int(ref*(1+pct/100)+1e-9)
            assert int(z[f'new_within{pct}'])==int(expected)
        assert int(z['repair_tabu_moves'])==64
        assert float(z['elapsed_ms'])>=.75*120
        assert float(z['search_ms'])+float(z['repair_ms'])<=float(z['elapsed_ms'])+1e-5
        key=(n,pair,rep)
        assert mode not in pairs[key];pairs[key][mode]=z
    assert len(rows)==625 and len(pairs)==125
    assert all(set(x)==set(NAMES) for x in pairs.values())
    report={'scope':'Forced ≥half-donor inheritance before local repair; exact generated, quenched and repaired certificates; 120ms end-to-end budget per pair/rep/arm',
     'source_orbits':len(source),'rows':len(rows),'paired_units':len(pairs),'lengths':{},'names':NAMES,
     'notes':['All source parents different eightfold LABS symmetry orbits; archived N<=60 lineage independence unknown',
       'Only initial candidate is forced to inherit from two parents; post-search repair can erase donor contribution',
       'A single generated best child per session, unlike preceding many-offspring 1000-unit experiment',
       'Schematic search kernels, NOT fully tuned existing GOMEA or modern strong GPU-MTS',
       'Novel near-optimal orbits and postrepair quality are primary; mask_search_E is a diagnostic']}
    for n in sorted(byN):
        keys=[key for key in pairs if key[0]==n]
        r={'pairs':len({z[1] for z in keys}),'replicates':len({z[2] for z in keys}),'sourceE':[int(x['E']) for x in byN[n]],'arms':{}}
        for mode,name in NAMES.items():
            vals=[pairs[k][mode] for k in keys]
            r['arms'][name]={
              'mean_mask_E':float(np.mean([int(v['mask_search_E']) for v in vals])),
              'mean_after_quench_E':float(np.mean([int(v['quench_E']) for v in vals])),
              'mean_after_common_tabu_E':float(np.mean([int(v['final_E']) for v in vals])),
              'best_final_E':int(min(int(v['final_E']) for v in vals)),
              'mean_final_nearest_parent_orbit_distance':float(np.mean([int(v['final_min_orbit_distance']) for v in vals])),
              'total_new5':sum(int(v['new_within5']) for v in vals),
              'total_new10':sum(int(v['new_within10']) for v in vals),
              'total_strict':sum(int(v['novel_strict']) for v in vals),
              'final_returns_to_existing_source_orbit':sum(v['final_canonical'] in sourceorbits[n] for v in vals),
              'mean_candidates_scored':float(np.mean([int(v['candidates_evaluated']) for v in vals])),
              'mean_quench_evaluations':float(np.mean([int(v['quench_evaluations']) for v in vals])),
              'mean_elapsed_ms':float(np.mean([float(v['elapsed_ms']) for v in vals]))}
        for candidate,base,label in ((2,1,'E_swap_vs_uniform_walk'),(3,2,'spectrum_vs_exact_E_swap'),(4,2,'basin_aware_vs_exact_E_swap')):
            diffs=[int(pairs[k][base]['final_E'])-int(pairs[k][candidate]['final_E']) for k in keys]
            r[label]={'mean_repaired_E_gain':float(np.mean(diffs)),
               'naive_pair_rep_CI95_not_source_independent':bootstrap(diffs,83291+n+candidate),
               'wins_ties_losses':[sum(x>0 for x in diffs),sum(x==0 for x in diffs),sum(x<0 for x in diffs)]}
        report['lengths'][str(n)]=r
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('PASS',len(rows),'independently scored forced biparent/repaired outcomes,',len(pairs),'paired units')
    for n,v in report['lengths'].items():
        print('N',n,'mask/quenched/repaired',
          {name:(round(z['mean_mask_E'],1),round(z['mean_after_common_tabu_E'],1),z['total_new10'])
           for name,z in v['arms'].items()},
          'spectrum vs true E',v['spectrum_vs_exact_E_swap'])
if __name__=='__main__':main()
