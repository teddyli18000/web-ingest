#!/usr/bin/env python3
"""Screen released Jain 32-AND AES (inverse-)S-box circuits for reusable 5-AND cores.

The released constructions have the tower-field AND architecture 9 + 5 + 18.
This script identifies those layers from AND ancestry, extracts the 4-dimensional
boundary and the nine nonlinear factors consumed by the last 18 products, then
checks all GL(4,2) input changes against the nine factors of the live 102-gate
Few Shots core.
"""
import itertools, json, urllib.request

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
    first=[]; core=[]; final=[]; ambiguous=[]
    for gi,(op,a,b) in enumerate(c['gates']):
        if op!='AND': continue
        sa,sb=supports[a],supports[b]
        if not sa and not sb:
            first.append(gi)
        elif sa and sb:
            core.append(gi)
        else:
            final.append(gi)
    return first,core,final,ambiguous


def choose_boundary_basis(c,vals,supports,core):
    core_set=set(core)
    candidates=[]
    for gi in core:
        _,a,b=c['gates'][gi]
        for s in (a,b):
            if not (set(supports[s]) & core_set) and s not in candidates:
                candidates.append(s)
    basis=[]
    for s in candidates:
        if rank([vals[x] for x in basis+[s]])>len(basis):
            basis.append(s)
        if len(basis)==4: break
    return candidates,basis


def collapse16(tt256,basis_tts):
    seen={}
    for x in range(256):
        p=0
        for i,t in enumerate(basis_tts):
            p |= ((t>>x)&1)<<i
        bit=(tt256>>x)&1
        if p in seen and seen[p]!=bit:
            return None
        seen[p]=bit
    if len(seen)!=16:
        return None
    out=0
    for p,b in seen.items(): out |= b<<p
    return out


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
        for i,r in enumerate(rows):
            y |= ((r & x).bit_count()&1)<<i
        out |= ((tt>>y)&1)<<x
    return out


def analyze(name):
    c=fetch(name); vals,supports,_=eval256(c)
    first,core,final,_=classify(c,supports)
    if (len(first),len(core),len(final))!=(9,5,18):
        return {'file':name,'counts':c.get('counts'),'classification':{'first':first,'core':core,'final':final},'error':'AND ancestry did not give 9+5+18'}

    candidates,basis=choose_boundary_basis(c,vals,supports,core)
    btts=[vals[s] for s in basis]
    # Nine nonlinear operands of the 18 final products; each should be used twice.
    factor_signals=[]
    for gi in final:
        _,a,b=c['gates'][gi]
        sa,sb=supports[a],supports[b]
        nonlinear=a if sa else b
        factor_signals.append(nonlinear)
    uniq=[]
    for s in factor_signals:
        if s not in uniq: uniq.append(s)

    collapsed=[collapse16(vals[s],btts) for s in uniq]
    if len(uniq)!=9 or any(t is None for t in collapsed):
        return {'file':name,'counts':c.get('counts'),'classification':{'first':first,'core':core,'final':final},
                'boundary_candidates':candidates,'basis':basis,'factor_signals':uniq,
                'error':'factor extraction/collapse failed'}

    tnames,current=current_targets(); cset=set(current)
    best=-1; best_rows=[]; exact=[]; hist={}
    for rows in gl4():
        fs={transform16(t,rows) for t in collapsed}
        hit=len(fs & cset)
        hist[hit]=hist.get(hit,0)+1
        if hit>best:
            best=hit; best_rows=[rows]
        elif hit==best and len(best_rows)<16:
            best_rows.append(rows)
        if fs==cset:
            exact.append(rows)

    # Count uses of each factor among the 18 final products.
    use_counts={s:factor_signals.count(s) for s in uniq}
    return {
        'file':name,'counts':c.get('counts'),
        'and_layers':{'first':first,'core':core,'final':final},
        'boundary_candidates':candidates,'boundary_rank':rank([vals[s] for s in candidates]),'basis':basis,
        'factor_signals':uniq,'factor_use_counts':use_counts,
        'max_target_overlap':best,'best_rows':best_rows,'exact_orbit_maps':exact,
        'overlap_histogram':dict(sorted(hist.items())),
    }


def main():
    results=[analyze(f) for f in FILES]
    print(json.dumps(results,indent=2,sort_keys=True))

if __name__=='__main__':main()
