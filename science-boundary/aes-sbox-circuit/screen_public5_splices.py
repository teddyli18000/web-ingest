#!/usr/bin/env python3
import collections, copy, json, pathlib, sys, urllib.request
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import analyze_public5_cores as A

LIVE='https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/huangxin-design/aes102-field-plane-offsets/certificate.json'
CORE_INPUTS=['q34','q36','q39','q41']
OLD_FACTORS=['q45','q59','q52','q57','q53','q49','q58','q55','q56']
TARGET_NAMES=['w45','w59','w52','w57','w53','w49','w58','w55','w56']


def fetch_live():
    with urllib.request.urlopen(LIVE,timeout=30) as r:return json.load(r)


def bitvars256():
    vals={}
    for i in range(8):
        t=0
        for x in range(256):
            if (x>>i)&1:t|=1<<x
        vals[f'x{i}']=t
    return vals


def eval_named(cert,stop=None):
    vals=bitvars256()
    for g in cert['gates']:
        vals[g['out']]=A.opv(g['op'],vals[g['a']],vals[g['b']],A.MASK256)
        if stop is not None and g['out']==stop:break
    return vals


def var16(i):
    t=0
    for x in range(16):
        if (x>>i)&1:t|=1<<x
    return t
VAR16=[var16(i) for i in range(4)]


def coord16(tt):
    return A.coordinates(tt,VAR16)


def map_linear_mask(mask,rows):
    r=0
    for i in range(4):
        if (mask>>i)&1:r^=rows[i]
    return r


def closure_plan(start_masks,goal_masks):
    start=set(start_masks);goals=set(goal_masks)
    if goals<=start:return []
    st0=sum(1<<m for m in start if m)
    goalbits=sum(1<<m for m in goals if m)
    q=collections.deque([st0]);prev={st0:None};move={}
    end=None
    while q:
        st=q.popleft()
        if (st&goalbits)==goalbits:end=st;break
        av=[m for m in range(1,16) if (st>>m)&1]
        for i,a in enumerate(av):
            for b in av[i+1:]:
                z=a^b
                if z==0 or (st>>z)&1:continue
                ns=st|(1<<z)
                if ns not in prev:
                    prev[ns]=st;move[ns]=(a,b,z);q.append(ns)
    if end is None:raise RuntimeError('closure failed')
    out=[]
    while prev[end] is not None:
        out.append(move[end]);end=prev[end]
    out.reverse();return out


def aes_sbox(x):
    def mul(a,b):
        r=0
        for _ in range(8):
            if b&1:r^=a
            hi=a&0x80;a=(a<<1)&0xff
            if hi:a^=0x1b
            b>>=1
        return r
    if x==0:y=0
    else:
        y=1;base=x;e=254
        while e:
            if e&1:y=mul(y,base)
            base=mul(base,base);e>>=1
    z=y
    for k in (1,2,3,4):z ^= ((y<<k)|(y>>(8-k)))&0xff
    return z^0x63


def eval_candidate(cert):
    outs=[]
    for x in range(256):
        v={f'x{i}':(x>>i)&1 for i in range(8)}
        for g in cert['gates']:
            a,b=v[g['a']],v[g['b']]
            if g['op']=='XOR':o=a^b
            elif g['op']=='XNOR':o=1^a^b
            elif g['op']=='AND':o=a&b
            else:raise ValueError(g['op'])
            v[g['out']]=o
        y=sum(v[n]<<i for i,n in enumerate(cert['outputs']))
        outs.append(y)
    return outs


def public_structure(name):
    c=A.fetch(name);vals,supports,_=A.eval256(c);first,core,final=A.classify(c,supports)
    assert (len(first),len(core),len(final))==(9,5,18)
    fac=[]
    for gi in final:
        _,a,b=c['gates'][gi];fac.append(a if supports[a] else b)
    factors=[]
    for s in fac:
        if s not in factors:factors.append(s)
    cone,boundary=A.factor_cone(c,supports,core,factors)
    basis=A.choose_independent(boundary,vals);assert len(basis)==4
    btts=[vals[s] for s in basis]
    bm=[A.coordinates(A.collapse16(vals[s],btts),btts) for s in boundary]
    ft=[A.collapse16(vals[s],btts) for s in factors]
    _,targets=A.current_targets();tset=set(targets)
    exact=[]
    for rows in A.gl4():
        if {A.transform16(t,rows) for t in ft}==tset:exact.append(rows)
    return c,vals,supports,core,factors,cone,boundary,basis,bm,ft,exact


