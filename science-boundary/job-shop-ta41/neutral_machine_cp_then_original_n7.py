#!/usr/bin/env python3
"""Coordinated neutral CP machine shuffle followed by TRUE published N7.

Falsifiable hypothesis: a neutral (Cmax non-worsening) machine-block
rearrangement can move an independently strong N7 incumbent to a more
productive basin than a matched total-time genuine N7 search alone.

This is hybrid CP-large-neighborhood + source-faithful N7, i.e. NOT
newly invented CP-LNS/tabu. Includes full job and machine constraints.
The ta41 run additionally forces at least one of the already
independently certified necessary 21 incumbent gateway pairs to reverse,
so a 2006 neutral parent crosses a known structural gate.

Keep hard 600-operation data and original source N7 untouched. Native
N7 source is pinned and only its warmstart loading method differs.
All candidate machine orders independently DAG-reverified.
"""
from __future__ import annotations
import argparse,csv,json,random,subprocess,tempfile,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import evaluate
from partial_resource_pair_repair import parse_case
from counterfactual_joint_cut import dag_graph,immutable_and_resource

ROOT=Path(__file__).resolve().parent

def choose_machines(orders,pos,dur,C,policy,seed,count):
    rng=random.Random(seed)
    graph=dag_graph(dur,immutable_and_resource(orders,pos),set())
    assert graph and graph['lb']==C
    scores=[0.0]*20
    for u,v,m in immutable_and_resource(orders,pos):
        gap=C-(graph['head'][u]+dur[u]+graph['tail'][v])
        scores[m]+=1.0/(1+max(0,gap))
    if policy=='static':
        ranked=sorted(range(20),key=lambda m:(-scores[m],rng.random()))
    else:
        ranked=list(range(20));rng.shuffle(ranked)
    return sorted(ranked[:count]),scores,graph

