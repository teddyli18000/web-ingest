#!/usr/bin/env python3
"""Fixed-work CP-neutral + original N7 crossover transfer benchmark.

24 source-independent high-quality 30x20 N7 starts; two second-stage seeds;
two machine-release policies. All runs use original Ming Qi N7 engine with
fixed iteration stopping rather than variable wall-time. Each source N7
control receives 800k iterations. CP-neutral creates a non-worsening but
structurally altered complete schedule (single-worker deterministic CP).
The hybrid N7 receives fewer iterations, scaled by measured CP time:
    hybrid_I = floor(I*(N7_wall-CP_wall)/N7_wall)
with a conservative minimum 100k. The trial records actual total time,
so neither hardware speed nor CP overhead is hidden.

All final solutions are independently resimulated from 600 operation
job and machine precedences. The source oracle is never consulted.
"""
from __future__ import annotations
import argparse,json,statistics,tempfile,time
from pathlib import Path
from partial_resource_pair_repair import parse_case
from neutral_machine_cp_then_original_n7 import exact_neutral
from n7_fixed_native import original_n7_fixed

ROOT=Path(__file__).resolve().parent

def main(a):
    cases=sorted((ROOT/'positive-n7-elite-data').glob('ta*js-n7elite*/start.txt'))
    assert len(cases)==12
    cases=cases[6*a.shard:6*(a.shard+1)]
    assert len(cases)==6
    a.out.mkdir(parents=True,exist_ok=True)
    experiments=[]
    def save(done=False):
        out=dict(policy=a.policy,seed=a.seed,shard=a.shard,
            reference_engine='Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8',
            reference_N7_kernels_unmodified=True,
            pure_reference_N7_iterations=a.iterations,
            allowed_CP_wall_seconds=a.cp_seconds,
            matched_work_rule='hybrid N7 iterations = floor(pure_N7_I*(pure_N7_wall - measured_CP_wall)/pure_N7_wall), minimum 100k; actual timing recorded',
            complete=done,
            trials=experiments)
        (a.out/'results.json').write_text(json.dumps(out,indent=2)+'\n')
    for source in cases:
        original,pos,dur,C=parse_case(str(source))
        start=time.monotonic()
        case=source.parent.name
        casedir=a.out/case;casedir.mkdir(exist_ok=True)
        src=source.read_text().splitlines()
        assert len(src)==51
        with tempfile.TemporaryDirectory() as scratch:
            scratch=Path(scratch)
            instance=scratch/'instance.txt'
            instance.write_text('\n'.join(src[:31])+'\n')
            direct,directorder=original_n7_fixed(a.driver,instance,original,pos,dur,
                a.seed,a.iterations,scratch)
            cp,neutral=exact_neutral(original,pos,dur,C,a.policy,a.seed,
                a.cp_seconds,False,a.open_machines,a.min_changed_machines,
                a.min_flips,workers=1)
            if neutral is not None:
                used=cp['cp_wall_seconds']
                iterations=max(100000,int(a.iterations*max(0,direct['native_seconds']-used)/
                                          direct['native_seconds']))
                hybrid,hybridorder=original_n7_fixed(a.driver,instance,neutral,pos,dur,
                    a.seed,iterations,scratch)
                assert hybrid['best']<=C
                (casedir/'neutral-certificate.json').write_text(
                    json.dumps({'machines':neutral},separators=(',',':'))+'\n')
                (casedir/'hybrid-certificate.json').write_text(
                    json.dumps({'machines':hybridorder},separators=(',',':'))+'\n')
            else:
                iterations=None;hybrid=None
        row=dict(case=case,initial=C,seed=a.seed,
            pure_N7_best=direct['best'],pure_N7_iterations=direct['iterations'],
            pure_N7_seconds=direct['native_seconds'],
            CP_status=cp['status'],CP_seconds=cp['cp_wall_seconds'],
            CP_neutral_makespan=cp.get('neutral_makespan'),
            CP_changed_machine_count=cp.get('changed_machines'),
            hybrid_N7_iterations=iterations,
            hybrid_best=hybrid['best'] if hybrid is not None else None,
            hybrid_N7_seconds=hybrid['native_seconds'] if hybrid else None,
            hybrid_total_search_seconds=(
                 cp['cp_wall_seconds']+hybrid['native_seconds'] if hybrid else None),
            total_experiment_wall_seconds=round(time.monotonic()-start,3))
        row['hybrid_vs_pure_score_advantage']=(
            direct['best']-hybrid['best'] if hybrid else None)
        experiments.append(row);save()
        print('CASE',case,'policy',a.policy,'seed',a.seed,'initial',C,
            'N7',direct['best'],'hybrid',row['hybrid_best'],
            'hybrid_iterations',iterations,'CP',cp['status'],flush=True)
    save(True)
    print('RESULT',a.policy,a.seed,a.shard,
        'improved',sum(x['hybrid_vs_pure_score_advantage'] is not None and
            x['hybrid_vs_pure_score_advantage']>0 for x in experiments),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--policy',choices=['static','random'],required=True)
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--shard',choices=[0,1],type=int,required=True)
    p.add_argument('--driver',type=Path,required=True)
    p.add_argument('--iterations',type=int,default=800000)
    p.add_argument('--cp-seconds',type=float,default=3.0)
    p.add_argument('--open-machines',type=int,default=8)
    p.add_argument('--min-changed-machines',type=int,default=2)
    p.add_argument('--min-flips',type=int,default=3)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
