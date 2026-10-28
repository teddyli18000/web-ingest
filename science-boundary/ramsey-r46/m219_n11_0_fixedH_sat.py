#!/usr/bin/env python3
"""Exact fixed-H SAT for the two m=219,n11=0 degree sequences.

Consumes representatives produced by m219_n11_0_H_types.py.  Sequence 0 is
12^30 13^6; sequence 1 is 12^31 13^4 14.  H is fixed to one complete induced
high-graph isomorphism representative.  M consists only of degree-12 vertices.
The complete lucky-d12 UNSAT campaign is encoded as the sound excess bound
  sum_{h in N(m) cap H}(deg(h)-12) <= 2
for every m in M.  Exact global degrees and all K4 / independent-6 clauses are
then imposed.  The H-row vectors of M are lexicographically ordered to quotient
M-label symmetry.

The first 630 DIMACS variables are the graph edges in sat_r46.py order.
"""
from __future__ import annotations

import argparse,itertools,json
from pathlib import Path
import degree17_static_sat_v2 as card

N=36
SEQS=({12:30,13:6},{12:31,13:4,14:1})

def edge_variables():
    e=[[0]*N for _ in range(N)];nxt=1
    for i in range(N):
        for j in range(i+1,N):e[i][j]=e[j][i]=nxt;nxt+=1
    return e,nxt-1

def emit(out,cl):out.write(' '.join(map(str,cl))+' 0\n')

def layout(seq):
    nM=SEQS[seq][12];M=list(range(nM));H=list(range(nM,N));return M,H

def targets(seq):
    t=[12]*SEQS[seq][12]+[13]*SEQS[seq].get(13,0)+[14]*SEQS[seq].get(14,0)
    assert len(t)==36 and sum(t)==438
    return t

def fixed_H(edge,rep,seq):
    M,H=layout(seq);rows=rep['adjacency'];assert len(rows)==len(H)
    fixed={}
    for i,j in itertools.combinations(range(len(H)),2):fixed[edge[H[i]][H[j]]]=rows[i][j]=='1'
    return fixed

def simp(vs,edge,fixed,positive):
    out=[]
    for u,v in itertools.combinations(vs,2):
        var=edge[u][v];val=fixed.get(var)
        if val is None:out.append(var if positive else -var)
        elif val if positive else not val:return None
    if not out:raise ValueError('fixed H violates Ramsey constraint')
    return out

def degree_clauses(edge,fixed,t,next_var):
    cls=[]
    for v in range(N):
        free=[];tr=0
        for u in range(N):
            if u==v:continue
            x=edge[u][v];val=fixed.get(x)
            if val is None:free.append(x)
            elif val:tr+=1
        need=t[v]-tr
        if not 0<=need<=len(free):return [[]],next_var
        a,next_var=card.atmost_seq(free,need,next_var);b,next_var=card.atmost_seq([-x for x in free],len(free)-need,next_var)
        cls+=a+b
    return cls,next_var

def add_row_lex(out,edge,M,H,next_var):
    """Sound lex nondecreasing order of M's H-adjacency bit rows."""
    count=0
    for u,v in zip(M,M[1:]):
        pref=list(range(next_var,next_var+len(H)));next_var+=len(H)
        emit(out,[pref[0]]);count+=1
        for i,h in enumerate(H):
            p,x,y=pref[i],edge[u][h],edge[v][h]
            emit(out,[-p,-x,y]);count+=1
            if i+1==len(H):continue
            q=pref[i+1]
            for cl in ([-q,p],[-q,-x,y],[-q,x,-y],[-p,-x,-y,q],[-p,x,y,q]):emit(out,list(cl));count+=1
    return next_var,count

def generate(path,reps,seq,index):
    rep=reps[f'sequence{seq}'][index];assert rep['sequence']==seq and rep['index']==index
    edge,edgevars=edge_variables();fixed=fixed_H(edge,rep,seq);M,H=layout(seq);t=targets(seq)
    fmt='p cnf {vars:10d} {clauses:12d}\n';header=fmt.format(vars=edgevars,clauses=0)
    counts={'fixed_H':0,'M_lex':0,'d12_excess':0,'k4':0,'ind6':0,'degree':0};next_var=edgevars+1
    with path.open('w+',encoding='ascii',buffering=1024*1024) as out:
        out.write(header)
        for x,val in sorted(fixed.items()):emit(out,[x if val else -x]);counts['fixed_H']+=1
        next_var,counts['M_lex']=add_row_lex(out,edge,M,H,next_var)
        # No degree-12 vertex can be lucky. With no d11, high excess <=2.
        if seq==0:
            for m in M:
                xs=[edge[m][h] for h in H]
                cls,next_var=card.atmost_seq(xs,2,next_var)
                for cl in cls:emit(out,cl)
                counts['d12_excess']+=len(cls)
        else:
            h13=H[:-1];h14=H[-1]
            for m in M:
                # weight-2 h14 edge excludes every h13 edge
                for h in h13:emit(out,[-edge[m][h14],-edge[m][h]]);counts['d12_excess']+=1
                cls,next_var=card.atmost_seq([edge[m][h] for h in h13],2,next_var)
                for cl in cls:emit(out,cl)
                counts['d12_excess']+=len(cls)
        for vs in itertools.combinations(range(N),4):
            cl=simp(vs,edge,fixed,False)
            if cl is not None:emit(out,cl);counts['k4']+=1
        for vs in itertools.combinations(range(N),6):
            cl=simp(vs,edge,fixed,True)
            if cl is not None:emit(out,cl);counts['ind6']+=1
        cls,next_var=degree_clauses(edge,fixed,t,next_var)
        for cl in cls:emit(out,cl)
        counts['degree']=len(cls)
        nvars=next_var-1;nclauses=sum(counts.values());final=fmt.format(vars=nvars,clauses=nclauses)
        assert len(final)==len(header);out.seek(0);out.write(final)
    return {'sequence':seq,'H_index':index,'degree_sequence':{str(k):v for k,v in SEQS[seq].items()},
            'H_rep':rep,'variables':nvars,'edge_variables':edgevars,'clauses':nclauses,**counts,'path':str(path)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--types',type=Path,required=True);ap.add_argument('--sequence',type=int,choices=(0,1),required=True);ap.add_argument('--index',type=int,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    reps=json.loads(a.types.read_text());print(json.dumps(generate(a.output,reps,a.sequence,a.index),sort_keys=True))
if __name__=='__main__':main()
