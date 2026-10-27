#!/usr/bin/env python3
import argparse,json
from itertools import combinations
from pathlib import Path
import generalized9 as g

TARGET=134770

def enumerate_states(r,digits,supports):
    rset=set(r); one={}; two={}
    for v,sm in enumerate(supports):
        if v in rset: continue
        bc=sm.bit_count()
        if bc==1:
            i=(sm&-sm).bit_length()-1; one.setdefault(i,[]).append(v)
        elif bc==2:
            xs=[i for i in range(g.R_SIZE) if (sm>>i)&1]
            two.setdefault(tuple(xs),[]).append(v)
    ownerpairs=set(two)
    os=sorted(one)
    for x,y in combinations(os,2): ownerpairs.add((x,y))
    seen=set(); out=[]
    for a,b in sorted(ownerpairs):
        cand=sorted(set(one.get(a,[])+one.get(b,[])+two.get((a,b),[])))
        for u,v in combinations(cand,2):
            if g.conflict(u,v,digits): continue
            st=list(r); st[a]=u; st[b]=v
            key=tuple(sorted(st))
            if key in seen: continue
            seen.add(key); out.append((st,(a,b),(u,v)))
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('r367',type=Path); ap.add_argument('baseline',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U)); r0=g.load_r(args.r367); xset=g.make_x(r0,digits)
    base_supports,_=g.support_masks(r0,digits)
    states=enumerate_states(r0,digits,base_supports)
    print('neutral2 states',len(states),flush=True)
    tested_states=0; tested_sat=0; best=None
    for si,(r,rem,add) in enumerate(states,1):
        if len(set(r))!=g.R_SIZE: continue
        supports,_=g.support_masks(r,digits); rset=set(r); owners={}
        for v,sm in enumerate(supports):
            if v in rset or sm.bit_count()!=1: continue
            i=(sm&-sm).bit_length()-1; owners.setdefault(i,[]).append(v)
        if len(owners)<9: continue
        tested_states+=1
        combos=[]
        for k9 in combinations(sorted(owners),9):
            km=sum(1<<i for i in k9); safe=sum(1 for sm in supports if sm & ~km == 0); combos.append((safe,k9))
        combos.sort(reverse=True)
        print('state',si,'rem',rem,'add',add,'centers',len(owners),'combos',len(combos),'best_safe',combos[0][0],flush=True)
        for safe,k9 in combos:
            tested_sat+=1
            model,stats=g.solve_structure(k9,9,r,xset,digits,supports,want_model=True)
            rec={'state':si,'remove':list(rem),'add':list(add),'centers':len(owners),'safe':safe,'k9':list(k9),'stats':stats}
            if best is None or (stats['active_x'], -safe) < (best['stats']['active_x'], -best['safe']): best=rec
            if model is None: continue
            cand=g.build_candidate(k9,model,r,xset,digits)
            if len(cand)!=TARGET: raise RuntimeError(f'wrong score {len(cand)}')
            baseline={int(p,7) for p in json.loads(args.baseline.read_text())['points']}
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps({'points':[g.dec10(v) for v in sorted(cand)]},separators=(',',':'))+'\n')
            status={'candidate':True,'score':len(cand),'method':'all-neutral2-generalized-sat','states_total':len(states),'tested_states':tested_states,'tested_sat':tested_sat,'state_index':si,'neutral_remove_indices':list(rem),'neutral_add':list(add),'private_center_count':len(owners),'selected_indices':list(k9),'selected_centers':[r[i] for i in k9],'sat_stats':stats,'removed_vs_baseline':len(baseline-cand),'added_vs_baseline':len(cand-baseline)}
            args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(status,sort_keys=True),flush=True); return
    status={'candidate':False,'score':134753,'method':'all-neutral2-generalized-sat','states_total':len(states),'tested_states':tested_states,'tested_sat':tested_sat,'best_unsat':best}
    args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__': main()
