#!/usr/bin/env python3
from __future__ import annotations
import itertools, json
import networkx as nx

DEGREES=tuple(range(11,18))
A_MIN={11:8,12:11,13:15,14:20,15:25,16:32,17:40}
A_MAX={11:26,12:29,13:32,14:35,15:37,16:40,17:42}
B_MIN={11:116,12:101,13:88,14:77,15:68,16:57,17:50}
B_MAX={11:132,12:122,13:114,14:107,15:100,16:92,17:85}

def compositions(total,k,prefix=()):
    if k==1:
        yield prefix+(total,); return
    for x in range(total+1):
        yield from compositions(total-x,k-1,prefix+(x,))

def s_interval(d,m=220):
    return max(11*d,m+A_MIN[d]-B_MAX[d]),min(17*d,m+A_MAX[d]-B_MIN[d])

def aggregate(m=220):
    out=[]
    for ns in compositions(36,len(DEGREES)):
        if sum(n*d for n,d in zip(ns,DEGREES))!=2*m: continue
        s2=sum(n*d*d for n,d in zip(ns,DEGREES)); lo=hi=0
        for n,d in zip(ns,DEGREES):
            a,b=s_interval(d,m)
            if d==12: b=min(b,147)
            lo+=n*a; hi+=n*b
        if lo<=s2<=hi: out.append(ns)
    return out

def n11_6_sequences():
    rows=[]
    for ns in aggregate():
        if ns[0]!=6: continue
        rows.append({d:n for n,d in zip(ns,DEGREES) if n})
    assert len(rows)==14
    return rows

def simple_R_upper(seq):
    s2=sum(n*d*d for d,n in seq.items())
    other=0
    for d,n in seq.items():
        if d==11: continue
        hi=s_interval(d)[1]
        if d==12: hi=min(hi,147)
        other += n*hi
    low_min=s2-other
    return 132*seq[11]-low_min

def boundary(R):
    if R==22: g6,r='Ep~o',[4,3,4,3,4,4]
    elif R==24: g6,r='EznW',[4,4,4,4,4,4]
    else: raise ValueError(R)
    G=nx.from_graph6_bytes(g6.encode())
    ds=[G.degree(i) for i in range(6)]
    assert ds==r
    e11=G.number_of_edges(); e1112=66-2*e11
    return {'R':R,'g6':g6,'r':r,'e11_11':e11,'e11_12':e1112}

def enum_seq6(R):
    low12=boundary(R)['e11_12']; out=[]
    for f in range(2):
        for b in range(15):
            d=14-b-f
            if not 0<=d<=9: continue
            for c in range(16):
                e=15-c-f
                if not 0<=e<=9: continue
                for x in range(28):
                    a=117-2*x-d-e
                    if a<0: continue
                    rem=228-low12-a-b-c
                    if rem<0 or rem%2: continue
                    p=rem//2
                    S12=11*low12+24*p+13*a+14*b+15*c
                    S13=26*x+12*a+14*d+15*e
                    S14=12*b+13*d+15*f
                    S15=12*c+13*e+14*f
                    if not (132*19<=S12<=147*19): continue
                    if not (143*9<=S13<=164*9): continue
                    if not (154<=S14<=178): continue
                    if not (165<=S15<=189): continue
                    out.append({'e12_12':p,'e12_13':a,'e12_14':b,'e12_15':c,
                                'e13_13':x,'e13_14':d,'e13_15':e,'e14_15':f,
                                'S12':S12,'S13':S13,'S14':S14,'S15':S15})
    return out

def enum_seq8(R):
    low12=boundary(R)['e11_12']; out=[]
    for y in range(6):
        for d in range(25):
            b=56-2*y-d
            if b<0: continue
            for x in range(13):
                a=78-2*x-d
                if a<0: continue
                rem=240-low12-a-b
                if rem<0 or rem%2: continue
                p=rem//2
                S12=11*low12+24*p+13*a+14*b
                S13=26*x+12*a+14*d
                S14=28*y+12*b+13*d
                if not (132*20<=S12<=147*20): continue
                if not (143*6<=S13<=164*6): continue
                if not (154*4<=S14<=178*4): continue
                out.append({'e12_12':p,'e12_13':a,'e12_14':b,
                            'e13_13':x,'e13_14':d,'e14_14':y,
                            'S12':S12,'S13':S13,'S14':S14})
    return out

