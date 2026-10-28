#!/usr/bin/env python3
"""Exact splice screen: every known public 32-AND / five-AND AES core vs live 102.

For each public core:
  * identify its 9+5+18 AND architecture and the exact cone generating the nine
    nonlinear factors consumed by its final 18 products;
  * collapse the cone boundary to four abstract core variables;
  * enumerate all GL(4,2) maps whose public nine-factor set equals the live-102
    nine-factor set;
  * map the public boundary into the live core coordinates and compute an exact
    shortest XOR/XNOR closure from affine functions already FREE in the live
    q0..q41 prefix;
  * replay the public cone. If total replacement cost <=17, splice it into the
    live certificate and independently check all 256 AES inputs.

The affine closure uses code mask|(const<<4), so XNOR(a,b) = a^b^0x10.
"""
import collections, copy, json, pathlib, urllib.request
import analyze_public5_costs_v2 as A

LIVE='https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/huangxin-design/aes102-field-plane-offsets/certificate.json'
CORE_INPUTS=['q34','q36','q39','q41']
OLD_FACTORS=['q45','q59','q52','q57','q53','q49','q58','q55','q56']
TARGET_NAMES=['w45','w59','w52','w57','w53','w49','w58','w55','w56']
CONST16=(1<<16)-1


def fetch_live():
    with urllib.request.urlopen(LIVE,timeout=30) as r:return json.load(r)


def eval_named(cert, stop=None):
    vals={}
    for i in range(8):
        t=0
        for x in range(256):
            if (x>>i)&1:t|=1<<x
        vals[f'x{i}']=t
    for g in cert['gates']:
        vals[g['out']]=A.opv(g['op'],vals[g['a']],vals[g['b']],A.MASK256)
        if stop is not None and g['out']==stop:break
    return vals


def affine_code(tt16):
    """Return 5-bit affine code mask|(const<<4), or None if non-affine."""
    c=tt16&1
    z=tt16^(CONST16 if c else 0)
    m=A.coord16(z)
    return None if m is None else (m|(c<<4))


def transform_affine(code, rows):
    m=code&15;c=(code>>4)&1;out=0
    for i in range(4):
        if (m>>i)&1:out^=rows[i]
    return out|(c<<4)


def closure_plan(initial_wires, goal_codes):
    """Exact BFS shortest affine closure. Return [(op,a_code,b_code,out_code),...].

    State tracks available affine FUNCTIONS. For every two distinct function codes,
    one gate can add either XOR or XNOR. Existing duplicate wires are irrelevant for
    our goal sets; no public boundary requires synthesizing a constant by x XNOR x.
    """
    goals=set(goal_codes)
    start=set(initial_wires)
    if goals<=start:return []
    def bits(s):
        b=0
        for x in s:b|=1<<x
        return b
    startb=bits(start);goalb=bits(goals)
    q=collections.deque([startb]);prev={startb:None};mv={}
    end=None
    while q:
        st=q.popleft()
        if (st&goalb)==goalb:end=st;break
        av=[x for x in range(32) if (st>>x)&1]
        for i,a in enumerate(av):
            for b in av[i+1:]:
                for op,z in (('XOR',a^b),('XNOR',a^b^16)):
                    if (st>>z)&1:continue
                    ns=st|(1<<z)
                    if ns not in prev:
                        prev[ns]=st;mv[ns]=(op,a,b,z);q.append(ns)
    if end is None:return None
    plan=[]
    while prev[end] is not None:
        plan.append(mv[end]);end=prev[end]
    return list(reversed(plan))


def current_targets_named():
    ts=A.current_targets()
    return dict(zip(TARGET_NAMES,ts)),{t:n for n,t in zip(TARGET_NAMES,ts)}


def public_structure(path):
    c=A.fetch(path);vals,supp=A.eval256(c);first,core,final=A.classify(c,supp)
    if (len(first),len(core),len(final))!=(9,5,18):
        raise ValueError((path,'AND layers',len(first),len(core),len(final)))
    factors=[]
    for gi in final:
        _,a,b=c['gates'][gi];s=a if supp[a] else b
        if s not in factors:factors.append(s)
    if len(factors)!=9:raise ValueError((path,'factor count',len(factors)))
    cone,boundary=A.factor_cone(c,supp,core,factors)
    basis=A.choose_basis(boundary,vals)
    if len(basis)!=4:raise ValueError((path,'boundary rank'))
    btts=[vals[s] for s in basis]
    b16=[A.collapse16(vals[s],btts) for s in boundary]
    f16=[A.collapse16(vals[s],btts) for s in factors]
    if any(x is None for x in b16+f16):raise ValueError((path,'collapse'))
    bc=[affine_code(x) for x in b16]
    if any(x is None for x in bc):raise ValueError((path,'non-affine boundary',list(map(hex,b16))))
    curset=set(A.current_targets());exact=[]
    for rows in A.gl4():
        ft={A.transform(t,rows) for t in f16}
        if ft==curset:exact.append(rows)
    return {'c':c,'vals':vals,'supp':supp,'core':core,'factors':factors,
            'cone':cone,'boundary':boundary,'basis':basis,'boundary_codes':bc,
            'factor16':f16,'exact':exact}


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
    for k in (1,2,3,4):z^=((y<<k)|(y>>(8-k)))&0xff
    return z^0x63


def eval_cert(cert):
    out=[]
    for x in range(256):
        v={f'x{i}':(x>>i)&1 for i in range(8)}
        for g in cert['gates']:
            a,b=v[g['a']],v[g['b']]
            if g['op']=='XOR':y=a^b
            elif g['op']=='XNOR':y=1^a^b
            elif g['op']=='AND':y=a&b
            else:raise ValueError(g['op'])
            v[g['out']]=y
        out.append(sum(v[n]<<i for i,n in enumerate(cert['outputs'])))
    return out


