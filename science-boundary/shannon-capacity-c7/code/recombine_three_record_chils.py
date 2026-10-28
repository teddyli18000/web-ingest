#!/usr/bin/env python3
"""Export/replay global MIS search on the union of three verified C7^10 records.

Inputs are three verifier-valid independent sets. Their universal intersection
is isolated in the union, so CHILS only needs to search the exact conflict graph
on D = union - intersection.  The public baseline restricted to D is supplied
as a known initial independent set.  The graph itself is enumerated exactly by
the same base-7 confusability trie used by the durable exact recombination code.

Subcommands:
  export GRAPH INIT STATUS CERT1 CERT2 CERT3
  replay SOLUTION OUTPUT STATUS CERT1 CERT2 CERT3
"""
import argparse
import json
from pathlib import Path

TARGET = 134754


def load(path: Path) -> set[str]:
    obj=json.loads(path.read_text())
    pts=obj.get('points')
    if not isinstance(pts,list): raise ValueError(f'bad certificate {path}')
    s=set(pts)
    if len(s)!=len(pts): raise ValueError(f'duplicate point {path}')
    if any(len(p)!=10 or any(c not in '0123456' for c in p) for p in s):
        raise ValueError(f'bad point {path}')
    return s


def conflict(a: str,b: str)->bool:
    return all((ord(x)-ord(y))%7 in (0,1,6) for x,y in zip(a,b))


def build_trie(words:list[str]):
    children=[{}]; terminal=[-1]
    for j,w in enumerate(words):
        node=0
        for ch in w:
            d=ord(ch)-48; z=children[node].get(d)
            if z is None:
                z=len(children); children[node][d]=z; children.append({}); terminal.append(-1)
            node=z
        if terminal[node]!=-1: raise RuntimeError('duplicate trie terminal')
        terminal[node]=j
    return children,terminal


def exact_adjacency(words:list[str]):
    children,terminal=build_trie(words)
    allowed=[[(d-1)%7,d,(d+1)%7] for d in range(7)]
    adj=[[] for _ in words]; edges=0; visits=0
    for i,w in enumerate(words):
        frontier=[0]
        for ch in w:
            digs=allowed[ord(ch)-48]; nxt=[]
            for node in frontier:
                c=children[node]
                for d in digs:
                    z=c.get(d)
                    if z is not None: nxt.append(z)
            visits+=len(nxt); frontier=nxt
            if not frontier: break
        for node in frontier:
            j=terminal[node]
            if j>i:
                if not conflict(w,words[j]): raise RuntimeError('trie edge replay failed')
                adj[i].append(j+1); adj[j].append(i+1); edges+=1
    return adj,edges,len(children),visits


def exact_edge_count(words:list[str]):
    children,terminal=build_trie(words)
    allowed=[[(d-1)%7,d,(d+1)%7] for d in range(7)]
    edges=0
    for i,w in enumerate(words):
        frontier=[0]
        for ch in w:
            nxt=[]; digs=allowed[ord(ch)-48]
            for node in frontier:
                c=children[node]
                for d in digs:
                    z=c.get(d)
                    if z is not None: nxt.append(z)
            frontier=nxt
            if not frontier: break
        for node in frontier:
            j=terminal[node]
            if j>i:
                if not conflict(w,words[j]): raise RuntimeError('selected trie replay failed')
                edges+=1
    return edges


def common(certificates):
    sets=[load(p) for p in certificates]
    if any(len(s)!=134753 for s in sets): raise RuntimeError([len(s) for s in sets])
    inter=set.intersection(*sets); union=set.union(*sets); diff=sorted(union-inter)
    return sets,inter,union,diff


def export(graph:Path,init:Path,status:Path,certificates):
    sets,inter,union,diff=common(certificates)
    pos={v:i+1 for i,v in enumerate(diff)}
    seed=sorted(sets[0]-inter)
    if any(v not in pos for v in seed): raise RuntimeError('seed position drift')
    adj,edges,nodes,visits=exact_adjacency(diff)
    degree=[len(r) for r in adj]
    graph.parent.mkdir(parents=True,exist_ok=True)
    with graph.open('w',encoding='ascii') as h:
        h.write(f'{len(diff)} {edges} 10\n')
        for row in adj:
            h.write('1')
            if row: h.write(' '+' '.join(map(str,row)))
            h.write('\n')
    init.parent.mkdir(parents=True,exist_ok=True)
    init.write_text(''.join(f'{pos[v]}\n' for v in seed),encoding='ascii')
    hist={}
    for v in diff:
        m=sum((1<<i) for i,s in enumerate(sets) if v in s)
        hist[str(m)]=hist.get(str(m),0)+1
    st={'method':'three-record-union-seeded-chils-export','input_sizes':[len(s) for s in sets],
        'universal_intersection':len(inter),'union_size':len(union),'difference_vertices':len(diff),
        'conflict_edges':edges,'degree_min':min(degree,default=0),'degree_max':max(degree,default=0),
        'degree_sum':sum(degree),'trie_nodes':nodes,'trie_visits':visits,
        'initial_difference_size':len(seed),'initial_total_size':len(inter)+len(seed),
        'membership_histogram':hist}
    status.parent.mkdir(parents=True,exist_ok=True); status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n')
    print(json.dumps(st,sort_keys=True),flush=True)


def replay(solution:Path,output:Path,status:Path,certificates):
    sets,inter,union,diff=common(certificates)
    raw=[int(x) for x in solution.read_text(encoding='ascii').split()]
    if len(raw)!=len(set(raw)) or any(x<1 or x>len(diff) for x in raw): raise RuntimeError('bad CHILS indices')
    kept=[diff[x-1] for x in raw]
    bad=exact_edge_count(kept)
    if bad: raise RuntimeError(f'CHILS selected {bad} conflict edges')
    out=inter|set(kept); score=len(out)
    st={'method':'three-record-union-seeded-chils-replay','candidate':score>=TARGET,
        'universal_intersection':len(inter),'difference_selected':len(kept),'score':score,'target':TARGET}
    status.parent.mkdir(parents=True,exist_ok=True); status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n')
    if score>=TARGET:
        output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps({'points':sorted(out)},separators=(',',':'))+'\n')
    print(json.dumps(st,sort_keys=True),flush=True)


def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    ep=sub.add_parser('export'); ep.add_argument('graph',type=Path);ep.add_argument('init',type=Path);ep.add_argument('status',type=Path);ep.add_argument('certificates',nargs=3,type=Path)
    rp=sub.add_parser('replay');rp.add_argument('solution',type=Path);rp.add_argument('output',type=Path);rp.add_argument('status',type=Path);rp.add_argument('certificates',nargs=3,type=Path)
    a=ap.parse_args()
    if a.cmd=='export': export(a.graph,a.init,a.status,a.certificates)
    else: replay(a.solution,a.output,a.status,a.certificates)

if __name__=='__main__': main()
