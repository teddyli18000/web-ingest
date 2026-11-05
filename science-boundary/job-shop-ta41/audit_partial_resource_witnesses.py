#!/usr/bin/env python3
"""Independent hidden-oracle soundness audit of precompletion resource witnesses.

The predictor, initial critical-path cuts and ranking are computed first
using only <case>/start.txt and its incumbent target Cmax-1. Only AFTER
that phase does this verifier read ScheduleOpt's archived complete
machine orders. Each precompletion witness has the sound implication:
any better feasible complete schedule must reverse >=1 retained adjacent
arc in the union of fixed-resource support paths.

Check that implication for EACH audited witness against an independent
already-verifiable published full schedule (not used as predictor input).
Also report top-K resource-arc precision vs the oracle's ACTUAL pair
reversals. This is an objective witness-specific diagnostic, NOT a
claim that a particular arc is globally necessary for improvement.
"""
import argparse,json,random
from pathlib import Path
from search import evaluate
from structural_cut import cut_analysis
from partial_resource_pair_repair import (parse_case,partial_witnesses,
                                          energetic_conflicts)

TOPIC=Path(__file__).resolve().parent

def link_support(orders,pos,dur,L,removed,obs):
    retained_mask=((1<<580)-1)
    for idx in removed:retained_mask &= ~(1<<idx)
    def single(op):
        return obs['prefix'][op]|obs['suffix'][op]
    pairs=[]
    for m,seq in enumerate(orders):
        ops=[j*20+pos[j][m] for j in seq]
        for i,u in enumerate(ops):
            for v in ops[i+1:]:
                ufirst=obs['head'][u]+dur[u]+obs['tail'][v]
                vfirst=obs['head'][v]+dur[v]+obs['tail'][u]
                if ufirst>L and vfirst>L:
                    mask=(single(u)|single(v)) & retained_mask
                    pairs.append((m,u,v,mask,ufirst,vfirst))
    energy=energetic_conflicts(orders,pos,dur,removed,L,obs)
    energetic=[]
    for w in energy['witnesses']:
        m,a,b=w['machine'],w['a'],w['b']
        terms=[]
        for j in orders[m]:
            op=j*20+pos[j][m];p=dur[op]
            es=obs['head'][op];ls=L-obs['tail'][op]
            compulsory=min(max(0,min(es+p,b)-max(es,a)),
                            max(0,min(ls+p,b)-max(ls,a)))
            if compulsory:terms.append((op,compulsory))
        assert sum(q for _,q in terms)-(b-a)==w['excess'],w
        support=0
        for op,_ in terms:support|=single(op)
        energetic.append((w,support & retained_mask))
    return pairs,energetic,energy

def prepare(source):
    orders,pos,dur,incumbent=parse_case(str(source))
    target=incumbent-1
    rng=random.Random(709)
    removed=set()
    while True:
        obs=partial_witnesses(orders,pos,dur,removed,target)
        if obs['lb']<=target:break
        cut=cut_analysis(orders,pos,dur,removed,rng,weighted=False)
        nxt=set(cut['cut_arcs'])-removed
        assert nxt
        removed.update(nxt)
    pairs,energ,metric=link_support(orders,pos,dur,target,removed,obs)
    crit={}
    for i,(m,k,u,v) in enumerate(obs['arcs']):
        crit[i]=-abs(target-(obs['head'][u]+dur[u]+obs['tail'][v]))
    predicted={m:sorted((j for j in range(580) if j not in removed),
            key=lambda j:-scores.get(j,0))[:20]
            for m,scores in [('bidirectional',obs['pressure']),
                              ('energetic',metric['pressure']),
                              ('static',crit)]}
    return dict(orders=orders,pos=pos,dur=dur,target=target,
                removed=removed,pairs=pairs,energy=energ,
                metrics=metric,predicted=predicted,
                precompletion_lb=obs['lb'],score=incumbent)

def main(args):
    arr=json.loads((args.reference_root/'jobshop'/'solutions'/'solutions.json').read_text())
    entries={x['instance']:x for x in arr}
    files=sorted((TOPIC/'positive-n7-elite-data').glob('ta*js-n7elite*/start.txt'))
    assert len(files)==12
    records=[]
    for start_file in files:
        # Isolation of oracle from prediction: first compute all witnesses
        # and rankings, then open the known published target for auditing.
        frozen=prepare(start_file)
        label=start_file.parent.name
        key=label.split('-')[0]
        archive=entries[key]
        full=[[op//20 for op in row] for row in archive['solution']]
        pos,dur,base=frozen['pos'],frozen['dur'],frozen['orders']
        known=evaluate(full,pos,dur)
        assert known==archive['makespan'] and known<=frozen['target']
        reversals=0
        for idx,(m,seq) in enumerate(enumerate(base)):
            pass
        for m in range(20):
            oracle_positions={job:i for i,job in enumerate(full[m])}
            for k in range(29):
                if oracle_positions[base[m][k]]>oracle_positions[base[m][k+1]]:
                    reversals|=1<<(m*29+k)
        for name,items in [('pair',frozen['pairs']),
                           ('energy',frozen['energy'])]:
            for x in items:
                mask=x[3] if name=='pair' else x[1]
                assert mask,(label,name,'no resource support')
                assert mask & reversals,(label,name,'oracle contradicts support',x)
        stats={}
        for strategy,top in frozen['predicted'].items():
            overlap=sum(bool(reversals&(1<<i)) for i in top)
            stats[strategy+'_top20_oracle_hits']=overlap
        record=dict(case=label,incumbent=frozen['score'],
            reference=known,target=frozen['target'],
            common_precedence_longest_path=frozen['precompletion_lb'],
            initial_retracted_arcs=len(frozen['removed']),
            known_oracle_reversed_baseline_adjacent_arcs=reversals.bit_count(),
            mandatory_double_forbidden_pairs=len(frozen['pairs']),
            certified_energetic_overload_witnesses=len(frozen['energy']),
            all_precompletion_witnesses_hit_by_published_improved_oracle=True,
            **stats)
        records.append(record)
        print('AUDIT',json.dumps(record),flush=True)
    summary=dict(instance_count=len(records),
        pair_witnesses=sum(x['mandatory_double_forbidden_pairs'] for x in records),
        energy_witnesses=sum(x['certified_energetic_overload_witnesses'] for x in records),
        all_witnesses_independently_oracle_consistent=True,
        rank_top20_totals={name:sum(x[name+'_top20_oracle_hits'] for x in records)
                           for name in ['bidirectional','energetic','static']})
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(dict(summary=summary,cases=records,
         caveat='No algorithm sees the oracle while ranking. Overlap with ONE witness is neither necessary nor sufficient for finding ANY improving solution.'),
         indent=2)+'\n')
    print('RESULT',json.dumps(summary),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--reference-root',type=Path,required=True)
    p.add_argument('--out',type=Path,default=TOPIC/'results'/'partial-resource-oracle-audit.json')
    main(p.parse_args())
