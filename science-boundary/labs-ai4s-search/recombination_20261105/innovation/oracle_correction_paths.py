#!/usr/bin/env python3
"""Exact *oracle* study of consensus repair between distinct known LABS optima.

No deployment / learning: C is a withheld known target used ONLY to diagnose
whether A/B allele inheritance can be repaired to C by its compulsory edits.
All eight LABS symmetry orientations of A/B/C are enumerated. The representative
minimizes (compulsory consensus edits, precursor energy, canonical words).
For this frozen minimal-consensus witness, all 2^k intermediate correction
subsets are enumerated exactly (k<=9 for these N46/47/50 inputs).
Dynamic programming gives the globally minimum number/size of uphill steps,
monotone path counts, and the greedy-order counterfactual.
"""
import argparse,csv,collections,itertools,json,math,random,pathlib

def variants(s):
    rev=s[::-1]
    def flip(t):return ''.join('1' if c=='0' else '0' for c in t)
    def alt(t):return ''.join(flip(c) if i%2 else c for i,c in enumerate(t))
    return sorted({y for x in (s,rev) for v in (x,alt(x)) for y in (v,flip(v))})

def energy(s):
    a=[2*int(c)-1 for c in s];n=len(a)
    return sum(sum(a[i]*a[i+k] for i in range(n-k))**2 for k in range(1,n))

def recalc_oracle(a,b,c):
    n=len(a)
    assert len(b)==len(c)==n
    consensus=[i for i in range(n) if a[i]==b[i]]
    forced=[i for i in consensus if a[i]!=c[i]]
    donor_count=sum(a[i]!=b[i] and c[i]==b[i] for i in range(n))
    d=sum(a[i]!=b[i] for i in range(n))
    precursor=''.join(c[i] if a[i]!=b[i] else a[i] for i in range(n))
    assert sum(precursor[i]!=c[i] for i in range(n))==len(forced)
    assert donor_count+sum(a[i]!=b[i] and c[i]==a[i] for i in range(n))==d
    return len(forced),energy(precursor),precursor,forced,donor_count,d

def choose(a,b,c):
    best=None
    for x in variants(a):
        for y in variants(b):
            for z in variants(c):
                k,e,p,forced,donor,d=recalc_oracle(x,y,z)
                # Choose a single fully declared representative for each known
                # target triple; the result is a targeted structural calibration.
                t=(k,e,abs(2*donor-d),x,y,z)
                if best is None or t<best[0]:
                    best=(t,(x,y,z,k,e,p,forced,donor,d))
    return best[1]

