#!/usr/bin/env python3
"""Run exact blocker-budget repair on every signed BPZ-X t=10 two-hit geometry.

The full signed-coordinate orbit of BPZ-X has 1920 distinct images.  Prior
exact scanning found 50 image-obstruction pairs with minimum hit count 2 and no
one-hit pair.  This driver regenerates every exact two-hit translated geometry,
deduplicates the resulting 365-point retained instances, and runs the pinned
c7-five exchange_dfs solver on each one.

For budget r the solver seeks r+1 additions whose blocker-owner union has size
at most r.  A witness restores the auxiliary from 365 to 366 points, yielding a
C7^10 certificate of size 134769.
"""
import argparse,json,subprocess,sys,tempfile
from itertools import permutations
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as t10
import bpz_t10_exchange_repair as ex


def signed_two_hit_cases(I0,X0,ring,digits,nb):
    obs,_=t10.obstruction_witnesses(I0,ring,digits,nb)
    Fobs=[(m,w,np.fft.fftn(t10.arr(t10.values(m),digits))) for m,w in obs.items()]
    images={}
    for perm in permutations(range(t10.D)):
        for negmask in range(1<<t10.D):
            S=frozenset(t10.enc(tuple(((-digits[v][perm[j]])%t10.Q if ((negmask>>j)&1) else digits[v][perm[j]]) for j in range(t10.D))) for v in X0)
            images.setdefault(S,(perm,negmask))
    if len(images)!=1920: raise RuntimeError(f'signed orbit drift {len(images)}')
    out=[];seen=set();pair_count=0
    for ii,(Sfro,meta) in enumerate(images.items()):
        S=set(Sfro);perm,negmask=meta;FS=np.fft.fftn(t10.arr(S,digits))
        for oi,(mask,w,FD) in enumerate(Fobs):
            corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16)
            if int(corr.min())!=2: continue
            pair_count+=1;Dset=set(t10.values(mask))
            for idx in np.argwhere(corr==2):
                tr=tuple(int(z) for z in idx); Xfull=set(t10.shift_set(S,tr,digits,1)); hits=Xfull&Dset
                if len(hits)!=2: continue
                retained=frozenset(Xfull-Dset)
                key=(oi,retained)
                if key in seen: continue
                seen.add(key)
                out.append({'image':ii,'perm':perm,'negmask':negmask,'obstruction_index':oi,'translation':tr,'S':Xfull,'hits':set(hits),'D':Dset,'witness':w})
    if pair_count!=50: raise RuntimeError(f'min2 pair drift {pair_count} != 50')
    return out,pair_count,len(images)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('family_root',type=Path);ap.add_argument('solver',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--budget',type=int,default=4);ap.add_argument('--per-case-cutoff',type=int,default=120);args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X0=set(map(int,raw['X']))
    ring=Ring(t10.D);digits=tuple(ring.decode(v) for v in range(t10.U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(t10.U)]
    cases,pair_count,nimages=signed_two_hit_cases(I0,X0,ring,digits,nb)
    target=args.budget+1;results=[];winner=None;complete=True
    print('CASES',json.dumps({'distinct_signed_images':nimages,'min2_image_obstruction_pairs':pair_count,'distinct_two_hit_geometries':len(cases)},sort_keys=True),flush=True)
    for ci,c in enumerate(cases):
        with tempfile.TemporaryDirectory() as td:
            inp=Path(td)/'exchange.txt';retained,candidates,blockers=ex.export_input(inp,c['S'],c['hits'],c['D'],ring,args.budget)
            with inp.open('rb') as src:
                p=subprocess.run([str(args.solver),str(args.per_case_cutoff),'--budget-bitsets'],stdin=src,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,text=True)
        if p.returncode!=0: raise RuntimeError(f'exchange_dfs failed geometry {ci} rc={p.returncode}: {p.stderr[-2000:]}')
        lines=[z for z in p.stdout.splitlines() if z.strip()]
        if not lines: raise RuntimeError(f'no solver JSON geometry {ci}')
        search=json.loads(lines[-1]);st=search.get('status');rec={'geometry':ci,'image':c['image'],'perm':list(c['perm']),'negmask':c['negmask'],'obstruction_index':c['obstruction_index'],'translation':list(c['translation']),'candidate_vertices':len(candidates),'search':search}
        results.append(rec)
        if st=='timeout': complete=False
        print('GEOMETRY_DONE',json.dumps({'geometry':ci,'status':st,'nodes':search.get('nodes'),'next_root':search.get('next_root')},sort_keys=True),flush=True)
        if st!='witness': continue
        chosen=[int(i) for i in search.get('chosen',[])]
        if len(chosen)!=target: raise RuntimeError(f'bad witness length {chosen}')
        add=[candidates[i] for i in chosen];owner_ids=set()
        for y in add:
            b=blockers[y]
            while b:
                q=b&-b;owner_ids.add(retained[q.bit_length()-1]);b^=q
        if len(owner_ids)>args.budget: raise RuntimeError('blocker replay failed')
        rem=set(owner_ids)
        for q in retained:
            if len(rem)==args.budget: break
            if q not in rem: rem.add(q)
        X=(set(retained)-rem)|set(add)
        if len(X)!=366 or X&c['D'] or not t10.independent(X,digits): raise RuntimeError('repair replay failed')
        Ibits,pairs,o,PH,PV=c['witness'];pts,xp=t10.build(Ibits,X,pairs,PH,PV,ring)
        if len(pts)!=134769: raise RuntimeError(f'score replay {len(pts)}')
        winner=(c,rem,add,pts,xp,search);break
    status={'method':'bpz-t10-signed-bpzX-two-hit-exact-exchange','candidate':winner is not None,'score':134753 if winner is None else 134769,'budget':args.budget,'target_additions':target,'distinct_signed_images':nimages,'min2_image_obstruction_pairs':pair_count,'distinct_two_hit_geometries':len(cases),'geometries_processed':len(results),'complete_without_witness':winner is None and complete,'geometry_results':results}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(('EXHAUSTED' if complete else 'INCOMPLETE'),json.dumps({k:v for k,v in status.items() if k!='geometry_results'},sort_keys=True),flush=True);return
    c,rem,add,pts,xp,search=winner;Ibits,pairs,o,PH,PV=c['witness'];status.update({'score':len(pts),'winning_image':c['image'],'winning_perm':list(c['perm']),'winning_negmask':c['negmask'],'winning_obstruction_index':c['obstruction_index'],'winning_translation':list(c['translation']),'forced_hits':sorted(c['hits']),'removed_retained_points':sorted(rem),'added_auxiliary_points':add,'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]},'winning_search':search})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps({k:v for k,v in status.items() if k!='geometry_results'},sort_keys=True),flush=True)

if __name__=='__main__':main()
