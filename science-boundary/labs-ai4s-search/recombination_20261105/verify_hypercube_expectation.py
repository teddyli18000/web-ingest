#!/usr/bin/env python3
"""Cross-check exhaustive LABS two-parent inheritance by an independent
closed-form expected energy identity, not a second copy of Gray enumeration.

For independent equiprobable inherited spins X_i in {A_i,B_i},
mu_i=E[X_i] is ±1 for parental agreement and 0 for disagreement.
C_k=sum_{i=0}^{N-k-1} X_i X_{i+k}. Then

E[C_k²] = (sum mu_i mu_{i+k})²
        + sum [1-(mu_i mu_{i+k})²]
        + 2 sum_{i=0}^{N-2k-1} mu_i mu_{i+2k}(1-mu_{i+k}²).

Covariance only remains between neighboring edges of the same lag chain.
This predicts the exact mean over all 2^D recombinant inherence masks
without enumerating any. We compare that prediction to the distinct C++
Gray enumerator and check the source symmetry alignment and coverage.
"""
import argparse,csv,json,pathlib,hashlib
from collections import Counter
def read(path):
    with path.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def entropy_mean_energy(a,b):
    n=len(a)
    assert len(b)==n
    mu=[(1 if x=='1' else -1) if x==y else 0 for x,y in zip(a,b)]
    total=0;deterministic=0;variance=0;overlap=0
    bylag=[]
    for k in range(1,n):
        edge=[mu[i]*mu[i+k] for i in range(n-k)]
        s=sum(edge)
        v=sum(1-x*x for x in edge)
        o=2*sum(mu[i]*mu[i+2*k]*(1-mu[i+k]*mu[i+k]) for i in range(n-2*k))
        z=s*s+v+o
        assert z>=0
        total+=z;deterministic+=s*s;variance+=v;overlap+=o
        bylag.append(z)
    return {'expected_E':total,'mean_term':deterministic,'edge_variance':variance,
            'lag_chain_covariance':overlap}
def orbit(s):
    neg=lambda t:''.join('1' if c=='0' else '0' for c in t)
    alt=lambda t:''.join(c if i%2==0 else ('1' if c=='0' else '0') for i,c in enumerate(t))
    return {z for q in (s,s[::-1]) for y in (q,alt(q)) for z in (y,neg(y))}
def main():
    p=argparse.ArgumentParser();p.add_argument('--parents',type=pathlib.Path,required=True)
    p.add_argument('--rows',type=pathlib.Path,required=True)
    p.add_argument('--out',type=pathlib.Path,required=True)
    a=p.parse_args()
    parent=read(a.parents);pmap={z['id']:z for z in parent}
    rs=read(a.rows)
    assert len(rs)==25, ('all short symmetry orientations',len(rs))
    assert sum(int(z['states']) for z in rs)==19689472
    assert all(int(z['maxD'])==21 and int(z['D'])<=21 for z in rs)
    groups=Counter();verified=[];pairs=set()
    for r in rs:
        n=int(r['N']);A,B=[pmap[s] for s in r['pair'].split('-')]
        assert n in (46,47,50) and int(A['n'])==n==int(B['n'])
        assert r['donor_bits'] in orbit(B['bits'])
        D=sum(x!=y for x,y in zip(A['bits'],r['donor_bits']))
        assert int(r['D'])==D
        assert int(r['states'])==1<<D
        assert int(r['mixed_states'])==(1<<D)-2
        val=entropy_mean_energy(A['bits'],r['donor_bits'])
        error=abs(float(r['mean_all_E'])-val['expected_E'])
        assert error<.00005,(n,r['pair'],r['frame'],error,val)
        assert val['expected_E']==val['mean_term']+val['edge_variance']+val['lag_chain_covariance']
        assert int(r['mixed_best_E'])>=int(r['refE'])
        assert int(r['balanced_best_E'])>=int(r['refE'])
        assert int(r['mixed_le5_count'])==int(r['mixed_le5_unique_orbits'])==0
        assert int(r['mixed_le10_count'])==int(r['mixed_le10_unique_orbits'])==0
        groups[n]+=1;pairs.add((n,r['pair']))
        verified.append(dict(N=n,pair=r['pair'],frame=int(r['frame']),D=D,states=int(r['states']),
             min_mixed_E=int(r['mixed_best_E']),mean_mixed_E=float(r['mean_all_E']),
             **val))
    out={'source_and_scope':'20 published symmetry-distinct parent orbits; checked every equivalent donor frame with <=21 differing positions for N46/47/50; some other frames and source pairs excluded',
      'alignment_frames_complete':len(verified),'source_pairs_covered':len(pairs),
      'states_independently_enumerated':sum(z['states'] for z in verified),
      'by_length_frame_count':dict(groups),
      'all_nonparent_mixtures_E_le_110pct_optimum':0,
      'analytic_formula':'E[Ck^2]=(sum mu_i mu_{i+k})^2+sum[1-(mu_i mu_{i+k})^2]+2sum mu_i mu_{i+2k}(1-mu_{i+k}^2)',
      'all_independent_closed_form_mean_checks_passed':True,
      'per_frame':verified,
      'caveats':['Only parent copying with independent coordinate inheritance; adding new corrective bits or full local-search trajectories escapes the hypercube',
      'Only aligned donor representations with D<=21 are exhaustive; frames with larger D are not excluded',
      'No new global optimum or full modern GOMEA comparison',
      'Uniform expectation is unconditional independent parent mixing, unlike constrained-half-donor crossover']}
    a.out.write_text(json.dumps(out,indent=2)+'\n')
    print('PASS',len(verified),'donor frames,',out['states_independently_enumerated'],
          'enumerated combinations, independent closed-form exact mean predictions')
    print('mean structure',[(z['N'],z['pair'],z['D'],z['min_mixed_E'],
                            z['mean_mixed_E'],z['edge_variance']) for z in verified[:7]])
if __name__=='__main__':main()
