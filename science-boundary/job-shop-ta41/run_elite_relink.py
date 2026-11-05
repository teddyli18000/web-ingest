#!/usr/bin/env python3
"""Reproduce elite path relinking under two controlled constructive selectors.

The original verified 2006 parent set is identical for both arms. C++ then
relinks adjacent machine-order inversions between diverse elite schedules,
either greedily or with a conditional second move that targets the newly
critical resource arcs induced by a hypothetical first move.

Any result must be an entirely legal 600-operation, 20-machine schedule;
the independent Python DAG is NOT the same C++ scorer, and an actual
new-best certificate additionally needs Few Shots official verify.py.
"""
import argparse,json,subprocess,time
from pathlib import Path
from search import obtain,setup,evaluate
from dynamic_critical_replacement import state

ROOT=Path(__file__).resolve().parent
SEEDS={
  "ninecore":("ninecore-neutral-baseline","neutral-certificate.json","neutral-verdict.json"),
  "gateway124":("gateway-124","certificate.json","upstream-verdict.json"),
  "critical8":("neutral-critical8","neutral-certificate.json","neutral-verdict.json"),
  "mixed20":("neutral-mixed20","neutral-certificate.json","neutral-verdict.json"),
  "rev5":("warm-backbone-5","neutral-certificate.json","best-verdict.json"),
  "rev6":("warm-backbone-6","neutral-certificate.json","best-verdict.json"),
  "rev7":("continuation-7","neutral-certificate.json","best-verdict.json"),
  "far_unconditioned":("orientation-maxmin-false/witness","certificate.json","upstream-verdict.json"),
  "far_core_guided":("orientation-maxmin-true/witness","certificate.json","upstream-verdict.json")
}

def kendall(a,b):
    n=0
    for m in range(20):
        p={job:k for k,job in enumerate(b[m])}
        v=[p[x] for x in a[m]]
        n+=sum(v[i]>v[j] for i in range(30) for j in range(i+1,30))
    return n

