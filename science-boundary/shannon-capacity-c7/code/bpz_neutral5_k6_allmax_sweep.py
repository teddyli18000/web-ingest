#!/usr/bin/env python3
"""Exact closure of the simple outside-neutral-k5 x irreducible-k6 product family.

Consumes the neutral5 owner/killer audit only to identify the 30 owner sets that
admit at least one outside-only independent 5-set.  For each such owner set C5
we reconstruct the COMPLETE Y_C5 pool, enumerate EVERY independent outside-only
5-set, pair each with each of the four fixed irreducible k6 outside 7-sets, both
factor orders, and all 18 BPZ terminal baselines.  The 35 product points replace
30 core points, so terminal loss <=4 gives a verified-score candidate >=134754.

This is exhaustive for the simple Cartesian-product family using any maximum
outside 5-set of those 30 neutral supports and the four frozen k6 witnesses.
"""
from __future__ import annotations
import argparse,itertools,json
from pathlib import Path
from bpz_joint_row_defects_maxsat import load_geometry,terminal_periphery
from bpz_amplify_row_defects import PINNED_DEFECTS

def conflict5(a,b):
    if a==b:return True
    for _ in range(5):
        x,y=a%7,b%7;a//=7;b//=7
        if (x-y)%7 not in (0,1,6):return False
    return True

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('audit_json',type=Path);ap.add_argument('output',type=Path);ap.add_argument('certificate',type=Path);a=ap.parse_args()
    _base,ring,B,fam=load_geometry(a.tan_root.resolve());B=set(B);audit=json.loads(a.audit_json.read_text());cases=[r for r in audit['rows'] if int(r['min_owner_intersection'])==0]
    if len(cases)!=30:raise RuntimeError(('outside case drift',len(cases)))
    k6=[d for d in PINNED_DEFECTS if len(d['owners'])==6]
    if len(k6)!=4:raise RuntimeError(('k6',len(k6)))
    # Exact support of every 5D vertex against B.
    supp={z:frozenset(ring.NB[z]&B) for z in range(ring.n)}
    terminals=[]
    for q in ('O','H','V'):
      for r in ('O','H','V'):
       for o in (0,1):
        P=terminal_periphery(fam,q,r,o);by={}
        for p in P:by.setdefault(p[0],[]).append(p)
        terminals.append((q,r,o,P,by,set(by)))
    best=None; checked_products=0; maxsets_total=0; per_case=[]; hits=[]
    for rec in cases:
        C5=frozenset(map(int,rec['owners']))
        pool=sorted(z for z in range(ring.n) if z not in B and supp[z] and supp[z]<=C5)
        maxsets=[]
        for comb in itertools.combinations(pool,5):
            if all(not conflict5(comb[i],comb[j]) for i in range(5) for j in range(i+1,5)):
                maxsets.append(comb)
        if not maxsets:raise RuntimeError(('audit outside witness missing',sorted(C5),len(pool)))
        maxsets_total+=len(maxsets);casebest=10**9
        for Y5 in maxsets:
          for kd in k6:
            C6=frozenset(map(int,kd['owners']));Y6=tuple(map(int,kd['additions']))
            for order in (0,1):
                selected=(tuple((x,y) for x in Y5 for y in Y6) if order==0 else tuple((y,x) for x in Y5 for y in Y6))
                deleted_core=({(x,y) for x in C5 for y in C6} if order==0 else {(y,x) for x in C5 for y in C6})
                if len(selected)!=35 or len(set(selected))!=35 or len(deleted_core)!=30:raise RuntimeError('shape')
                # Factor independence proves product independence; replay once anyway.
                for i,p in enumerate(selected):
                    for z in selected[i+1:]:
                        if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(('product conflict',p,z))
                for q,r,o,P,by,fk in terminals:
                    loss=set()
                    for x,y in selected:
                        for u in ring.NB[x]&fk:
                            for p in by[u]:
                                if p[1] in ring.NB[y]:loss.add(p)
                    checked_products+=1;L=len(loss);casebest=min(casebest,L);score=134758-L
                    row={'neutral_owners':sorted(C5),'neutral_set':list(Y5),'k6':kd['name'],'order':order,'q':q,'r':r,'terminal_orientation':o,'terminal_loss':L,'score':score}
                    if best is None or (score,-L)> (best['score'],-best['terminal_loss']):best=row|{'selected':selected,'deleted_core':sorted(deleted_core),'lost':sorted(loss)}
                    if score>=134754:hits.append(row)
        per_case.append({'owners':sorted(C5),'pool_size':len(pool),'outside_independent5_count':len(maxsets),'best_terminal_loss':casebest})
    materialized=False
    if best and best['score']>=134754:
        P=terminal_periphery(fam,best['q'],best['r'],best['terminal_orientation']);base={(x,y) for x in B for y in B}|P;deleted=set(map(tuple,best['deleted_core']))|set(map(tuple,best['lost']));selected=set(map(tuple,best['selected']));cand=(base-deleted)|selected
        if len(cand)!=best['score']:raise RuntimeError(('score replay',len(cand),best['score']))
        cv=list(cand)
        for i,p in enumerate(cv):
            for z in cv[i+1:]:
                if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(('certificate conflict',p,z))
        def enc(p):return ''.join(str(d) for d in ring.decode(p[0])+ring.decode(p[1]))
        pts=sorted(enc(p) for p in cand);a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');materialized=True
    public_best=None
    if best:public_best={k:v for k,v in best.items() if k not in ('selected','deleted_core','lost')}
    out={'method':'exact-all-outside-neutral5-maxsets-x-k6-product-sweep','neutral_owner_sets':len(cases),'outside_independent5_total':maxsets_total,'scenarios_checked':checked_products,'hit_count':len(hits),'best':public_best,'per_case':per_case,'hits':hits[:100],'candidate_materialized':materialized,'candidate_score':best['score'] if materialized else None}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','hits')},sort_keys=True));print('best_cases',json.dumps(sorted(per_case,key=lambda x:x['best_terminal_loss'])[:10],sort_keys=True))
if __name__=='__main__':main()
