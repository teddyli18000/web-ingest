#!/usr/bin/env python3
"""Test whether six independently verified 4-opt neutral moves commute.

All combinations are reconstructed from the *same* baseline edge set.
Every Hamiltonian combination is validated by the upstream exact scorer;
connectedness is checked independently through degree-two traversal.
"""
import argparse,importlib.util,itertools,json,os,time
from pathlib import Path

def edge(a,b):return (a,b) if a<b else (b,a)
def edges(t):return {edge(t[i],t[(i+1)%len(t)]) for i in range(len(t))}
def cycle_from(n,es):
    adj=[[] for _ in range(n+1)]
    for a,b in es:
        adj[a].append(b);adj[b].append(a)
    assert all(len(adj[i])==2 for i in range(1,n+1))
    seen=bytearray(n+1)
    result=[]
    cur=1;prev=0
    while not seen[cur]:
        seen[cur]=1;result.append(cur)
        x,y=adj[cur];nxt=x if x!=prev else y
        prev,cur=cur,nxt
    return result,cur,len(result)==n and cur==1

def main():
    parser=argparse.ArgumentParser()
    for opt in ('baseline','moves','report','output-dir'):
        parser.add_argument('--'+opt,required=True)
    args=parser.parse_args()
    t0=time.monotonic()
    baseline=json.loads(Path(args.baseline).read_text())['tour']
    n=len(baseline)
    assert n==100000
    base=edges(baseline)
    moves=json.loads(Path(args.moves).read_text())['neutral_moves']
    assert len(moves)==6
    mods=[]
    for move in moves:
        old=set(map(tuple,move['removed']))
        new=set(map(tuple,move['added']))
        assert len(old)==len(new)==4 and old<=base and not (new&base)
        mods.append((old,new))
    pairs=[]
    for i in range(6):
        for j in range(i+1,6):
            pairs.append({'i':i,'j':j,
                'overlap_vertices':len({v for e in mods[i][0]|mods[i][1] for v in e}&
                    {v for e in mods[j][0]|mods[j][1] for v in e})})
    spec=importlib.util.spec_from_file_location('p010_verify',
        Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    assert v.tour_length(baseline)==5757191
    all_records=[]
    outdir=Path(args.output_dir)
    outdir.mkdir(parents=True,exist_ok=True)
    best_mask=0
    for mask in range(64):
        selected=[i for i in range(6) if (mask>>i)&1]
        combined=set(base)
        for i in selected:
            combined.difference_update(mods[i][0])
        for i in selected:
            combined.update(mods[i][1])
        assert len(combined)==n
        candidate,endpoint,connected=cycle_from(n,combined)
        record={'mask':mask,'selected_move_indices':selected,'connected':connected,
            'traversed':len(candidate)}
        if connected:
            score=v.tour_length(candidate)
            assert score==5757191
            digest=v.canonical_hash({'tour':v.canonical_tour(candidate)})
            record.update({'score':score,'canonical_hash':digest})
            # Freeze a couple of extreme combinations as full certificates.
            if mask in [0,63]:
                (outdir/f'mask-{mask:02d}.json').write_text(
                    json.dumps({'tour':candidate},separators=(',',':')))
        all_records.append(record)
    report={'baseline_score':5757191,'move_count':6,
        'pair_overlap':pairs,'total_combinations':64,
        'connected_combinations':sum(r['connected'] for r in all_records),
        'disconnected_combinations':sum(not r['connected'] for r in all_records),
        'unique_connected_hashes':len({r.get('canonical_hash') for r in all_records if r['connected']}),
        'records':all_records,
        'elapsed_seconds':round(time.monotonic()-t0,3)}
    assert report['unique_connected_hashes']==report['connected_combinations']
    Path(args.report).parent.mkdir(parents=True,exist_ok=True)
    Path(args.report).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:val for k,val in report.items() if k!='records'}),flush=True)

if __name__=='__main__':
    main()
