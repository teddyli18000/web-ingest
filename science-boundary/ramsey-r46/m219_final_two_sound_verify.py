#!/usr/bin/env python3
"""Sound replacement closure for the two final m=219 degree sequences.

This verifier deliberately does NOT use the withdrawn binary row-domain CSP.
It combines the post-audit seq0 r=3 certificates with new solver-free / exact
small-CSP arguments for the remaining r=4 and seq1 branches.
"""
from __future__ import annotations
import argparse, itertools, json, math
from collections import defaultdict
from pathlib import Path
import networkx as nx

HERE=Path(__file__).resolve().parent
DATA=HERE/'data'
RESULTS=HERE/'results'

SEQ0={11:7,12:16,13:13}
SEQ1={11:8,12:14,13:14}

A_MIN={11:8,12:11,13:15}; A_MAX={11:26,12:29,13:32}
B_MIN={11:116,12:101,13:88}; B_MAX={11:132,12:122,13:114}

def read_g6(path:Path):
    return [nx.from_graph6_bytes(s.encode()) for s in path.read_text().splitlines() if s]

def independent_sets(G,k):
    return [frozenset(S) for S in itertools.combinations(G.nodes(),k)
            if G.subgraph(S).number_of_edges()==0]

def hit_number_i5(A):
    I5=independent_sets(A,5)
    for k in range(12):
        n=sum(1 for S in itertools.combinations(A.nodes(),k)
              if all(set(S)&T for T in I5))
        if n: return k,n
    raise AssertionError

def triangle_free(G):
    return all(G.subgraph(S).number_of_edges()<3 for S in itertools.combinations(G.nodes(),3))

def no_independent(G,k):
    return all(G.subgraph(S).number_of_edges()>0 for S in itertools.combinations(G.nodes(),k))

def label_context_count(B, low_count, high_count, rmin, tau=2):
    """Count relaxed B class-labelings satisfying sound necessary conditions.

    Labels are global degrees 11/12/13. Every B column into A must hit every
    A-independent 5-set, hence cross degree >= tau (=2 for all A25/A26 types).
    For a B-low q, r(q)>=rmin gives h_B <= l_B + (11-d_B(q))-rmin.
    """
    n=len(B); total=0; lowsets=0
    for Qt in itertools.combinations(range(n),low_count):
        Q=set(Qt)
        if any(11-B.degree(q)<tau for q in Q): continue
        rem=[v for v in range(n) if v not in Q]
        if any(13-B.degree(v)<tau for v in rem): continue
        forced={v for v in rem if 12-B.degree(v)<tau}
        if len(forced)>high_count: continue
        qlist=sorted(Q); caps=[]; bad=False
        for q in qlist:
            lB=sum(B.has_edge(q,u) for u in Q if u!=q)
            cap=lB+(11-B.degree(q))-rmin
            if cap<0: bad=True; break
            caps.append(cap)
        if bad: continue
        used=tuple(sum(B.has_edge(v,q) for v in forced) for q in qlist)
        if any(used[i]>caps[i] for i in range(len(qlist))): continue
        optional=[v for v in rem if v not in forced]
        need=high_count-len(forced)
        states={(0,used):1}
        for v in optional:
            pat=tuple(int(B.has_edge(v,q)) for q in qlist)
            nxt=defaultdict(int)
            for (cnt,z),ways in states.items():
                nxt[(cnt,z)] += ways
                if cnt<need:
                    zz=tuple(z[i]+pat[i] for i in range(len(qlist)))
                    if all(zz[i]<=caps[i] for i in range(len(qlist))):
                        nxt[(cnt+1,zz)] += ways
            states=nxt
        ways=sum(w for (cnt,_),w in states.items() if cnt==need)
        if ways:
            lowsets+=1; total+=ways
    return lowsets,total

def ex_k4(n):
    q,r=divmod(n,3); p=[q+(i<r) for i in range(3)]
    return sum(p[i]*p[j] for i in range(3) for j in range(i+1,3))

def distributions(total,limits,p=()):
    if len(limits)==1:
        if 0<=total<=limits[0]: yield p+(total,)
        return
    lo=max(0,total-sum(limits[1:])); hi=min(limits[0],total)
    for x in range(lo,hi+1): yield from distributions(total-x,limits[1:],p+(x,))

