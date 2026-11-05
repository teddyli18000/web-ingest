#!/usr/bin/env python3
"""Construct hidden-answer 30x20 positive controls from real archived schedules.

The generator (outside the test harness) reads published ta42..ta47 machine
orders from ScheduleOpt and validates every solution by an independent
job+machine DAG evaluator. It *constructs* worsened, still legal schedules
by adjacent transpositions, and writes only the degraded machine orders,
the instance data, and the initial score to each test case.

Search algorithms consume only <case>/start.txt, and never the oracle
machine sequence or its target score. A separate results/manifest.json
records benchmark provenance and the oracle score for post-search judging.
"""
import argparse, hashlib, json, random
from pathlib import Path
from search import setup, evaluate

SELECTED=("ta42js","ta43js","ta44js","ta45js","ta46js","ta47js")

def load_case(root,name,solutions):
    d=json.loads((root/"jobshop"/"instances"/"json"/(name+".json")).read_text())
    ops=d["operations"]
    assert d["jobs"]==30 and d["machines"]==20 and len(ops)==600
    route=[[None]*20 for _ in range(30)]
    durations=[[None]*20 for _ in range(30)]
    for o in ops:
        assert o["option"]==0
        j,k=o["job"],o["step"]
        assert o["operation"]==20*j+k
        assert route[j][k] is None
        route[j][k]=o["machine"]
        durations[j][k]=o["duration"]
    assert all(sorted(row)==list(range(20)) for row in route)
    entry=next((x for x in solutions if x["instance"]==name),None)
    assert entry is not None and len(entry["solution"])==20
    oracle=[[op//20 for op in row] for row in entry["solution"]]
    assert all(sorted(row)==list(range(30)) for row in oracle)
    for m,seq in enumerate(entry["solution"]):
        assert all(route[op//20][op%20]==m for op in seq)
    pos,dur=setup(route,durations)
    score=evaluate(oracle,pos,dur)
    assert score==entry["makespan"],(name,score,entry["makespan"])
    return route,durations,oracle,score,pos,dur

def degrade(oracle,score,pos,duration,seed,level):
    rng=random.Random(seed)
    rows=[x[:] for x in oracle]
    count=0;attempts=0
    best=score
    goal=score+level
    history=[]
    while count<24 and best<goal and attempts<12000:
        attempts+=1
        m=rng.randrange(20)
        i=rng.randrange(29)
        rows[m][i],rows[m][i+1]=rows[m][i+1],rows[m][i]
        val=evaluate(rows,pos,duration)
        if val is not None and score<=val<=score+180 and (
                val>=best or rng.random()<0.06):
            count+=1
            best=val
            history.append([m,i,val])
        else:
            rows[m][i],rows[m][i+1]=rows[m][i+1],rows[m][i]
    assert count>=2 and best>=goal,(seed,level,count,best-score)
    verified=evaluate(rows,pos,duration)
    assert verified==best and verified>score
    return rows,best,history

def main(a):
    benchmark=json.loads((a.reference_root/"jobshop"/"solutions"/"solutions.json").read_text())
    a.out.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for label in SELECTED:
        route,duration,oracle,oracle_score,pos,dur=load_case(a.reference_root,label,benchmark)
        for difficulty in (12,35):
            seed=100000+int(label[2:4])*101+difficulty
            initial,initial_score,changes=degrade(oracle,oracle_score,pos,dur,seed,difficulty)
            name=f"{label}-gap{difficulty}"
            folder=a.out/name
            folder.mkdir(parents=True,exist_ok=True)
            with (folder/"start.txt").open("w") as out:
                out.write("30 20\n")
                for j in range(30):
                    out.write(" ".join(f"{route[j][k]} {duration[j][k]}" for k in range(20))+"\n")
                for m in range(20):
                    out.write(" ".join(map(str,initial[m]))+"\n")
            source_hash=hashlib.sha256(json.dumps(oracle,separators=(",",":")).encode()).hexdigest()
            manifest.append(dict(case=name,instance=label,difficulty_label=difficulty,
                initial_makespan=initial_score,
                verified_hidden_oracle_makespan=oracle_score,
                known_positive_gap=initial_score-oracle_score,
                source_oracle_hash=source_hash,
                degradation_swaps=len(changes),
                source="ScheduleOpt/benchmarks:jobshop/solutions/solutions.json",
                proof="Archived oracle machine sequences independently DAG-scored; no oracle sequences in test-case start.txt."))
            print("FIXTURE",name,"initial",initial_score,"oracle",oracle_score,"gap",initial_score-oracle_score,flush=True)
    assert len(manifest)==12
    (a.out/"manifest.json").write_text(json.dumps(dict(cases=manifest,
       evaluation_rule="Algorithms read only case start.txt. Target oracle score/hash and oracle orders never passed to the search process.",
       official_limitations="This does not prove algorithmic generalization. Compare matched initialized algorithms, at multiple seeds and time budgets."),indent=2)+"\n")
    print("RESULT generated",len(manifest),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--reference-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    main(p.parse_args())