def path_stats(p,c,forced,seed):
    k=len(forced);assert 0<k<=12
    energies=[]
    for mask in range(1<<k):
        z=list(p)
        for j,i in enumerate(forced):
            if mask>>j&1:z[i]=c[i]
        energies.append(energy(''.join(z)))
    full=(1<<k)-1
    assert energies[0]==energy(p) and energies[-1]==energy(c)
    dp_up=[10**12]*(full+1);dp_up[0]=0
    dp_peak=[10**12]*(full+1);dp_peak[0]=energies[0]
    count_mono=[0]*(full+1);count_mono[0]=1
    for mask in range(1,full+1):
        for j in range(k):
            if not (mask>>j)&1:continue
            prev=mask^(1<<j);delta=energies[mask]-energies[prev]
            dp_up[mask]=min(dp_up[mask],dp_up[prev]+max(0,delta))
            dp_peak[mask]=min(dp_peak[mask],max(dp_peak[prev],energies[mask]))
            if delta<=0:count_mono[mask]+=count_mono[prev]
    order=[];mask=0;greedy_up=0;greedy_max=energies[0];greedy_increase=0
    while mask!=full:
        opts=[(energies[mask |(1<<j)],j) for j in range(k) if not(mask>>j)&1]
        v,j=min(opts)
        delta=v-energies[mask]
        greedy_up+=max(0,delta);greedy_increase+=(delta>0)
        greedy_max=max(greedy_max,v)
        mask|=1<<j;order.append(forced[j])
    rng=random.Random(seed)
    rand_up=[]
    for rep in range(100):
        indexes=list(range(k));rng.shuffle(indexes)
        mask=0;up=0
        for j in indexes:
            nxt=mask|(1<<j)
            up+=max(0,energies[nxt]-energies[mask]);mask=nxt
        rand_up.append(up)
    singles=[energies[1<<i]-energies[0] for i in range(k)]
    return {'k':k,'precursor_E':energies[0],'target_E':energies[-1],
       'E_ratio_precursor_over_target':energies[0]/energies[-1],
       'min_uphill_total':dp_up[-1],'min_extra_peak_over_precursor':dp_peak[-1]-energies[0],
       'monotone_order_count':count_mono[-1],'possible_correction_orders':math.factorial(k),
       'all_initial_single_moves_uphill':all(z>0 for z in singles),
       'best_single_delta':min(singles),'worst_single_delta':max(singles),
       'greedy_uphill_total':greedy_up,'greedy_ascending_moves':greedy_increase,
       'greedy_peak_above_precursor':greedy_max-energies[0],
       'greedy_order':order,'random_order_mean_uphill':sum(rand_up)/len(rand_up),
       'superadditive_correction_delta':energies[-1]-energies[0]-sum(singles),
       'raw_E_by_all_correction_subsets':energies}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--parents',type=pathlib.Path,required=True)
    p.add_argument('--out',type=pathlib.Path,required=True)
    a=p.parse_args()
    with a.parents.open() as f:inputs=list(csv.DictReader(f,delimiter='\t'))
    group=collections.defaultdict(list)
    for z in inputs:
        if int(z['n']) not in (46,47,50):continue
        assert energy(z['bits'])==int(z['E'])
        assert variants(z['bits'])[0]==z['canonical']
        group[int(z['n'])].append(z)
    result={'scope':'known-target diagnostic oracle only, not deployable search or neural generalization',
      'source':'20 certified archival optimum orbits; no synthetic parents',
      'witnesses':[],'by_length':{}}
    for n,pool in sorted(group.items()):
        for i,j in itertools.combinations(range(len(pool)),2):
            for k,T in enumerate(pool):
                if k==i or k==j:continue
                A,B=pool[i],pool[j]
                x,y,z,m,pre,p,forced,donor,d=choose(A['bits'],B['bits'],T['bits'])
                stats=path_stats(p,z,forced,seed=20261105+n*101+i*23+j*41+k*127)
                row={'N':n,'A':A['id'],'B':B['id'],'target':T['id'],
                     'A_E':int(A['E']),'B_E':int(B['E']),'targetE':int(T['E']),
                     'minimum_forced_consensus_edits_over_all_symmetries':m,
                     'chosen_A_orientation':x,'chosen_B_orientation':y,'chosen_target_orientation':z,
                     'mixed_precursor':p,'consensus_edit_positions':forced,
                     'donor_bits_inherited':donor,'total_disagreement_bits':d,**stats}
                assert row['k']==m
                result['witnesses'].append(row)
        witness=[r for r in result['witnesses'] if r['N']==n]
        assert len(witness)==({46:3,47:60,50:3}[n])
        result['by_length'][str(n)]={'triples':len(witness),
          'min_forced':min(r['k'] for r in witness),'median_forced':sorted(r['k'] for r in witness)[len(witness)//2],
          'max_forced':max(r['k'] for r in witness),
          'need_any_uphill_step':sum(r['min_uphill_total']>0 for r in witness),
          'need_new_peak_above_precursor':sum(r['min_extra_peak_over_precursor']>0 for r in witness),
          'no_monotone_path':sum(r['monotone_order_count']==0 for r in witness),
          'all_single_corrections_initially_uphill':sum(r['all_initial_single_moves_uphill'] for r in witness),
          'mean_precursor_excess_E':sum(r['precursor_E']-r['targetE'] for r in witness)/len(witness),
          'mean_greedy_uphill':sum(r['greedy_uphill_total'] for r in witness)/len(witness),
          'mean_optimal_uphill':sum(r['min_uphill_total'] for r in witness)/len(witness),
          'mean_random_order_uphill':sum(r['random_order_mean_uphill'] for r in witness)/len(witness),
          'mean_interaction_synergy':sum(r['superadditive_correction_delta'] for r in witness)/len(witness)}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['by_length'],indent=2),flush=True)
    assert len(result['witnesses'])==66
    print('PASS 66 triplets, all 8^3 orientations, all 2^k correction mask energies and exact minimax/uphill DP',flush=True)
if __name__=='__main__':main()
