#!/usr/bin/env python3
"""Screen released Jain 32-AND AES (inverse-)S-box circuits for reusable 5-AND cores.

The released constructions have the tower-field AND architecture 9 + 5 + 18.
This script identifies those layers from AND ancestry, extracts the 4-dimensional
boundary and the nine nonlinear factors consumed by the last 18 products, checks
all GL(4,2) input changes against the nine factors of the live 102-gate Few Shots
core, and measures the released factor-generation cone from a movable 4-wire
interface.
"""
import collections, itertools, json, urllib.request

BASE = 'https://raw.githubusercontent.com/ahrazzle/gf2m-circuits/main/sbox/circuits/'
FILES = ['sbox106_d34.json','sbox110_d38.json','invsbox109_d30.json','invsbox109_d31.json']
MASK256=(1<<256)-1
MASK16=(1<<16)-1


def fetch(name):
    with urllib.request.urlopen(BASE+name, timeout=30) as r:
        return json.load(r)


def rank(vals):
    piv=[]
    for x in vals:
        y=x
        for p in piv:
            y=min(y,y^p)
        if y:
            piv.append(y); piv.sort(reverse=True)
    return len(piv)


def independent_rows(rows):
    return rank(rows)==len(rows)


def gl4():
    for rows in itertools.permutations(range(1,16),4):
        if independent_rows(rows):
            yield rows


def opv(op,a,b,mask):
    if op=='XOR': return a^b
    if op=='XNOR': return (~(a^b))&mask
    if op=='AND': return a&b
    raise ValueError(op)


def eval256(c):
    vals=[]; supports=[]; and_gate_ids=[]
    # U0 is MSB, U7 LSB in Jain's pack.
    for i in range(8):
        t=0
        for x in range(256):
            if (x>>(7-i))&1: t |= 1<<x
        vals.append(t); supports.append(frozenset())
    for gi,(op,a,b) in enumerate(c['gates']):
        vals.append(opv(op,vals[a],vals[b],MASK256))
        s=set(supports[a])|set(supports[b])
        if op=='AND':
            s.add(gi); and_gate_ids.append(gi)
        supports.append(frozenset(s))
    return vals,supports,and_gate_ids


def classify(c,supports):
    first=[]; core=[]; final=[]
    for gi,(op,a,b) in enumerate(c['gates']):
        if op!='AND': continue
        sa,sb=supports[a],supports[b]
        if not sa and not sb: first.append(gi)
        elif sa and sb: core.append(gi)
        else: final.append(gi)
    return first,core,final


def choose_independent(signals, vals):
    basis=[]
    for s in signals:
        if rank([vals[x] for x in basis+[s]])>len(basis): basis.append(s)
        if len(basis)==4: break
    return basis


def collapse16(tt256,basis_tts):
    seen={}
    for x in range(256):
        p=0
        for i,t in enumerate(basis_tts): p |= ((t>>x)&1)<<i
        bit=(tt256>>x)&1
        if p in seen and seen[p]!=bit: return None
        seen[p]=bit
    if len(seen)!=16: return None
    out=0
    for p,b in seen.items(): out |= b<<p
    return out


def coordinates(tt,basis_tts):
    for m in range(16):
        v=0
        for i,b in enumerate(basis_tts):
            if (m>>i)&1:v^=b
        if v==tt:return m
    return None


def min_xor_closure(target_masks):
    """Exact min XOR gates from four free basis masks 1,2,4,8 to target masks."""
    start_mask=sum(1<<m for m in (1,2,4,8))
    goal_mask=sum(1<<m for m in set(target_masks))
    if (start_mask & goal_mask)==goal_mask:return 0
    q=collections.deque([(start_mask,0)]); seen={start_mask}
    while q:
        st,d=q.popleft()
        avail=[m for m in range(1,16) if (st>>m)&1]
        for i,a in enumerate(avail):
            for b in avail[i+1:]:
                z=a^b
                if z==0 or (st>>z)&1:continue
                ns=st|(1<<z)
                if (ns&goal_mask)==goal_mask:return d+1
                if ns not in seen:
                    seen.add(ns);q.append((ns,d+1))
    raise RuntimeError('linear closure failed')


