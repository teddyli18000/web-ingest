#!/usr/bin/env python3
"""Controlled neutral-machine-interaction ablation with unchanged native N7.

Anchor example: genuine source N7 elite ta46js-n7elite1701 makespan 2044.
A source-only CP-neutral machine shuffle retained makespan 2044 and
changed ONLY machine 12 and machine 14, while the set of all critical
machine precedences was unchanged.

An exact factorial experiment creates four independently DAG-validated
complete starts:
  00 both original, 10 only machine 12 changed,
  01 only machine 14 changed, 11 both changed.
Run author original N7 from EACH under the same random seed and 14s cap.
This tests whether an observed benefit is additive vs interaction,
instead of inferring causality from a single CP result or neural predictor.
No archived hidden oracle is accessed by any phase.
"""
import argparse,json,tempfile,time
from pathlib import Path
from partial_resource_pair_repair import parse_case
from neutral_machine_cp_then_original_n7 import native_n7
from search import evaluate

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'positive-n7-elite-data'/'ta46js-n7elite1701'/'start.txt'
CP=ROOT/'results'/'neutral-N7-ta46js-n7elite1701-random-seed4107'/'neutral-certificate.json'

def main(a):
    orig,pos,dur,initial=parse_case(str(BASE))
    assert initial==2044
    modified=json.loads(CP.read_text())['machines']
    assert evaluate(modified,pos,dur)==initial
    changed=[m for m in range(20) if orig[m]!=modified[m]]
    assert changed==[12,14],changed
    variants={}
    for mask in range(4):
        new=[x[:] for x in orig]
        for i,m in enumerate(changed):
            if (mask>>i)&1:new[m]=modified[m][:]
        assert evaluate(new,pos,dur)==2044,(mask,evaluate(new,pos,dur))
        variants[mask]=new
    full_data=BASE.read_text().splitlines()
    assert len(full_data)==51
    a.out.mkdir(parents=True,exist_ok=True)
    outcomes={}
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        instance=tmp/'instance.txt'
        instance.write_text('\n'.join(full_data[:31])+'\n')
        for mask,orders in variants.items():
            began=time.monotonic()
            native,witness=native_n7(a.driver,instance,orders,pos,dur,
                                     a.seed,a.seconds,tmp)
            verified=evaluate(witness,pos,dur)
            assert verified==native['score']<=2044
            outcomes[str(mask)]=dict(
                subset=mask,changed_machine_orders=[changed[i] for i in range(2) if (mask>>i)&1],
                starting_makespan=2044,
                best_makespan=verified,
                gain=2044-verified,
                original_source_N7_seconds=native['native_seconds'],
                actual_wall_seconds=round(time.monotonic()-began,3),
                native_iterations=native['iterations'])
            (a.out/f'variant{mask}-certificate.json').write_text(
                json.dumps({'machines':witness},separators=(',',':'))+'\n')
            print('ABLATED',a.seed,'mask',mask,'best',verified,
                  'gain',2044-verified,flush=True)
    baseline=outcomes['0']['gain'];single=max(outcomes['1']['gain'],outcomes['2']['gain'])
    ab=outcomes['3']['gain']
    result=dict(instance='ta46js-n7elite1701',seed=a.seed,
        original_N7_source='Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8',
        original_search_loop_unchanged=True,
        seed_and_14_second_budget_matched=True,
        nominal_seconds=a.seconds,
        anchor_score=2044,CP_neutral_changed_machines=changed,
        all_four_input_states_legal_and_makespan_2044=True,
        oracle_hidden=True,results=outcomes,
        joint_vs_best_single_gain=ab-single,
        joint_vs_no_machine_change_gain=ab-baseline,
        complete=True)
    (a.out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--driver',required=True,type=Path)
    p.add_argument('--seed',required=True,type=int)
    p.add_argument('--seconds',default=14,type=int)
    p.add_argument('--out',required=True,type=Path)
    main(p.parse_args())
