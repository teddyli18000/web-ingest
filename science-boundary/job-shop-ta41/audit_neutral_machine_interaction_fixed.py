#!/usr/bin/env python3
"""Fixed-work factorial: two noncritical machine rewires, 4 start variants.

Every source starts at score 2044 and four machine-order combinations
have the same deadline and same critical-machine arc set (audited
separately). Native original N7 receives EXACTLY 800,000 iterations
under identical seed; CPU wall-time variation is measured, not used as
the search stopping rule. All 600 native operation records are replayed
in independent Python DAG scorer.

This asks if a purely neutral change in machine 12, machine 14, or
both changes future optimization access in a causal intervention.
"""
import argparse,json,tempfile,time
from pathlib import Path
from search import evaluate
from partial_resource_pair_repair import parse_case
from n7_fixed_native import original_n7_fixed

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'positive-n7-elite-data'/'ta46js-n7elite1701'/'start.txt'
CP=ROOT/'results'/'neutral-N7-ta46js-n7elite1701-random-seed4107'/'neutral-certificate.json'
def main(a):
    baseline,pos,dur,C=parse_case(str(BASE))
    neutral=json.loads(CP.read_text())['machines']
    assert C==2044 and evaluate(neutral,pos,dur)==C
    changed=[m for m in range(20) if baseline[m]!=neutral[m]]
    assert changed==[12,14]
    sources=BASE.read_text().splitlines()
    assert len(sources)==51
    a.out.mkdir(parents=True,exist_ok=True)
    outcomes={}
    with tempfile.TemporaryDirectory() as folder:
        folder=Path(folder)
        instance=folder/'instance.txt'
        instance.write_text('\n'.join(sources[:31])+'\n')
        for mask in range(4):
            orders=[row[:] for row in baseline]
            for i,m in enumerate(changed):
                if (mask>>i)&1:orders[m]=neutral[m][:]
            assert evaluate(orders,pos,dur)==C
            now=time.monotonic()
            native,result=original_n7_fixed(a.driver,instance,orders,
                pos,dur,a.seed,a.iterations,folder)
            assert native['best']<=C
            outcomes[str(mask)]={**native,'mask':mask,
                'perturbed_machines':[changed[i] for i in range(2) if (mask>>i)&1],
                'python_wall':round(time.monotonic()-now,3)}
            (a.out/f'variant{mask}-certificate.json').write_text(
                json.dumps({'machines':result},separators=(',',':'))+'\n')
            print('FIXED',a.seed,'mask',mask,'score',native['best'],
                'iterations',native['iterations'],flush=True)
    gain={int(k):C-v['best'] for k,v in outcomes.items()}
    report=dict(source='Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8',
       original_N7_kernel_unchanged=True,
       same_source_initial_and_no_oracle=True,
       all_four_initial_scores_2044=True,
       seed=a.seed,iteration_limit=a.iterations,
       neutral_machine_interventions=[12,14],
       trials=outcomes,
       interaction_gain= gain[3]-max(gain[1],gain[2]),
       all_start_machine_orders_independently_verified=True,
       complete=True)
    (a.out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',a.seed,'scores',[outcomes[str(i)]['best'] for i in range(4)],
        'interaction_gain',report['interaction_gain'],flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--driver',type=Path,required=True)
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--iterations',type=int,default=800000)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
