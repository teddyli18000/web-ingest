#!/usr/bin/env python3
"""EXACT 2^15 lattice test for coordination among 15 simultaneous swaps.

A score-2006 neutral schedule was independently verified by Few Shots at
exact Kendall distance 15, with one adjacent swap on each of 15 machines.
Construct ALL 2^15 combinations of those precise swaps and evaluate every
intermediate machine-oriented DAG. Dynamic programming on the entire
hypercube computes the *exact minimum possible maximum makespan* on a
monotone sequence that accumulates those 15 swaps in some order.

If min peak == 2006, these changes do NOT demand any uphill step: the
large changed-machine count is a metric artifact. If min peak >2006,
this particular move cohort needs transient degradation in every
monotone ordering, even though both endpoints score 2006.

No inference is made about paths involving other operations, or
the unknown <=2005 target solution.
"""
import argparse,json,time
from collections import Counter
from pathlib import Path
from search import obtain,setup,evaluate

ROOT=Path(__file__).resolve().parent

def main(a):
    rows,runs,base=obtain()
    pos,dur=setup(rows,runs)
    assert evaluate(base,pos,dur)==2006
    folder=ROOT/'results'/'synchronous-single-2006'
    cert=json.loads((folder/'certificate.json').read_text())['machines']
    verdict=json.loads((folder/'upstream-verdict.json').read_text())
    assert verdict['valid'] and int(verdict['score'])==2006
    assert evaluate(cert,pos,dur)==2006
    flips=[]
    for m in range(20):
        current=base[m];dest=cert[m]
        for k in range(29):
            if current[k]!=dest[k]:
                if k+1<30 and current[k]==dest[k+1] and current[k+1]==dest[k]:
                    flips.append((m,k))
                    break
                else:
                    raise ValueError(('unexpected difference',m,k))
    assert len(flips)==15 and len(set(m for m,k in flips))==15
    trial=[x[:] for x in base]
    for m,k in flips:trial[m][k],trial[m][k+1]=trial[m][k+1],trial[m][k]
    assert trial==cert
    size=1<<len(flips)
    scores=[None]*size
    histogram=Counter()
    started=time.monotonic()
    for mask in range(size):
        orders=[x[:] for x in base]
        for i,(m,k) in enumerate(flips):
            if mask&(1<<i):
                orders[m][k],orders[m][k+1]=orders[m][k+1],orders[m][k]
        score=evaluate(orders,pos,dur)
        scores[mask]=score
        histogram[score if score is not None else 'cyclic']+=1
        if mask%4096==0:print('ENUMERATED',mask,size,flush=True)
    assert scores[0]==scores[-1]==2006
    high=10**8
    dp=[high]*size
    predecessor=[-1]*size
    dp[0]=scores[0]
    for mask in range(1,size):
        if scores[mask] is None:continue
        c=mask
        while c:
            bit=c&-c
            parent=mask^bit
            candidate=max(dp[parent],scores[mask])
            if candidate<dp[mask]:
                dp[mask]=candidate
                predecessor[mask]=parent
            c-=bit
    assert dp[-1]<high
    seq=[];at=size-1
    while at:
        prev=predecessor[at]
        assert prev>=0
        bit=at^prev
        idx=bit.bit_length()-1
        seq.append(dict(machine=flips[idx][0],position=flips[idx][1],
                        remaining_changes=at.bit_count(),intermediate_makespan=scores[at]))
        at=prev
    seq.reverse()
    assert len(seq)==15
    # Exact monotone 2006-level reachability through all 32768 states.
    reachable=[False]*size
    reach_parent=[-1]*size
    reachable[0]=True
    for mask in range(1,size):
        if scores[mask] is None or scores[mask]>2006:continue
        cur=mask
        while cur:
            bit=cur&-cur
            pred=mask^bit
            if reachable[pred]:
                reachable[mask]=True
                reach_parent[mask]=pred
                break
            cur-=bit
    assert reachable[-1] == (dp[-1]<=2006)
    minimal_prerequisites=[]
    for i,(m,k) in enumerate(flips):
        bit=1<<i
        possibilities=[mask for mask in range(size)
                       if not (mask&bit) and reachable[mask]
                       and scores[mask|bit] is not None
                       and scores[mask|bit]<=2006]
        assert possibilities
        prereq=min(possibilities,key=lambda mask:(mask.bit_count(),mask))
        history=[];cur=prereq
        while cur:
            old=reach_parent[cur]
            assert old>=0
            move=(cur^old).bit_length()-1
            history.append(move)
            cur=old
        history.reverse()
        assert len(history)==prereq.bit_count()
        minimal_prerequisites.append({
          'machine':m,'position':k,
          'individual_makespan':scores[bit],
          'minimal_other_swaps_before_this_can_be_applied_without_exceeding_2006':prereq.bit_count(),
          'one_valid_preparation_sequence':[list(flips[j]) for j in history],
          'makespan_after_preparation':scores[prereq],
          'makespan_after_applying_move':scores[prereq|bit],
        })
    exact=dict(
        instance='ta41',baseline_score=2006,other_endpoint_score=2006,
        both_endpoints_independently_verified=True,
        fixed_simultaneous_adjacent_swaps=[list(x) for x in flips],
        total_intermediate_states_exhaustively_enumerated=size,
        count_states_score_at_most_2006=sum(v for s,v in histogram.items() if isinstance(s,int) and s<=2006),
        cyclic_intermediate_states=histogram.get('cyclic',0),
        minimum_peak_makespan_on_any_monotone_ordering=dp[-1],
        minimum_required_monotone_uphill_degradation=dp[-1]-2006,
        individual_one_swap_makespans=[scores[1<<i] for i in range(15)],
        exact_neutral_reachable_state_count=sum(reachable),
        minimal_coordination_prerequisites=minimal_prerequisites,
        scores_by_size={str(k):dict(Counter(scores[mask] for mask in range(size) if mask.bit_count()==k))
                        for k in range(16)},
        optimal_minimax_move_sequence=seq,
        elapsed_seconds=round(time.monotonic()-started,3),
        scope='EXACT for the 2^15 subsets of these specific 15 swaps only; not a bound on 2005 distance or arbitrary temporary moves.')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(exact,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in exact.items() if k not in ('scores_by_size','optimal_minimax_move_sequence','minimal_coordination_prerequisites')},default=str),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=ROOT/'results'/'exact-15-swap-coordination-lattice.json')
    main(p.parse_args())