def exact_neutral(orders,pos,dur,C,policy,seed,seconds,is_ta41,
                  open_count,min_groups,min_flips,workers=4):
    free,scores,graph=choose_machines(orders,pos,dur,C,policy,seed,open_count)
    if is_ta41:
        mandatory=json.loads((ROOT/'results'/
           'ta41-mandatory-adjacent-gateways-independently-proved.json').read_text())
        gw=set(mandatory['asserted_machine_resource_arcs'])
        assert len(gw)==21
        if not gw.intersection({m*29+k for m in free for k in range(29)}):
            # Ensure at least one structural necessary gateway is variable;
            # choose a gate machine by source-only criticality, no 2005 oracle.
            gateway_m=max(sorted(set(x//29 for x in gw)),key=lambda m:scores[m])
            free[-1]=gateway_m
            free=sorted(set(free))
            assert len(free)==open_count
    else:gw=set()
    model=cp_model.CpModel()
    s=[model.new_int_var(0,C-dur[i],f's{i}') for i in range(600)]
    e=[model.new_int_var(dur[i],C,f'e{i}') for i in range(600)]
    intervals=[model.new_interval_var(s[i],dur[i],e[i],f'iv{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(s[j*20+k+1]>=e[j*20+k])
    flags=[];changed=[];gateway_flags=[]
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
        if m not in free:
            for a,b in zip(orders[m],orders[m][1:]):
                u=a*20+pos[a][m];v=b*20+pos[b][m]
                model.add(s[v]>=e[u])
            continue
        flips=[]
        for k,(a,b) in enumerate(zip(orders[m],orders[m][1:])):
            u=a*20+pos[a][m];v=b*20+pos[b][m]
            f=model.new_bool_var(f'flip_{m}_{k}')
            model.add(s[u]>=e[v]).only_enforce_if(f)
            model.add(s[v]>=e[u]).only_enforce_if(f.Not())
            flips.append(f);flags.append(f)
            if m*29+k in gw:gateway_flags.append(f)
        cm=model.new_bool_var(f'changed_machine_{m}')
        model.add(sum(flips)>=cm)
        model.add(sum(flips)<=29*cm)
        changed.append(cm)
    assert len(flags)==29*len(free)
    assert min_groups<=len(free)
    model.add(sum(changed)>=min_groups)
    model.add(sum(flags)>=min_flips)
    if is_ta41:
        assert gateway_flags
        model.add(sum(gateway_flags)>=1)
    # Use original complete DAG head values for neutral start hints,
    # never an archived 2005 or positive-control target schedule.
    for op in range(600):
        model.add_hint(s[op],graph['head'][op])
        model.add_hint(e[op],graph['head'][op]+dur[op])
    for f in flags:model.add_hint(f,0)
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=workers
    solver.parameters.random_seed=seed%2147483647
    solver.parameters.max_time_in_seconds=seconds
    tick=time.monotonic()
    st=solver.solve(model)
    record=dict(status=solver.status_name(st),
        cp_wall_seconds=round(time.monotonic()-tick,3),cp_conflicts=solver.num_conflicts,
        free_machines=free,required_changed_machines=min_groups,
        required_original_adjacent_pair_reversals=min_flips,
        gateway_reversal_hard_required=is_ta41)
    if st not in (cp_model.FEASIBLE,cp_model.OPTIMAL):return record,None
    rows=[[j for j in sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]]))]
          for m in range(20)]
    score=evaluate(rows,pos,dur)
    assert score is not None and score<=C
    groupchange=0;pairchange=0;gated=0
    for m in range(20):
        rank={j:i for i,j in enumerate(rows[m])}
        local=0
        for k,(a,b) in enumerate(zip(orders[m],orders[m][1:])):
            if rank[a]>rank[b]:
                pairchange+=1;local+=1
                if m*29+k in gw:gated+=1
        groupchange+=(local>0)
    assert groupchange>=min_groups and pairchange>=min_flips
    if is_ta41:assert gated>=1
    record.update(neutral_makespan=score,changed_machines=groupchange,
                  reversed_original_adjacent_pairs=pairchange,
                  reversed_mandatory_gateway_pairs=gated)
    return record,rows

def native_n7(binary,instance_file,orders,pos,dur,seed,seconds,dir):
    # Input format is that used in previous original published N7 comparison.
    order_file=dir/'warm.txt'
    order_file.write_text('\n'.join(' '.join(map(str,row)) for row in orders)+'\n')
    native=dir/'native.csv'
    cp=subprocess.run([str(binary),str(instance_file),str(native),
                       str(seconds),str(seed),str(order_file)],
                      capture_output=True,text=True,timeout=seconds+25)
    assert cp.returncode==0,(cp.stdout,cp.stderr[-2000:])
    items=cp.stdout.strip().split()
    assert items[0]=='RESULT' and len(items)==4,items
    reported=int(items[1])
    starts=[[] for _ in range(20)]
    seen=set()
    with native.open() as f:
        for rec in csv.DictReader(f):
            j=int(rec['Job'])-1;k=int(rec['Operation'])-1
            m=int(rec['Machine']);start=int(rec['StartTime']);end=int(rec['EndTime'])
            assert (j,k) not in seen and 0<=j<30 and 0<=k<20
            assert pos[j][m]==k and end-start==dur[j*20+k]
            seen.add((j,k));starts[m].append((start,j))
    assert len(seen)==600 and all(len(v)==30 for v in starts)
    sortedrows=[[j for _,j in sorted(items)] for items in starts]
    actual=evaluate(sortedrows,pos,dur)
    assert actual==reported and actual<=evaluate(orders,pos,dur)
    return dict(score=actual,native_seconds=float(items[3]),
        iterations=int(items[2]),independently_audited_600_records=True),sortedrows

def run(a):
    old,pos,dur,initial=parse_case(a.start)
    ta41=a.start=='ta41'
    a.out.mkdir(parents=True,exist_ok=True)
    begun=time.monotonic()
    report=dict(instance=('ta41' if ta41 else Path(a.start).parent.name),
      original_makespan=initial,
      source_n7_revision='Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8',
      original_author_N7_search_unchanged=True,
      oracle_never_loaded_by_optimizer=True,
      policy=a.policy,seed=a.seed,
      comparison='neutral CP+source-faithful N7 vs source-faithful N7 alone at same total planning budget',
      total_time_budget=a.total_seconds)
    with tempfile.TemporaryDirectory() as temp:
        dir=Path(temp)
        instance=dir/'instance.txt'
        inv=[[None]*20 for j in range(30)]
        for j in range(30):
            for m in range(20):inv[j][pos[j][m]]=m
        with instance.open('w') as f:
            f.write('30 20\n')
            for j in range(30):
                f.write(' '.join(f'{inv[j][k]} {dur[j*20+k]}' for k in range(20))+'\n')
        n7_seed=a.seed%2147483647
        # Matched budget source-N7-only control is run first.
        control,control_rows=native_n7(a.driver,instance,old,pos,dur,n7_seed,
                                       a.total_seconds,dir)
        report['control_only_N7']=control
        neutral_record,neutral=exact_neutral(old,pos,dur,initial,
            a.policy,a.seed,a.cp_seconds,ta41,a.open_machines,
            a.min_changed_machines,a.min_reversed_pairs)
        report['neutral_cp']=neutral_record
        if neutral is not None:
            cp_used=neutral_record['cp_wall_seconds']
            remaining=max(0,int(a.total_seconds-math.ceil(cp_used)))
            report['hybrid_remaining_N7_seconds']=remaining
            if remaining:
                hybrid,hybrid_rows=native_n7(a.driver,instance,neutral,pos,dur,
                    n7_seed,remaining,dir)
            else:
                hybrid_rows=neutral
                hybrid=dict(score=evaluate(neutral,pos,dur),
                           native_seconds=0.0,iterations=0,
                           independently_audited_600_records=False)
            report['hybrid_CP_then_N7']=hybrid
            score=evaluate(hybrid_rows,pos,dur)
            assert score is not None and score<=initial
            (a.out/'hybrid-certificate.json').write_text(
                json.dumps({'machines':hybrid_rows},separators=(',',':'))+'\n')
            (a.out/'neutral-certificate.json').write_text(
                json.dumps({'machines':neutral},separators=(',',':'))+'\n')
        else:
            report['hybrid_CP_then_N7']=None
        report['hybrid_better_than_direct_N7']=(
            report['hybrid_CP_then_N7'] is not None and
            report['hybrid_CP_then_N7']['score']<control['score'])
        report['hybrid_equal_to_direct_N7']=(
            report['hybrid_CP_then_N7'] is not None and
            report['hybrid_CP_then_N7']['score']==control['score'])
        report['complete']=True
        report['total_actual_wall_seconds']=round(time.monotonic()-begun,3)
        (a.out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('RESULT',json.dumps(report),flush=True)

if __name__=='__main__':
    import math
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True)
    p.add_argument('--policy',choices=['static','random'],required=True)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--driver',type=Path,required=True)
    p.add_argument('--open-machines',type=int,default=15)
    p.add_argument('--min-changed-machines',type=int,default=3)
    p.add_argument('--min-reversed-pairs',type=int,default=6)
    p.add_argument('--cp-seconds',type=float,default=5.)
    p.add_argument('--total-seconds',type=int,default=15)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