def main(a):
    routes,ds,baseline=obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(baseline,pos,dur)==2006
    parents={"baseline":baseline}
    for name,(folder,cert_file,verdict_file) in SEEDS.items():
        p=ROOT/"results"/folder
        v=json.loads((p/verdict_file).read_text())
        assert v['valid'] and int(v['score'])==2006,(name,v)
        orders=json.loads((p/cert_file).read_text())['machines']
        assert evaluate(orders,pos,dur)==2006
        parents[name]=orders
    a.out.mkdir(parents=True,exist_ok=True)
    inst=a.out/"elite-pool.txt"
    with inst.open("w") as f:
        f.write("30 20\n")
        for j in range(30):
            f.write(" ".join(f"{routes[j][k]} {ds[j][k]}" for k in range(20))+"\n")
        for row in baseline:
            f.write(" ".join(map(str,row))+"\n")
        f.write(str(len(parents)-1)+"\n")
        for name,orders in list(parents.items())[1:]:
            for row in orders:
                f.write(" ".join(map(str,row))+"\n")
    result=a.out/"raw.txt"
    started=time.monotonic()
    subprocess.run([str(a.binary),str(inst),str(result),a.mode,str(a.seed),
                    str(a.evaluations),"ok"],check=True)
    lines=result.read_text().splitlines()
    assert len(lines)==21, len(lines)
    words=lines[0].split()
    assert len(words)==14,words
    summary_numbers=list(map(int,words[:13]))
    (score,evals,invalid,run_count,finished,deadends,paired,hits,
      neutral,visited,maxdist,initial_count,elite_count)=summary_numbers
    cpu=float(words[13])
    assert initial_count==len(parents)
    assert 0<evals<=a.evaluations
    orders=[list(map(int,line.split())) for line in lines[1:]]
    assert len(orders)==20 and all(sorted(row)==list(range(30)) for row in orders)
    independent=evaluate(orders,pos,dur)
    assert independent==score,(independent,score)
    assert score<=2006
    core=json.loads((ROOT/"results"/"consensus-five-parents"/"consensus-analysis.json").read_text())
    revealed=[c["index"] for c in core["proven_unsat_core"]
      if orders[c["machine"]].index(c["to_job"])<orders[c["machine"]].index(c["from_job"])]
    _,newcrit,_=state(orders,pos,dur)
    _,oldcrit,_=state(baseline,pos,dur)
    info=dict(
        instance="ta41",mode=a.mode,seed=a.seed,
        policies_compared="greedy elite path-relink vs replacement-critical-arc targeted pairwise elite path-relink",
        initial_officially_verified_2006_parents=list(parents),
        original_2026_Diaz_implementation=False,
        all_20_machine_NoOverlap_preserved=True,
        all_job_routing_precedences_preserved=True,
        exact_DAG_evaluations=evals,evaluation_budget=a.evaluations,
        cyclic_candidates=invalid,
        path_relinks_started=run_count,completed_target_monotone_paths=finished,
        paths_blocked_by_acyclicity=deadends,
        jointly_accepted_target_directed_pair_moves=paired,
        new_critical_edge_directed_second_moves=hits,
        distinct_neutral_schedules_generated=neutral,
        total_elite_schedules_seen=visited,
        initial_elite_size=initial_count,final_elite_size=elite_count,
        maximum_path_endpoint_kendall_distance=maxdist,
        original_cpp_reported_makespan=score,independent_Python_DAG_makespan=independent,
        closest_kendall_to_eight_original_parents=min(kendall(orders,v) for v in parents.values()),
        baseline_kendall_distance=kendall(orders,baseline),
        new_critical_machine_edges_vs_baseline=len(newcrit-oldcrit),
        old_mandatory_21_core_relations_reversed=revealed,
        wall_seconds_cpp=cpu,wall_seconds_wrapper=round(time.monotonic()-started,3),
        improved=score<=2005,
        note="This is a constructive baseline vs dynamic-repair experiment; neither policy is a faithful 2026 N7/LLG/Diaz implementation. Only official Few Shots checker can establish record."
    )
    archive=Path(str(result)+".novel")
    if archive.exists():
        note=archive.read_text().splitlines()
        assert len(note)==21,len(note)
        reported_novel,checked,protected=map(int,note[0].split())
        assert protected==len(parents) and checked>0
        archived=[list(map(int,line.split())) for line in note[1:]]
        assert len(archived)==20 and all(sorted(row)==list(range(30)) for row in archived)
        arch_score=evaluate(archived,pos,dur)
        assert arch_score==2006,arch_score
        positions=[{job:k for k,job in enumerate(archived[m])} for m in range(20)]
        adj_distance={name:sum(
           positions[m][arr[m][k]]>positions[m][arr[m][k+1]]
           for m in range(20) for k in range(29))
           for name,arr in parents.items()}
        nearest=min(adj_distance.values())
        assert nearest==reported_novel,(nearest,reported_novel)
        kendall_dist={name:kendall(archived,arr) for name,arr in parents.items()}
        info.update(
           archived_verified_neutral_score=arch_score,
           diverse_neutral_trials_sampled=checked,
           reported_minimum_parent_adjacent_pair_disagreement=reported_novel,
           independently_checked_minimum_parent_adjacent_pair_disagreement=nearest,
           minimum_Kendall_distance_to_all_original_parents=min(kendall_dist.values()),
           archive_pairwise_parent_disagreements=adj_distance)
        if score>2005:
            (a.out/"neutral-certificate.json").write_text(json.dumps({"machines":archived})+"\n")
    (a.out/"summary.json").write_text(json.dumps(info,indent=2)+"\n")
    if score<=2005:
        (a.out/"certificate.json").write_text(json.dumps({"machines":orders})+"\n")
    print("RESULT",json.dumps(info),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=('greedy','dynamic2'),required=True)
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--evaluations',type=int,default=1000000)
    p.add_argument('--binary',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