def current_targets():
    def v(i):
        t=0
        for x in range(16):
            if (x>>i)&1:t|=1<<x
        return t
    a,b,c,d=[v(i) for i in range(4)]
    w42=a&b; w43=w42^c; w44=w43&d; w45=b^w44; w46=w42&c; w47=d^w46
    w48=a&w47; w49=w43^w48; w50=w48^b; w51=w49&w50; w52=w51^a; w53=w52^w49
    w54=w45&w53; w55=w54^w47; w56=w55^w49; w57=w53^w45; w58=w56^w57; w59=w55^w45
    names=['w45','w59','w52','w57','w53','w49','w58','w55','w56']
    return names,[w45,w59,w52,w57,w53,w49,w58,w55,w56]


def transform16(tt,rows):
    out=0
    for x in range(16):
        y=0
        for i,r in enumerate(rows): y |= ((r & x).bit_count()&1)<<i
        out |= ((tt>>y)&1)<<x
    return out


def factor_cone(c, supports, core, factors):
    core_set=set(core); gates=set(); boundary=set()
    def visit_signal(s):
        if not (set(supports[s]) & core_set):
            boundary.add(s);return
        if s<8: raise RuntimeError('core-dependent primary input')
        gi=s-8
        if gi in gates:return
        gates.add(gi)
        _,a,b=c['gates'][gi]
        visit_signal(a);visit_signal(b)
    for s in factors: visit_signal(s)
    return sorted(gates),sorted(boundary)


def analyze(name):
    c=fetch(name); vals,supports,_=eval256(c)
    first,core,final=classify(c,supports)
    if (len(first),len(core),len(final))!=(9,5,18):
        return {'file':name,'counts':c.get('counts'),'classification':{'first':first,'core':core,'final':final},'error':'AND ancestry did not give 9+5+18'}

    # Nine nonlinear operands of the 18 final products; each should be used twice.
    factor_signals=[]
    for gi in final:
        _,a,b=c['gates'][gi]
        nonlinear=a if supports[a] else b
        factor_signals.append(nonlinear)
    uniq=[]
    for s in factor_signals:
        if s not in uniq:uniq.append(s)

    cone_gates,cone_boundary=factor_cone(c,supports,core,uniq)
    basis=choose_independent(cone_boundary,vals)
    if len(basis)!=4:
        return {'file':name,'counts':c.get('counts'),'error':'factor-cone boundary rank is not four','cone_boundary':cone_boundary}
    btts=[vals[s] for s in basis]
    boundary16=[collapse16(vals[s],btts) for s in cone_boundary]
    factor16=[collapse16(vals[s],btts) for s in uniq]
    if len(uniq)!=9 or any(t is None for t in boundary16+factor16):
        return {'file':name,'counts':c.get('counts'),'error':'factor extraction/collapse failed','basis':basis,'factor_signals':uniq,'cone_boundary':cone_boundary}

    boundary_masks=[coordinates(t,btts) for t in boundary16]
    if any(m is None for m in boundary_masks):
        return {'file':name,'counts':c.get('counts'),'error':'boundary is not linear in chosen basis','boundary_masks':boundary_masks}
    boundary_extra=min_xor_closure(boundary_masks)
    opcounts=collections.Counter(c['gates'][gi][0] for gi in cone_gates)
    released_core_factor_cost=len(cone_gates)+boundary_extra

    _,current=current_targets(); cset=set(current)
    best=-1;best_rows=[];exact=[];hist={}
    for rows in gl4():
        fs={transform16(t,rows) for t in factor16}
        hit=len(fs&cset);hist[hit]=hist.get(hit,0)+1
        if hit>best:best=hit;best_rows=[rows]
        elif hit==best and len(best_rows)<16:best_rows.append(rows)
        if fs==cset:exact.append(rows)

    return {
        'file':name,'counts':c.get('counts'),
        'and_layers':{'first':first,'core':core,'final':final},
        'factor_signals':uniq,'factor_use_counts':{s:factor_signals.count(s) for s in uniq},
        'cone_gates':cone_gates,'cone_gate_count':len(cone_gates),'cone_op_counts':dict(opcounts),
        'cone_boundary':cone_boundary,'cone_boundary_rank':rank([vals[s] for s in cone_boundary]),
        'basis':basis,'boundary_masks':boundary_masks,'boundary_extra_xors':boundary_extra,
        'released_core_factor_cost':released_core_factor_cost,
        'max_target_overlap':best,'best_rows':best_rows,'exact_orbit_maps':exact,
        'overlap_histogram':dict(sorted(hist.items())),
    }


def main():
    print(json.dumps([analyze(f) for f in FILES],indent=2,sort_keys=True))

if __name__=='__main__':main()
