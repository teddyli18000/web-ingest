#!/usr/bin/env python3
"""Generate genuinely multi-machine blind positive controls, not one-swap toys."""
import argparse,hashlib,json,random
from pathlib import Path
from create_hidden_positive_cases import SELECTED,load_case
from search import evaluate

def create(oracle,score,pos,duration,seed,steps,gap):
    rng=random.Random(seed)
    order=[v[:] for v in oracle]
    used=set();machines=set();history=[]
    for step in range(steps):
        suggestions=[]
        for attempt in range(320):
            m=rng.randrange(20);i=rng.randrange(29)
            if (m,i) in used:continue
            order[m][i],order[m][i+1]=order[m][i+1],order[m][i]
            value=evaluate(order,pos,duration)
            order[m][i],order[m][i+1]=order[m][i+1],order[m][i]
            if value is None or value<score or value>score+300:continue
            ideal=score+(gap+35 if step>=4 else gap)
            cost=abs(value-ideal)+(0 if m not in machines else 30)+rng.random()*20
            suggestions.append((cost,m,i,value))
        assert suggestions,(seed,steps,step)
        _,m,i,value=min(suggestions)
        order[m][i],order[m][i+1]=order[m][i+1],order[m][i]
        used.add((m,i));machines.add(m)
        history.append([m,i,value])
    assert len(machines)>=9,(seed,len(machines))
    assert evaluate(order,pos,duration)>=score+gap,(seed,steps,evaluate(order,pos,duration)-score)
    return order,evaluate(order,pos,duration),history,len(machines)

def main(a):
    entries=json.loads((a.reference_root/'jobshop'/'solutions'/'solutions.json').read_text())
    manifest_path=a.out/'manifest.json'
    manifest=json.loads(manifest_path.read_text())
    assert len(manifest['cases'])==12
    for name in SELECTED:
        route,duration,oracle,score,pos,dur=load_case(a.reference_root,name,entries)
        oracle_hash=hashlib.sha256(json.dumps(oracle,separators=(',',':')).encode()).hexdigest()
        for moves,gap in ((16,12),(32,35)):
            seed=200000+int(name[2:4])*101+moves
            initial,best,swaps,machine_count=create(oracle,score,pos,dur,seed,moves,gap)
            key=f'{name}-multi{moves}'
            folder=a.out/key;folder.mkdir(parents=True,exist_ok=True)
            with (folder/'start.txt').open('w') as out:
                out.write('30 20\n')
                for j in range(30):
                    out.write(' '.join(f'{route[j][k]} {duration[j][k]}' for k in range(20))+'\n')
                for m in range(20):
                    out.write(' '.join(map(str,initial[m]))+'\n')
            manifest['cases'].append(dict(case=key,instance=name,
                difficulty_label=f'multi{moves}',initial_makespan=best,
                verified_hidden_oracle_makespan=score,known_positive_gap=best-score,
                source_oracle_hash=oracle_hash,degradation_swaps=len(swaps),
                changed_machine_count=machine_count,
                source='ScheduleOpt/benchmarks:jobshop/solutions/solutions.json',
                proof='Both endpoints independently DAG-verified. No original oracle orders in runtime inputs.'))
            print('MULTI',key,'initial',best,'oracle',score,'gap',best-score,
                 'machines',machine_count,flush=True)
    assert len(manifest['cases'])==24
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print('RESULT 24 verified positive fixtures, 12 multi-move',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--reference-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
