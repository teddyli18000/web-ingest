#!/usr/bin/env python3
"""Export/replay a full C7^5 CHILS search seeded by validated 367-point sets.

The full graph has all 7^5=16807 vertices.  Vertices conflict when every cyclic
coordinate difference is 0 or +/-1; self loops are omitted in METIS.  A corpus
entry is an exact 367-point independent set.  CHILS solution indices are
1-based full-graph vertex positions, so vertex v maps to v+1.

If replay finds >=368 points, the first 368 are squared to an independent set in
C7^10 of size 368^2 = 135424, far above the Few Shots p004 target 134754.
"""
from __future__ import annotations
import argparse,itertools,json
from pathlib import Path

N5=7**5

def dec(v):
    d=[0]*5
    for i in range(4,-1,-1):d[i]=v%7;v//=7
    return tuple(d)
def enc(d):
    z=0
    for x in d:z=7*z+x
    return z
def conflict(a,b):
    if a==b:return True
    da,db=dec(a),dec(b)
    return all((x-y)%7 in (0,1,6) for x,y in zip(da,db))
def independent(S):
    S=set(S)
    for v in S:
        d=dec(v)
        for delta in itertools.product((-1,0,1),repeat=5):
            if all(x==0 for x in delta):continue
            u=enc(tuple((d[i]+delta[i])%7 for i in range(5)))
            if u in S:return False
    return True

def export(corpus:Path,graph:Path,seeds:Path,status:Path):
    data=json.loads(corpus.read_text());rows=data['sets']
    if not rows:raise RuntimeError('empty corpus')
    # Exact full graph adjacency by 3^5 closed neighborhoods minus self.
    adj=[];degree_sum=0
    for v in range(N5):
        d=dec(v);row=[]
        for delta in itertools.product((-1,0,1),repeat=5):
            if all(x==0 for x in delta):continue
            u=enc(tuple((d[i]+delta[i])%7 for i in range(5)))
            row.append(u+1)
        row=sorted(set(row))
        if len(row)!=242:raise RuntimeError(('degree',v,len(row)))
        adj.append(row);degree_sum+=len(row)
    if degree_sum%2:raise RuntimeError('odd degree sum')
    edges=degree_sum//2
    graph.parent.mkdir(parents=True,exist_ok=True)
    with graph.open('w',encoding='ascii') as h:
        h.write(f'{N5} {edges} 10\n')
        for row in adj:h.write('1 '+' '.join(map(str,row))+'\n')
    seeds.mkdir(parents=True,exist_ok=True);manifest=[]
    seen=set()
    for i,row in enumerate(rows):
        S=tuple(sorted(map(int,row['points'])))
        if len(S)!=367 or len(set(S))!=367 or not independent(S):raise RuntimeError(('bad seed',i,row.get('sha256')))
        h=row['sha256']
        if h in seen:raise RuntimeError(('duplicate hash',h))
        seen.add(h);p=seeds/f'{i:02d}.sol';p.write_text(''.join(f'{v+1}\n' for v in S),encoding='ascii')
        manifest.append({'index':i,'sha256':h,'sources':row['sources'],'path':p.name})
    st={'method':'full-c7p5-public367-chils-export','graph_vertices':N5,'graph_edges':edges,'degree':242,'seed_count':len(manifest),'seeds':manifest}
    status.parent.mkdir(parents=True,exist_ok=True);status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in st.items() if k!='seeds'},sort_keys=True))

def read_solution(p:Path):
    ids=[int(x) for x in p.read_text(encoding='ascii').split()]
    if len(ids)!=len(set(ids)) or any(x<1 or x>N5 for x in ids):raise RuntimeError(('bad solution indices',p,len(ids)))
    S=[x-1 for x in ids]
    if not independent(S):raise RuntimeError(('CHILS output not independent',p,len(S)))
    return S

def replay(best_dir:Path,output:Path,status:Path):
    rows=[];best=None
    for p in sorted(best_dir.glob('*.sol')):
        S=read_solution(p);r={'file':p.name,'size':len(S)};rows.append(r)
        if best is None or len(S)>len(best[1]):best=(p,S)
    if best is None:raise RuntimeError('no CHILS outputs')
    p,S=best;st={'method':'full-c7p5-public367-chils-replay','outputs':len(rows),'best_file':p.name,'best_size':len(S),'candidate_368':len(S)>=368,'sizes':rows}
    if len(S)>=368:
        A=sorted(S)[:368]
        pts=[]
        for x in A:
            sx=''.join(map(str,dec(x)))
            for y in A:pts.append(sx+''.join(map(str,dec(y))))
        if len(pts)!=135424 or len(set(pts))!=135424:raise RuntimeError(('square size',len(pts),len(set(pts))))
        output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps({'points':sorted(pts)},separators=(',',':'))+'\n');st['score']=135424;st['auxiliary_used']=368
    status.parent.mkdir(parents=True,exist_ok=True);status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in st.items() if k!='sizes'},sort_keys=True))

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    e=sub.add_parser('export');e.add_argument('corpus',type=Path);e.add_argument('graph',type=Path);e.add_argument('seeds',type=Path);e.add_argument('status',type=Path)
    r=sub.add_parser('replay');r.add_argument('best_dir',type=Path);r.add_argument('output',type=Path);r.add_argument('status',type=Path)
    a=ap.parse_args();export(a.corpus,a.graph,a.seeds,a.status) if a.cmd=='export' else replay(a.best_dir,a.output,a.status)
if __name__=='__main__':main()
