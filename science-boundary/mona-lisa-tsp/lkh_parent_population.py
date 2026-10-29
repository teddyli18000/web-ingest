#!/usr/bin/env python3
"""Prepare and independently audit LKH3 source tours for GPX population tests.

The purpose is to create structurally distinct, high-quality *parents*, not
to present another LKH parameter sweep as a novel solver. Initial tours
are different points of the independently verified 51-bit neutral cube.
Only the upstream Few Shots exact verifier can approve record candidates.
"""
import argparse,importlib.util,json,os,random
from pathlib import Path

def ek(a,b):return (a,b) if a<b else (b,a)
def edges(t):return {ek(t[i],t[(i+1)%len(t)]) for i in range(len(t))}
def construct(base,mods,mask):
    n=len(base);setedges=edges(base)
    for i,m in enumerate(mods):
        if (mask>>i)&1:
            setedges.difference_update(ek(*x) for x in m['removed'])
    for i,m in enumerate(mods):
        if (mask>>i)&1:
            setedges.update(ek(*x) for x in m['added'])
    assert len(setedges)==n
    adj=[[] for _ in range(n+1)]
    for a,b in setedges:adj[a].append(b);adj[b].append(a)
    assert all(len(adj[u])==2 for u in range(1,n+1))
    seen=bytearray(n+1);cur=1;prev=0;out=[]
    while not seen[cur]:
        seen[cur]=1;out.append(cur)
        a,b=adj[cur];nextnode=a if a!=prev else b
        prev,cur=cur,nextnode
    assert cur==1 and len(out)==n
    return out

def verifier():
    modulepath=Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py'
    spec=importlib.util.spec_from_file_location('verifier',modulepath)
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    return v

def write_tour(path,route):
    Path(path).write_text(f'NAME : monalisa-neutral-parent\nTYPE : TOUR\nDIMENSION : {len(route)}\nTOUR_SECTION\n'+
                          ''.join(f'{x}\n' for x in route)+'-1\nEOF\n')

def read_tour(path):
    s=Path(path).read_text().splitlines()
    indices=[i for i,x in enumerate(s) if x.strip().upper()=='TOUR_SECTION']
    assert len(indices)==1
    route=[]
    for line in s[indices[0]+1:]:
        for word in line.split():
            if word=='-1':return route
            if word.upper()=='EOF':return route
            route.append(int(word))
    return route

def main():
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['prepare','collect'])
    for name in ('baseline','neutral-moves','workdir'):p.add_argument('--'+name,required=True)
    p.add_argument('--mask-mode',choices=['baseline','all','euclidean','random'],default='baseline')
    p.add_argument('--seed',type=int,default=19)
    p.add_argument('--seconds',type=int,default=120)
    args=p.parse_args()
    work=Path(args.workdir);work.mkdir(parents=True,exist_ok=True)
    v=verifier()
    baseline=json.loads(Path(args.baseline).read_text())['tour']
    assert len(baseline)==100000 and v.tour_length(baseline)==5757191
    data=json.loads(Path(args.neutral_moves).read_text())
    mods=[data['moves'][i] for i in data['selected_indices']]
    assert len(mods)==51
    if args.mask_mode=='all':mask=(1<<51)-1
    elif args.mask_mode=='euclidean':mask=sum(1<<i for i,m in enumerate(mods) if m['continuous_delta']<0)
    elif args.mask_mode=='random':mask=random.Random(args.seed).getrandbits(51)
    else:mask=0
    initial=construct(baseline,mods,mask)
    assert v.tour_length(initial)==5757191
    if args.mode=='prepare':
        xs,ys=v.coordinates()
        assert len(xs)==len(ys)==100000
        (work/'instance.tsp').write_text(
          'NAME : monalisa100k\nTYPE : TSP\nDIMENSION : 100000\nEDGE_WEIGHT_TYPE : EUC_2D\nNODE_COORD_SECTION\n'+
          ''.join(f'{i+1} {xs[i]} {ys[i]}\n' for i in range(100000))+'EOF\n')
        write_tour(work/'initial.tour',initial)
        params='\n'.join([
          f'PROBLEM_FILE = {work.resolve()}/instance.tsp',
          f'INITIAL_TOUR_FILE = {work.resolve()}/initial.tour',
          f'TOUR_FILE = {work.resolve()}/lkh-best.tour',
          f'OUTPUT_TOUR_FILE = {work.resolve()}/lkh-improvement.tour',
          'RUNS = 1',
          f'SEED = {args.seed}',
          f'TIME_LIMIT = {args.seconds}',
          'MAX_TRIALS = 500',
          'MAX_CANDIDATES = 5',
          'MOVE_TYPE = 5',
          'PATCHING_C = 3',
          'PATCHING_A = 2',
          'RECOMBINATION = GPX2',
          'TRACE_LEVEL = 1',
          ''])
        (work/'params.par').write_text(params)
        print(json.dumps({'stage':'prepared','mode':args.mask_mode,
           'neutral_mask':str(mask),'baseline_score':5757191,'seed':args.seed}))
        return
    output=work/'lkh-best.tour'
    assert output.exists(),('LKH did not produce final tour',str(output))
    route=read_tour(output)
    assert len(route)==100000 and len(set(route))==100000
    score=v.tour_length(route)
    cert={'tour':route}
    blob=json.dumps(cert,separators=(',',':')).encode()
    verdict=v.verify_bytes(blob,v.load_config())
    assert verdict['valid'] and int(verdict['score'])==score
    changed=len(edges(route)^edges(initial))//2
    basechanged=len(edges(route)^edges(baseline))//2
    report={'mask_mode':args.mask_mode,'seed':args.seed,
       'neutral_mask':str(mask),'initial_score':5757191,
       'lkh_score':score,'gain':5757191-score,
       'changed_edges_from_initial':changed,'changed_edges_from_baseline':basechanged,
       'canonical_hash':verdict['canonical_hash']}
    (work/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (work/'certificate.json').write_bytes(blob)
    print(json.dumps({'stage':'verified_population_member',**report}))

if __name__=='__main__':main()
