#!/usr/bin/env python3
"""Exact deep repair for one case of the unique FunSearch t=9 one-hit basin.

The two 20-state signed-orbit basins are exactly isomorphic.  We use image 330
as the sole representative.  Its signed-coordinate metadata and translation
were independently replayed and are fixed below, so there is no need to repeat
the expensive 768-image FFT scan in every deep-search job.

The 20 states share the same translated 367-set and differ only in which of the
160 exact BPZ t=9 obstruction masks has a unique intersection point.  A chosen
case is exported to the pinned c7-five blocker-budget exchange solver; any
witness is replayed and materialized as a 134770-point Few Shots certificate.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t9_aux_translation_fft as f
import bpz_t9_exchange_repair as ex
from bpz_t9_funsearch_fft import funsearch_seed, FUNSEARCH_COMMIT

PERM=(0,2,4,1,3)
NEGMASK=10
TRANSLATION=(6,3,6,3,6)
IMAGE_INDEX=330


def representative_set(digits):
    seed=funsearch_seed(digits);S0=set()
    for v in seed:
        w=digits[v]
        q=tuple(((-w[PERM[j]])%f.Q) if ((NEGMASK>>j)&1) else w[PERM[j]] for j in range(f.D))
        S0.add(f.enc(q))
    if len(S0)!=f.N or not f.independent(S0,digits):raise RuntimeError('signed image replay failed')
    S=set(f.shift_set(S0,TRANSLATION,digits,1))
    if len(S)!=f.N or not f.independent(S,digits):raise RuntimeError('translated image replay failed')
    return S


def cases(I0,ring,digits,nbmask):
    obs=list(f.obstruction_witnesses(I0,ring,digits,nbmask).items());S=representative_set(digits);out=[]
    for oi,(mask,witness) in enumerate(obs):
        D=set(f.values(mask));hits=S&D
        if len(hits)==1:out.append({'obstruction_index':oi,'S':S,'D':D,'bad':next(iter(hits)),'witness':witness})
    if len(out)!=20:raise RuntimeError(f'representative one-hit drift {len(out)} != 20')
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('solver',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path)
    ap.add_argument('--case',type=int,required=True);ap.add_argument('--budget',type=int,default=8);ap.add_argument('--cutoff',type=int,default=300);args=ap.parse_args()
    if not 0<=args.case<20:raise SystemExit('case must be 0..19')
    if not 1<=args.budget<=8:raise SystemExit('budget must be 1..8')
    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));ring=Ring(f.D);digits=tuple(ring.decode(v) for v in range(f.U));nbmask=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]
    cc=cases(I0,ring,digits,nbmask);c=cc[args.case];S,bad,Dset=c['S'],c['bad'],c['D']
    with tempfile.TemporaryDirectory() as td:
        inp=Path(td)/'exchange.txt';retained,candidates,blockers=ex.export_input(inp,S,bad,Dset,ring,args.budget)
        with inp.open('rb') as src:p=subprocess.run([str(args.solver),str(args.cutoff),'--budget-bitsets'],stdin=src,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False)
    if p.returncode!=0:raise RuntimeError(f'exchange_dfs failed rc={p.returncode}: {p.stderr[-2000:]}')
    lines=[z for z in p.stdout.splitlines() if z.strip()]
    if not lines:raise RuntimeError('exchange solver produced no JSON')
    search=json.loads(lines[-1]);target=args.budget+1
    status={'method':'bpz-t9-funsearch-representative-exact-blocker-budget','candidate':search.get('status')=='witness','complete':search.get('status') in ('witness','exhausted'),'score':134753,'image':IMAGE_INDEX,'perm':list(PERM),'negmask':NEGMASK,'translation':list(TRANSLATION),'case_index':args.case,'obstruction_index':c['obstruction_index'],'bad':bad,'budget':args.budget,'target_additions':target,'candidate_vertices':len(candidates),'search':search,'solver_stderr_tail':p.stderr[-2000:],'funsearch_source_commit':FUNSEARCH_COMMIT,'exchange_solver_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if not status['candidate']:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(search.get('status','UNKNOWN').upper(),json.dumps(status,sort_keys=True),flush=True);return
    chosen=[int(i) for i in search.get('chosen',[])]
    if len(chosen)!=target or any(not 0<=i<len(candidates) for i in chosen):raise RuntimeError(f'bad witness {chosen}')
    add=[candidates[i] for i in chosen];owner_ids=set()
    for y in add:
        b=blockers[y]
        while b:
            q=b&-b;owner_ids.add(retained[q.bit_length()-1]);b^=q
    if len(owner_ids)>args.budget:raise RuntimeError('blocker budget replay failed')
    rem={bad}|owner_ids
    for q in retained:
        if len(rem)==target:break
        if q not in rem:rem.add(q)
    repaired=(S-rem)|set(add)
    if len(rem)!=target or len(repaired)!=f.N or repaired&Dset or not f.independent(repaired,digits):raise RuntimeError('repair replay failed')
    Ibits,pairs,orient,PH,PV=c['witness'];points,xp=f.build(Ibits,sum(1<<q for q in repaired),pairs,PH,PV,ring)
    if len(points)!=f.TARGET:raise RuntimeError(f'target score drift {len(points)}')
    status.update({'score':len(points),'removed_auxiliary_points':sorted(rem),'added_auxiliary_points':add,'private_pairs':[list(q) for q in pairs],'orientation':list(orient),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__':main()