def seq8_survival_reason(m):
    x,d,y=m['e13_13'],m['e13_14'],m['e14_14']
    if x==0:
        return False,'six degree-13 vertices would be an independent 6-set'
    if y==5 and d>18:
        return False,'K4-e on the four degree-14 vertices lets each degree-13 vertex meet at most 3 of them, so e13_14<=18'
    if y==4 and d>=23 and x>=1:
        return False,'with at most one missing 13-14 incidence, endpoints of a 13-13 edge have >=3 common degree-14 neighbours; every 3-subset of a 4-edge graph on 4 vertices contains an edge, forming K4'
    return True,'survives these necessary K4/I6 filters'

def main():
    seqs=n11_6_sequences()
    ubs=[simple_R_upper(s) for s in seqs]
    killed=[{'index_1based':i+1,'degree_sequence':s,'R_upper':u}
            for i,(s,u) in enumerate(zip(seqs,ubs)) if u<22]
    assert [x['index_1based'] for x in killed]==[7,9,10,11,12,13,14]

    s6=seqs[5]; assert s6=={11:6,12:19,13:9,14:1,15:1}
    s6r24=enum_seq6(24); assert s6r24==[]
    s6r22=enum_seq6(22); assert len(s6r22)==6
    assert set(x['S12'] for x in s6r22)=={2792,2793}
    s6_extreme_min=18

    s8=seqs[7]; assert s8=={11:6,12:20,13:6,14:4}
    s8r24=enum_seq8(24); assert len(s8r24)==2
    r24=[]
    for m in s8r24:
        ok,reason=seq8_survival_reason(m); assert not ok
        r24.append({**m,'status':'UNSAT','reason':reason})
    s8r22=enum_seq8(22); assert len(s8r22)==7
    r22=[]
    for m in s8r22:
        ok,reason=seq8_survival_reason(m)
        r22.append({**m,'status':'SURVIVES' if ok else 'UNSAT','reason':reason})
    survivors=[x for x in r22 if x['status']=='SURVIVES']
    assert len(survivors)==2
    assert all(x['S12']==2940 and x['S13']==984 for x in survivors)
    assert s_interval(13)==(143,164) and A_MAX[13]==32 and B_MIN[13]==88

    out={
      'campaign':'m220-n11-6-class-boundary-post-audit',
      'edges':220,'n11':6,
      'universal_inputs':{'R_lower':22,'R23_impossible':True,
                          'R22_boundary':boundary(22),'R24_boundary':boundary(24)},
      'degree_sequences':[
          {'index_1based':i+1,'degree_sequence':s,'simple_R_upper':ubs[i]}
          for i,s in enumerate(seqs)],
      'simple_bound_exclusions':killed,
      'remaining_after_simple_bound':[i+1 for i,u in enumerate(ubs) if u>=22],
      'seq6':{'degree_sequence':s6,'R24_class_matrix_count':0,
              'R22_class_matrix_count':len(s6r22),'R22_matrices':s6r22,
              'forced_min_d12_vertices_with_S147':s6_extreme_min,
              'interpretation':'R=24 is impossible already at integer class-edge level. At R=22 only six class matrices remain and at least 18/19 degree-12 vertices lie in the S=147 extreme local stratum.'},
      'seq8':{'degree_sequence':s8,'R24':r24,'R22':r22,
              'R22_survivor_count':len(survivors),'R22_survivors':survivors,
              'forced_local_strata_in_R22_survivors':{
                  'all_20_degree12_vertices':'S=147, hence (A28,B101) or (A29,B102)',
                  'all_6_degree13_vertices':'S=164, hence uniquely (A32,B88)'},
              'interpretation':'R=24 is fully excluded by K4/I6. R=22 has exactly two class-edge patterns after sound K4/I6 filtering.'},
      'soundness':'Uses only endpoint edge extrema, degree-class handshakes, per-degree S caps, the post-audit universal n11=6 low-graph boundary, and direct K4/I6 necessities. No withdrawn row-domain predicate and no SAT/heuristic claim is used.'
    }
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__': main()
