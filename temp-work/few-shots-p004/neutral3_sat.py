#!/usr/bin/env python3
import argparse,json
from itertools import combinations
from pathlib import Path
import generalized9 as g

BASELINE=134753

def score_for(k): return (g.R_SIZE-k)**2+2*k*g.R_SIZE

def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('states',type=Path);ap.add_argument('baseline',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args()
    result=json.loads(args.states.read_text()); tops=result.get('top',[])
    digits=tuple(g.dec5(v) for v in range(g.U)); original=g.load_r(args.r367); xset=g.make_x(original,digits)
    baseline_ids={int(p,7) for p in json.loads(args.baseline.read_text())['points']}
    tests=0; best_unsat=None
    for rank,rec in enumerate(tops,1):
        r=rec['state'];
        if len(r)!=g.R_SIZE or len(set(r))!=g.R_SIZE: raise RuntimeError('bad parent state')
        supports,_=g.support_masks(r,digits); rset=set(r); owners={}
        for v,sm in enumerate(supports):
            if v in rset or sm.bit_count()!=1: continue
            i=(sm&-sm).bit_length()-1; owners.setdefault(i,[]).append(v)
        c=len(owners)
        if c<9: continue
        owner_ids=sorted(owners)
        for k in range(c,8,-1):
            combos=[]
            for ks in combinations(owner_ids,k):
                km=sum(1<<i for i in ks); safe=sum(1 for sm in supports if sm & ~km == 0); combos.append((safe,ks))
            combos.sort(reverse=True)
            for safe,ks in combos:
                tests+=1
                print('SAT try',json.dumps({'rank':rank,'overlap':rec['overlap'],'centers':c,'k':k,'safe':safe,'test':tests}),flush=True)
                model,stats=g.solve_structure(ks,k,r,xset,digits,supports,want_model=True)
                u={'rank':rank,'overlap':rec['overlap'],'centers':c,'k':k,'safe':safe,'stats':stats,'remove_indices':rec['remove_indices'],'add':rec['add']}
                if best_unsat is None or (stats['active_x'],-safe)<(best_unsat['stats']['active_x'],-best_unsat['safe']): best_unsat=u
                if model is None: continue
                cand=g.build_candidate(ks,model,r,xset,digits); target=score_for(k)
                if len(cand)!=target: raise RuntimeError(f'wrong score {len(cand)} != {target}')
                if target<=BASELINE: continue
                args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':[g.dec10(v) for v in sorted(cand)]},separators=(',',':'))+'\n')
                status={'candidate':True,'score':target,'method':'neutral3-generalized-sat','parent_rank':rank,'parent_overlap':rec['overlap'],'parent_centers':c,'parent_remove_indices':rec['remove_indices'],'parent_add':rec['add'],'k':k,'selected_indices':list(ks),'selected_centers':[r[i] for i in ks],'sat_stats':stats,'tests':tests,'removed_vs_baseline':len(baseline_ids-cand),'added_vs_baseline':len(cand-baseline_ids),'neutral3_summary':{q:result.get(q) for q in ('states','evaluated','max_private','max_private_centers','best_overlap')}}
                args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True);return
    status={'candidate':False,'score':BASELINE,'method':'neutral3-generalized-sat','tests':tests,'best_unsat':best_unsat,'neutral3_summary':{q:result.get(q) for q in ('owner_triples','states','evaluated','max_private','max_private_centers','best_overlap')},'top_states':len(tops)}
    args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