def main():
    live=fetch_live();prefixvals=eval_named(live,'q41')
    basis256=[prefixvals[n] for n in CORE_INPUTS]
    assert A.rank(basis256)==4

    # Every prefix wire that is an affine function of the four live core inputs is free.
    free={}
    for n,t in prefixvals.items():
        z=A.collapse16(t,basis256)
        if z is None:continue
        code=affine_code(z)
        if code is not None:free.setdefault(code,[]).append(n)
    initial_codes=set(free)
    target_by_name,target_by_tt=current_targets_named()

    # Fixed live decomposition is q0..q41 (42) + q42..q59 (18) + q60..q101 (42).
    prefix_gates=[]
    for g in live['gates']:
        prefix_gates.append(copy.deepcopy(g))
        if g['out']=='q41':break
    tail_start=next(i for i,g in enumerate(live['gates']) if g['out']=='q60')
    tail_template=live['gates'][tail_start:]
    assert len(prefix_gates)==42 and len(tail_template)==42

    results=[];best_cert=None;best_rec=None
    for path in A.FILES:
        try:p=public_structure(path)
        except Exception as e:
            results.append({'file':path,'error':repr(e)});continue
        c=p['c'];cone_set=set(p['cone'])
        for rows in p['exact']:
            mapped_boundary=[transform_affine(code,rows) for code in p['boundary_codes']]
            plan=closure_plan(initial_codes,mapped_boundary)
            if plan is None:
                results.append({'file':path,'rows':rows,'error':'affine closure failed'});continue
            cost=len(plan)+len(p['cone'])
            rec={'file':path,'rows':rows,'cone_gate_count':len(p['cone']),
                 'cone_ops':dict(collections.Counter(c['gates'][gi][0] for gi in p['cone'])),
                 'boundary_codes_public':p['boundary_codes'],'boundary_codes_live':mapped_boundary,
                 'prefix_extra_gates':len(plan),'splice_core_cost':cost,'closure_plan':plan,
                 'candidate_gate_count':84+cost}

            # Build candidates only when competitive with live 18-gate region.
            if cost<=18:
                new=[];code_wire={code:names[0] for code,names in free.items()};counter=0
                for op,ca,cb,cz in plan:
                    if ca not in code_wire or cb not in code_wire:
                        raise RuntimeError(('plan operand missing',ca,cb))
                    out=f'rb{counter}';counter+=1
                    new.append({'op':op,'a':code_wire[ca],'b':code_wire[cb],'out':out})
                    code_wire[cz]=out
                sigmap={s:code_wire[code] for s,code in zip(p['boundary'],mapped_boundary)}
                for gi in p['cone']:
                    op,a,b=c['gates'][gi]
                    def src(s):
                        if s in sigmap:return sigmap[s]
                        if s>=8 and (s-8) in cone_set and s in sigmap:return sigmap[s]
                        raise KeyError((path,gi,s))
                    out=f'rc{counter}';counter+=1
                    new.append({'op':op,'a':src(a),'b':src(b),'out':out})
                    sigmap[8+gi]=out
                assert len(new)==cost

                # Map transformed public factor truth tables onto the nine live target names.
                fwire={}
                for s,t in zip(p['factors'],p['factor16']):
                    tt=A.transform(t,rows);name=target_by_tt[tt]
                    fwire[name]=sigmap[s]
                assert set(fwire)==set(TARGET_NAMES)
                replace={old:fwire[name] for old,name in zip(OLD_FACTORS,TARGET_NAMES)}

                tail=[];old_core={f'q{i}' for i in range(42,60)}
                for g in tail_template:
                    gg=copy.deepcopy(g)
                    for k in ('a','b'):
                        if gg[k] in replace:gg[k]=replace[gg[k]]
                        elif gg[k] in old_core:raise RuntimeError(('unmapped old core ref',gg))
                    tail.append(gg)
                cert={'gates':prefix_gates+new+tail,'outputs':live['outputs']}
                assert len(cert['gates'])==84+cost
                got=eval_cert(cert);want=[aes_sbox(x) for x in range(256)]
                rec['candidate_valid_256']=got==want
                if got!=want:
                    rec['first_mismatch']=next((i,got[i],want[i]) for i in range(256) if got[i]!=want[i])
                elif best_cert is None or len(cert['gates'])<len(best_cert['gates']):
                    best_cert=cert;best_rec=rec
            results.append(rec)

    results.sort(key=lambda r:(r.get('splice_core_cost',999),r.get('file',''),str(r.get('rows',''))))
    summary={'live_prefix_affine_codes':{str(k):v for k,v in sorted(free.items())},
             'public_map_count':sum(1 for r in results if 'rows' in r),
             'best_splice_core_cost':min((r['splice_core_cost'] for r in results if 'splice_core_cost' in r),default=None),
             'best_20':results[:20],
             'valid_candidate_gates':len(best_cert['gates']) if best_cert else None,
             'valid_candidate_record':best_rec}
    out=pathlib.Path('/tmp/aes-public5-splice-v2');out.mkdir(parents=True,exist_ok=True)
    json.dump(summary,open(out/'summary.json','w'),indent=2)
    if best_cert is not None:json.dump(best_cert,open(out/'candidate.json','w'),indent=2)
    print(json.dumps(summary,indent=2,sort_keys=True))
    if best_cert is not None:print('VALID_CANDIDATE',len(best_cert['gates']))

if __name__=='__main__':main()
