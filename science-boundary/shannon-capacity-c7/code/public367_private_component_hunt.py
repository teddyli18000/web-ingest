#!/usr/bin/env python3
"""Search private-swap components of public 367-sets for >=11 private owners.

A private swap replaces an old independent-set vertex a by an outside vertex q
that conflicts with exactly a.  This preserves size 367 and independence.  The
BPZ/Gao t-construction can use t distinct private owners, so a state with >=11
private owners would open a t=11 family with substantially more obstruction-hit
tolerance than the current t=9/10 routes.

This is a multi-source exact graph traversal over the BPZ X/I0 and 36 Family-F
seeds.  A configurable state cap protects CI resources; the output distinguishes
complete exhaustion from a capped partial search.  Any >=11 state is replayed
for independence and written explicitly for follow-up construction work.
"""
import argparse
import json
import sys
from collections import deque
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as t10


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('tan_root',type=Path); ap.add_argument('family_root',type=Path); ap.add_argument('status',type=Path)
    ap.add_argument('--max-states',type=int,default=100000)
    args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve())); from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text()); I0=set(map(int,raw['I0'])); X0=set(map(int,raw['X']))
    fam=json.loads((args.family_root/'data'/'family-f.json').read_text()); states=[set(map(int,s)) for s in fam['states']]
    seeds=[('bpz-X',X0),('bpz-I0',I0)]+[(f'family-f-{i}',s) for i,s in enumerate(states)]
    ring=Ring(t10.D); digits=tuple(ring.decode(v) for v in range(t10.U)); nb=[sum(1<<z for z in ring.NB[v]) for v in range(t10.U)]

    seed_bits=[]
    for name,S in seeds:
        if len(S)!=367 or not t10.independent(S,digits): raise RuntimeError(f'invalid seed {name}')
        seed_bits.append((name,sum(1<<z for z in S)))

    seen=set(); q=deque(); origin={}
    for name,b in seed_bits:
        if b not in seen:
            seen.add(b); q.append((b,0)); origin[b]=name

    expanded=0; transitions=0; best_owners=-1; best_pairs=-1; best=None; hist={}; found=None; max_depth=0
    while q and expanded<args.max_states:
        bits,depth=q.popleft(); expanded+=1; max_depth=max(max_depth,depth)
        pp=t10.private(bits,nb); owners={a for a,x in pp}; no=len(owners); npair=len(pp)
        hist[str(no)]=hist.get(str(no),0)+1
        if no>best_owners or (no==best_owners and npair>best_pairs):
            best_owners=no; best_pairs=npair; best=(bits,depth,origin.get(bits),pp)
            print('NEW_BEST',json.dumps({'expanded':expanded,'seen':len(seen),'depth':depth,'private_owners':no,'private_pairs':npair,'origin':origin.get(bits)},sort_keys=True),flush=True)
        if no>=11:
            found=(bits,depth,pp); break
        for a,x in pp:
            nb_state=bits^(1<<a)^(1<<x); transitions+=1
            if nb_state in seen: continue
            # The private-neighbour definition is sufficient, but replay newly
            # discovered states before retaining them as durable evidence.
            S=set(t10.values(nb_state))
            if len(S)!=367 or not t10.independent(S,digits): raise RuntimeError('private swap replay failed')
            seen.add(nb_state); q.append((nb_state,depth+1)); origin[nb_state]=origin.get(bits)

    complete=not q and found is None
    status={'method':'public-367-private-swap-component-hunt','seed_count':len(seeds),'distinct_seed_states':len(seed_bits),'max_states':args.max_states,'states_expanded':expanded,'states_seen':len(seen),'frontier_remaining':len(q),'complete_without_t11':complete,'found_t11_parent':found is not None,'max_private_owners':best_owners,'max_private_pairs':best_pairs,'max_depth_expanded':max_depth,'transitions_examined':transitions,'owner_histogram':hist}
    if best is not None:
        bb,bd,bo,bpp=best; status['best']={'depth':bd,'origin':bo,'private_owners':len({a for a,x in bpp}),'private_pairs':len(bpp),'points':list(t10.values(bb))}
    if found is not None:
        fb,fd,fpp=found; status['t11_parent']={'depth':fd,'origin':origin.get(fb),'private_owners':len({a for a,x in fpp}),'private_pairs':len(fpp),'points':list(t10.values(fb)),'private_pairs_list':[list(z) for z in fpp]}
    args.status.parent.mkdir(parents=True,exist_ok=True); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print(('FOUND' if found else 'DONE' if complete else 'CAPPED'),json.dumps({k:v for k,v in status.items() if k not in ('best','t11_parent','owner_histogram')},sort_keys=True),flush=True)

if __name__=='__main__': main()