def main():
    live=fetch_live();prefix=eval_named(live,'q41');basis256=[prefix[n] for n in CORE_INPUTS]
    assert A.rank(basis256)==4
    avail={}
    for n,t in prefix.items():
        z=A.collapse16(t,basis256)
        if z is None:continue
        m=coord16(z)
        if m is not None and m!=0:avail.setdefault(m,[]).append(n)
    start_masks=set(avail)
    _,target_tts=A.current_targets();target_by_tt={t:n for t,n in zip(target_tts,TARGET_NAMES)}
    results=[];best_candidate=None

    for name in A.FILES:
        c,pvals,supports,core,factors,cone,boundary,pbasis,bm,ft,exact=public_structure(name)
        for rows in exact:
            mapped_boundary=[map_linear_mask(m,rows) for m in bm]
            plan=closure_plan(start_masks,mapped_boundary)
            cost=len(cone)+len(plan)
            rec={'file':name,'rows':rows,'cone_gate_count':len(cone),'boundary_signals':boundary,
                 'boundary_masks_public':bm,'boundary_masks_current':mapped_boundary,
                 'prefix_extra_xors':len(plan),'splice_core_cost':cost,'xor_plan':plan}
            results.append(rec)
            if cost>17:continue

            # Materialize missing boundary forms using existing prefix wires plus XORs.
            prefix_gates=[]
            for g in live['gates']:
                prefix_gates.append(copy.deepcopy(g))
                if g['out']=='q41':break
            maskwire={m:names[0] for m,names in avail.items()}
            new=[];counter=0
            for a,b,z in plan:
                out=f'rb{counter}';counter+=1
                new.append({'op':'XOR','a':maskwire[a],'b':maskwire[b],'out':out});maskwire[z]=out
            sigmap={s:maskwire[cm] for s,cm in zip(boundary,mapped_boundary)}
            cone_set=set(cone)
            for gi in sorted(cone):
                op,a,b=c['gates'][gi]
                def src(s):
                    if s in sigmap:return sigmap[s]
                    if s>=8 and (s-8) in cone_set:return sigmap[s]
                    raise KeyError((name,gi,s))
                out=f'rc{counter}';counter+=1
                new.append({'op':op,'a':src(a),'b':src(b),'out':out});sigmap[8+gi]=out

            factor_target_wire={}
            for s,t in zip(factors,ft):
                tt=A.transform16(t,rows);tn=target_by_tt[tt];factor_target_wire[tn]=sigmap[s]
            assert len(factor_target_wire)==9
            replace={old:factor_target_wire[tn] for old,tn in zip(OLD_FACTORS,TARGET_NAMES)}

            tail=[]
            seen60=False
            oldcore=set(f'q{i}' for i in range(42,60))
            for g in live['gates']:
                if g['out']=='q60':seen60=True
                if not seen60:continue
                gg=copy.deepcopy(g)
                for k in ('a','b'):
                    if gg[k] in replace:gg[k]=replace[gg[k]]
                    elif gg[k] in oldcore:raise RuntimeError(f'unmapped old core ref {gg[k]} in {gg}')
                tail.append(gg)
            cand={'gates':prefix_gates+new+tail,'outputs':live['outputs']}
            assert len(cand['gates'])==84+cost
            got=eval_candidate(cand);want=[aes_sbox(x) for x in range(256)]
            rec['candidate_valid_256']=got==want;rec['candidate_gates']=len(cand['gates'])
            if rec['candidate_valid_256'] and (best_candidate is None or len(cand['gates'])<len(best_candidate['gates'])):
                best_candidate=cand

    results.sort(key=lambda r:(r['splice_core_cost'],r['file'],r['rows']))
    summary={'live_prefix_core_linear_masks':{str(k):v for k,v in sorted(avail.items())},
             'best_splice_core_cost':min(r['splice_core_cost'] for r in results),
             'best':results[:20],'all_map_count':len(results)}
    out=pathlib.Path('/tmp/aes-public5-splice');out.mkdir(parents=True,exist_ok=True)
    json.dump(summary,open(out/'summary.json','w'),indent=2)
    if best_candidate is not None:json.dump(best_candidate,open(out/'candidate.json','w'),indent=2)
    print(json.dumps(summary,indent=2,sort_keys=True))
    if best_candidate is not None:print('VALID_CANDIDATE',len(best_candidate['gates']))

if __name__=='__main__':main()
