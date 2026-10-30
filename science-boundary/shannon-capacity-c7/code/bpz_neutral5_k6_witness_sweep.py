#!/usr/bin/env python3
"""Cheap exact replay of audited outside-only neutral-k5 witnesses x k6 +1 witnesses.

For an outside-only independent 5-set Y5 supported by five deleted B owners C5
and one of the four irreducible independent 7-sets Y6 supported by six deleted
owners C6, Y5 x Y6 is an independent 35-set in C7^10.  Deleting C5 x C6 costs
30 core points, so the construction beats 134753 iff its distinct terminal
periphery blockers are at most four.  This script exhaustively checks the one
lexicographically audited witness stored for every outside-only neutral5 case,
all four k6 defects, both factor orders, and all 18 public terminal baselines.

No SAT is needed.  Any hit is structurally replayed and materialized for the
upstream Few Shots verifier.  A miss excludes only these audited witnesses, not
all maximum 5-sets of each neutral factor.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from bpz_joint_row_defects_maxsat import load_geometry,terminal_periphery
from bpz_amplify_row_defects import PINNED_DEFECTS

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('audit_json',type=Path);ap.add_argument('output',type=Path);ap.add_argument('certificate',type=Path);a=ap.parse_args()
    _base,ring,B,fam=load_geometry(a.tan_root.resolve());B=set(B);audit=json.loads(a.audit_json.read_text());rows=[r for r in audit.get('rows',[]) if int(r['min_owner_intersection'])==0]
    k6=[d for d in PINNED_DEFECTS if len(d['owners'])==6]
    if len(k6)!=4:raise RuntimeError(('k6 defect count',len(k6)))
    terminals=[]
    for q in ('O','H','V'):
      for r in ('O','H','V'):
       for o in (0,1):
        P=terminal_periphery(fam,q,r,o);by={}
        for p in P:by.setdefault(p[0],[]).append(p)
        terminals.append((q,r,o,P,by,set(by)))
    best=None;checked=0;hits=[]
    for nr in rows:
        C5=set(map(int,nr['owners']));Y5=list(map(int,nr['witness']))
        if len(C5)!=5 or len(Y5)!=5 or any(y in B for y in Y5):raise RuntimeError(('neutral witness shape',nr))
        for kd in k6:
            C6=set(map(int,kd['owners']));Y6=list(map(int,kd['additions']))
            if len(C6)!=6 or len(Y6)!=7 or any(y in B for y in Y6):raise RuntimeError(('k6 witness shape',kd))
            for order in (0,1):
                selected=([(x,y) for x in Y5 for y in Y6] if order==0 else [(y,x) for x in Y5 for y in Y6])
                deleted_core=({(x,y) for x in C5 for y in C6} if order==0 else {(y,x) for x in C5 for y in C6})
                if len(selected)!=35 or len(deleted_core)!=30:raise RuntimeError('product size')
                # structural independence replay
                for i,p in enumerate(selected):
                    for z in selected[i+1:]:
                        if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(('product conflict',p,z))
                for q,r,o,P,by,fk in terminals:
                    loss=set()
                    for x,y in selected:
                        for u in ring.NB[x]&fk:
                            for p in by[u]:
                                if p[1] in ring.NB[y]:loss.add(p)
                    checked+=1;score=134753-30+35-len(loss)
                    rec={'neutral_owners':sorted(C5),'neutral_killers':nr['min_killer_colors_given_owner_min'],'k6':kd['name'],'order':order,'q':q,'r':r,'terminal_orientation':o,'terminal_loss':len(loss),'score':score}
                    if best is None or (rec['score'], -rec['terminal_loss'])>(best['score'],-best['terminal_loss']):best=rec|{'selected':selected,'deleted_core':sorted(deleted_core),'lost':sorted(loss)}
                    if score>=134754:hits.append(rec)
    materialized=False
    if best and best['score']>=134754:
        P=terminal_periphery(fam,best['q'],best['r'],best['terminal_orientation']);base={(x,y) for x in B for y in B}|P;deleted=set(map(tuple,best['deleted_core']))|set(map(tuple,best['lost']));selected=set(map(tuple,best['selected']));cand=(base-deleted)|selected
        if len(cand)!=best['score']:raise RuntimeError(('materialized score',len(cand),best['score']))
        cv=list(cand)
        for i,p in enumerate(cv):
            for z in cv[i+1:]:
                if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(('materialized conflict',p,z))
        def enc(p):return ''.join(str(d) for d in ring.decode(p[0])+ring.decode(p[1]))
        pts=sorted(enc(p) for p in cand);a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');materialized=True
    public_best=None
    if best:
        public_best={k:v for k,v in best.items() if k not in ('selected','deleted_core','lost')}
    out={'method':'exact-audited-neutral5-k6-witness-product-sweep','outside_neutral_cases':len(rows),'k6_defects':len(k6),'scenarios_checked':checked,'hit_count':len(hits),'best':public_best,'hits':hits[:100],'candidate_materialized':materialized,'candidate_score':best['score'] if materialized else None}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='hits'},sort_keys=True))
if __name__=='__main__':main()
