#!/usr/bin/env python3
"""Symmetry-robust correction-path audit for all 66 known-optimum LABS triples.

Earlier oracle selected ONE orientation by min(# consensus edits, precursor E).
This repeats the path DP for ALL orientations that achieve global minimum
consensus edits. A may be fixed in one orientation because applying the SAME
eightfold LABS symmetry to all three strings preserves energy and equality
site-wise; hence 8×8(B,C) relative orientations suffice instead of 8^3.
It separately measures whether permitting ONE extra required consensus edit
through a different representative resolves a forced-uphill path.

Independent score algorithm: bitset XOR/popcount of shifted bitstrings.
For s_i in +/-1:
 C_k(s) = (n-k)-2 popcount[(b xor (b>>k)) & ((1<<(n-k))-1)].
"""
import argparse,collections,csv,json,pathlib
from itertools import combinations
INF=10**15
def variants(s):
    def flip(x):return ''.join('1' if c=='0' else '0' for c in x)
    def alt(x):return ''.join(c if i%2==0 else flip(c) for i,c in enumerate(x))
    return sorted({y for x in (s,s[::-1]) for v in (x,alt(x)) for y in (v,flip(v))})
def bitmask(s):
    return int(s[::-1],2)
def bitenergy(bits,n):
    return sum(((n-k)-2*((bits^(bits>>k)) & ((1<<(n-k))-1)).bit_count())**2
               for k in range(1,n))
def exact_reference(s):
    x=[1 if c=='1' else -1 for c in s]
    return sum(sum(x[i]*x[i+k] for i in range(len(x)-k))**2 for k in range(1,len(x)))
def consensus(a,b,c):
    q=[i for i,(x,y,z) in enumerate(zip(a,b,c)) if x==y and x!=z]
    p=''.join(z if x!=y else x for x,y,z in zip(a,b,c))
    assert sum(x!=y for x,y in zip(p,c))==len(q)
    return q,p
def stats(p,c,edits):
    n=len(p);k=len(edits);assert 0<=k<=12
    base=bitmask(p);target=bitmask(c)
    full=(1<<k)-1
    flip=[1<<e for e in edits]
    vals=[0]*(full+1)
    bits=[0]*(full+1)
    bits[0]=base
    vals[0]=bitenergy(base,n)
    for mask in range(1,full+1):
        b=(mask&-mask).bit_length()-1
        bits[mask]=bits[mask^(1<<b)]^flip[b]
        vals[mask]=bitenergy(bits[mask],n)
    assert bits[-1]==target
    assert vals[-1]==bitenergy(target,n)
    dp=[INF]*(full+1);dp[0]=0
    monotone=[0]*(full+1);monotone[0]=1
    for mask in range(1,full+1):
        choices=mask
        while choices:
            b=(choices&-choices).bit_length()-1
            before=mask^(1<<b)
            cost=vals[mask]-vals[before]
            dp[mask]=min(dp[mask],dp[before]+max(cost,0))
            if cost<=0:monotone[mask]+=monotone[before]
            choices&=choices-1
    return {'uphill':dp[-1], 'monotone':monotone[-1],
            'initial_E':vals[0], 'target_E':vals[-1]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--parents',type=pathlib.Path,required=True)
    p.add_argument('--previous',type=pathlib.Path,required=True)
    p.add_argument('--out',type=pathlib.Path,required=True)
    a=p.parse_args()
    with a.parents.open() as f:parents=list(csv.DictReader(f,delimiter='\t'))
    previous=json.loads(a.previous.read_text())['witnesses']
    previously={(v['N'],v['A'],v['B'],v['target']):v for v in previous}
    group=collections.defaultdict(list)
    for z in parents:
        n=int(z['n'])
        if n not in (46,47,50):continue
        assert bitenergy(bitmask(z['bits']),n)==int(z['E'])==exact_reference(z['bits'])
        group[n].append(z)
    answer={'scope':'complete symmetry-equivalent min-consensus-edit known-target path study; oracle only',
       'independent_scorer':'integer shift-xor-bitcount direct LABS correlations, checked against independent nested loops for all 20 parents',
       'by_length':{},'triples':[]}
    for n,pool in sorted(group.items()):
        for i,j in combinations(range(len(pool)),2):
            for t,T in enumerate(pool):
                if t in (i,j):continue
                A,B=pool[i],pool[j]
                key=(n,A['id'],B['id'],T['id'])
                old=previously[key]
                # Global eightfold group action on (A,B,C) lets us fix A.
                aa=A['bits']
                orientations=[]
                for bb in variants(B['bits']):
                    for cc in variants(T['bits']):
                        edits,precursor=consensus(aa,bb,cc)
                        k=len(edits)
                        if k<=old['k']+1:
                            details=stats(precursor,cc,edits)
                            orientations.append({'k':k,'B':bb,'C':cc,
                               'precursor':precursor,'edits':edits,**details})
                minK=min(x['k'] for x in orientations)
                assert minK==old['k'],(key,minK,old['k'])
                strict=[z for z in orientations if z['k']==minK]
                extra=[z for z in orientations if z['k']==minK+1]
                def bestgroup(x):
                    if not x:return None
                    return min(x,key=lambda z:(z['uphill'],z['initial_E'],z['B'],z['C']))
                chosen=bestgroup(strict)
                extraBest=bestgroup(extra)
                ans={'N':n,'A':A['id'],'B':B['id'],'target':T['id'],
                     'minimum_consensus_edits':minK,
                     'minK_representative_orientations':len(strict),
                     'minK_orientations_with_monotone_path':sum(z['monotone']>0 for z in strict),
                     'minimum_uphill_across_minK':chosen['uphill'],
                     'previous_selected_uphill':old['min_uphill_total'],
                     'previous_selected_monotone':old['monotone_order_count']>0,
                     'minK_optimal_witness':chosen,
                     'kplus1_representative_orientations':len(extra),
                     'minimum_uphill_across_kplus1':extraBest['uphill'] if extraBest else None,
                     'kplus1_has_monotone_path':bool(extraBest and any(z['monotone']>0 for z in extra)),
                     'kplus1_optimal_witness':extraBest}
                assert ans['minimum_uphill_across_minK']<=ans['previous_selected_uphill']
                answer['triples'].append(ans)
        vals=[x for x in answer['triples'] if x['N']==n]
        answer['by_length'][str(n)]={'triples':len(vals),
          'all_minK_orientations_require_uphill':sum(x['minK_orientations_with_monotone_path']==0 for x in vals),
          'some_minK_orientations_allow_monotone':sum(x['minK_orientations_with_monotone_path']>0 for x in vals),
          'previous_single_orientation_uphill':sum(x['previous_selected_uphill']>0 for x in vals),
          'strictly_positive_best_uphill':sum(x['minimum_uphill_across_minK']>0 for x in vals),
          'positive_uphill_resolved_with_plus_one_extra_consensus_edit':sum(
             x['minimum_uphill_across_minK']>0 and x['kplus1_has_monotone_path'] for x in vals),
          'sample_minK_orientations':sum(x['minK_representative_orientations'] for x in vals),
          'sample_plus1_orientations':sum(x['kplus1_representative_orientations'] for x in vals)}
    assert len(answer['triples'])==66
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(answer,indent=2)+'\n')
    print(json.dumps(answer['by_length'],indent=2),flush=True)
    print('PASS 66 triples with ALL relative symmetry orientations and exact bitset min-uphill DP',flush=True)
if __name__=='__main__':main()