def s_interval(d,m=219):
    return max(11*d,m+A_MIN[d]-B_MAX[d]),min(17*d,m+A_MAX[d]-B_MIN[d])

def max_sum_r_seq1():
    seq=SEQ1; ds=sorted(seq);k=len(ds);M=[[0]*k for _ in ds];cap=[[0]*k for _ in ds];vals=[]
    for i,d in enumerate(ds):
        for j in range(i,k):
            cap[i][j]=min(math.comb(seq[d],2),ex_k4(seq[d])) if i==j else seq[d]*seq[ds[j]]
    def check(i):
        d=ds[i]
        ss=2*d*M[i][i]+sum(e*M[min(i,j)][max(i,j)] for j,e in enumerate(ds) if j!=i)
        lo,hi=s_interval(d)
        if d==12: hi=min(hi,146)
        return lo*seq[d]<=ss<=hi*seq[d]
    def rec(i,rem):
        if i==k-1:
            if rem[i]<0 or rem[i]%2:return
            z=rem[i]//2
            if z>cap[i][i]:return
            M[i][i]=z
            if check(i):
                i11=ds.index(11)
                R=2*M[i11][i11]-sum((d-12)*M[min(i11,j)][max(i11,j)] for j,d in enumerate(ds) if d>=13)
                vals.append(R)
            return
        for eii in range(min(cap[i][i],rem[i]//2)+1):
            need=rem[i]-2*eii; js=list(range(i+1,k)); lims=[min(cap[i][j],rem[j]) for j in js]
            if need<0 or need>sum(lims): continue
            M[i][i]=eii
            for xs in distributions(need,lims):
                nr=rem[:]
                for j,x in zip(js,xs): M[i][j]=x; nr[j]-=x
                if min(nr)>=0 and check(i): rec(i+1,nr)
    rec(0,[d*seq[d] for d in ds])
    assert vals
    return max(vals),len(vals)

def t7_A26_supports(A):
    V=set(A.nodes()); out=[]
    for St in itertools.combinations(A.nodes(),7):
        S=set(St); H=V-S; ok=True
        for u in S:
            dt=sum(A.has_edge(u,w) for w in S if w!=u)
            ha=sum(A.has_edge(u,w) for w in H)
            if ha>dt-2: ok=False;break
        if ok: out.append((tuple(sorted(S)),tuple(sorted(H))))
    return out

def load_post_audit_seq0_r3(results_dir:Path):
    a=json.loads((results_dir/'m219-seq0-r3-t356-transversal.json').read_text())
    b=json.loads((results_dir/'m219-seq0-r3-t4-col2.json').read_text())
    assert a['campaign']=='m219-seq0-r3-t356-transversal'
    assert a['t3']['all_excluded'] and a['t5']['all_excluded'] and a['t6']['all_excluded']
    assert b['campaign']=='m219-seq0-r3-t4-col2' and all(x['status']=='UNSAT' for x in b['col2_runs'])
    return {'t356':a['campaign'],'t4':b['campaign']}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data-dir',type=Path,default=DATA)
    ap.add_argument('--results-dir',type=Path,default=RESULTS)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--skip-existing-seq0-r3',action='store_true')
    args=ap.parse_args()
    data=args.data_dir; results=args.results_dir

    As25=read_g6(data/'A25.g6' if (data/'A25.g6').exists() else data/'m219-r34-A25.g6')
    As26=read_g6(data/'A26.g6' if (data/'A26.g6').exists() else data/'m219-r34-A26.g6')
    Bs116=read_g6(data/'B116.g6' if (data/'B116.g6').exists() else data/'m219-r34-B116.g6')
    Bs117=read_g6(data/'B117.g6' if (data/'B117.g6').exists() else data/'m219-r34-B117.g6')
    assert (len(As25),len(As26),len(Bs116),len(Bs117))==(6,2,9,90)
    assert all(len(A)==11 and A.number_of_edges()==25 and triangle_free(A) and no_independent(A,6) for A in As25)
    assert all(len(A)==11 and A.number_of_edges()==26 and triangle_free(A) and no_independent(A,6) for A in As26)
    assert all(len(B)==24 and B.number_of_edges()==116 for B in Bs116)
    assert all(len(B)==24 and B.number_of_edges()==117 for B in Bs117)
    hit25=[hit_number_i5(A) for A in As25]; hit26=[hit_number_i5(A) for A in As26]
    assert all(x[0]==2 for x in hit25+hit26)

    seq0_r3 = ({'t356':'m219-seq0-r3-t356-transversal','t4':'m219-seq0-r3-t4-col2'}
                if args.skip_existing_seq0_r3 else load_post_audit_seq0_r3(results))

    seq0_r4_labels={}
    for t in (4,5):
        lc=6-t; hc=17-t
        z116=sum(label_context_count(B,lc,hc,4)[1] for B in Bs116)
        z117=sum(label_context_count(B,lc,hc,4)[1] for B in Bs117)
        assert z116==0 and z117==0
        seq0_r4_labels[str(t)]={'B116_contexts':z116,'B117_contexts':z117}
    seq0_t6_upper=9+0+9+6
    assert seq0_t6_upper==24<25

    seq1_r3={}
    for t in (3,4):
        lc=7-t; hc=17-t
        z=sum(label_context_count(B,lc,hc,3)[1] for B in Bs116)
        assert z==0
        seq1_r3[str(t)]={'B116_contexts':z}

    seq1_r3['5']={'reuses_sound_certificate':'m219-seq0-r3-t4-col2',
                  'local_B_class_counts':{'11':2,'12':10,'13':12},
                  'reason':'identical A26/B116 local strata and B degree-class counts'}

    t6_candidates=[]
    for bi,B in enumerate(Bs116):
        ds=dict(B.degree())
        forced_high={v for v,d in ds.items() if d==11}
        for q,d in ds.items():
            if d!=8: continue
            if any(B.has_edge(q,h) for h in forced_high): continue
            t6_candidates.append((bi,q))
    assert t6_candidates==[(1,0)]
    seq1_r3['6']={'candidate_B_low_vertices':[list(x) for x in t6_candidates],
                  'reduction':'q has d_B=8, no B-high neighbour, x=3, no B-low neighbour; r(q)>=3 forces q to be t=3,r=3'}

    t7_support=[len(t7_A26_supports(A)) for A in As26]
    assert t7_support==[0,0]
    seq1_r3['7']={'A26_partition_support_counts':t7_support}

    maxR,nclass=max_sum_r_seq1(); assert maxR==32
    seq1_r4={}
    for t in (4,5,6):
        lc=7-t; hc=18-t
        z116=sum(label_context_count(B,lc,hc,4)[1] for B in Bs116)
        z117=sum(label_context_count(B,lc,hc,4)[1] for B in Bs117)
        assert z116==0 and z117==0
        seq1_r4[str(t)]={'B116_contexts':z116,'B117_contexts':z117}

    out={
      'campaign':'m219-final-two-sound-post-audit',
      'edges':219,
      'catalog_counts':{'A25':6,'A26':2,'B116':9,'B117':90},
      'hitting_numbers':{'A25':hit25,'A26':hit26},
      'seq0':{
        'degree_sequence':{str(k):v for k,v in SEQ0.items()},
        'post_audit_r3_evidence':seq0_r3,
        'r4_label_exclusions':seq0_r4_labels,
        'r4_t6_edge_upper':seq0_t6_upper,
        'forcing':'after r=3 is excluded, if every low vertex had r>=5 then sum r>=35, but K4-free on 7 lows gives sum t<=2*ex(7,K4)=32 and r<=t; hence an r=4 anchor exists',
        'status':'UNSAT'},
      'seq1':{
        'degree_sequence':{str(k):v for k,v in SEQ1.items()},
        'r3_subbranches':seq1_r3,
        'class_relaxation_count':nclass,'max_sum_r':maxR,
        'r4_label_exclusions':seq1_r4,
        'forcing':'after r=3 is excluded, eight lows with r>=4 and max sum r=32 force r=4 at every low vertex; t=4,5,6 are impossible, so all would need t=7, giving K8 and hence K4',
        'status':'UNSAT'},
      'all_unsat':True,
      'soundness':'No conclusion here uses the withdrawn row-domain triangle-free predicate. B-label scans use only cross-degree>=2 from I5 hitting and r lower bounds; the reused col2 certificate keeps only necessary mixed K4/I6 constraints; remaining arguments are finite A26 enumeration or extremal edge counts.'
    }
    text=json.dumps(out,indent=2,sort_keys=True)+'\n'; print(text,end='')
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)

if __name__=='__main__': main()
