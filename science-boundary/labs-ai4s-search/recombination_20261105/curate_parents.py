#!/usr/bin/env python3
"""Certify *genuinely distinct* public LABS parent orbits at each length.

Use a pinned original 2004-Knauer RLE archive, plus existing independently
published GPU-MTS and QOBLIB anchors. No perturbations/synthetics allowed.
"""
import argparse, collections, hashlib, json, pathlib, re

CHOSEN=(46,47,50,59,60,92,99)
ARCHIVE_COUNTS={46:3,47:6,50:3,59:2,60:2}
EXACT_REFS={46:131,47:135,50:153,59:205,60:218}

def exact(bits):
    a=[1 if c=='1' else -1 for c in bits]
    return sum(sum(a[i]*a[i+k] for i in range(len(a)-k))**2 for k in range(1,len(a)))
def orbit(bits):
    def rev(a):return a[::-1]
    def flip(a):return ''.join('1' if x=='0' else '0' for x in a)
    def alt(a):return ''.join(('1' if x=='0' else '0') if i%2 else x for i,x in enumerate(a))
    return tuple(sorted({t for a in (bits,rev(bits)) for b in (a,alt(a)) for t in (b,flip(b))}))
def skew(bits):
    n=len(bits)
    if n%2==0:return False
    m=n//2
    return all((bits[m+j]==bits[m-j])==(j%2==0) for j in range(1,m+1))
def near_skew(bits):
    return skew(bits) if len(bits)%2 else skew(bits[:-1]) or skew(bits[1:])
def from_rle(s,n):
    a=[int(x) for x in s.strip().split()]
    if not a or sum(a)!=n:return None
    bit=1;out=''
    for length in a:
        out+=str(bit)*length
        bit=1-bit
    assert len(out)==n
    return out
def load_2004(path):
    src=path.read_text(encoding='latin-1').replace('\r','\n')
    assert 'Where possible, all sequences that achieve the maximal merit factor are listed' in src
    src=src.split('Length (N)',1)[1].split('Plot of best know merit factors',1)[0]
    candidates=collections.defaultdict(list);n=None;energy=None;row=0
    for line in src.splitlines():
        t=line.strip()
        if not t:continue
        m=re.match(r'^(\d+)\*?\s+(\d+)\s+[\d.]+\s+(.+)',t)
        if m:
            n,energy=int(m[1]),int(m[2]);fragment=m[3]
            if n not in ARCHIVE_COUNTS:continue
        elif n in ARCHIVE_COUNTS:
            fragment=t
        else:continue
        m2=re.match(r'^((?:\d+\s+)*\d+)\s*,',fragment)
        if not m2:continue
        bits=from_rle(m2[1],n)
        if bits is None:continue
        row+=1
        if exact(bits)!=energy:raise RuntimeError(f'historical RLE contradicts E {n} {energy}')
        candidates[n].append(dict(n=n,E=energy,bits=bits,canonical=orbit(bits)[0],
           source='Knauer_2004_RLE_archive',lineage='archive_optima_enumerated',source_row=row))
    for n,want in ARCHIVE_COUNTS.items():
        observed={x['canonical'] for x in candidates[n]}
        assert len(observed)==want,(n,len(observed),want)
        assert {x['E'] for x in candidates[n]}=={EXACT_REFS[n]}
    return candidates
def load_frontier(path):
    x=collections.defaultdict(list)
    for line in path.read_text().splitlines()[1:]:
        if not line:continue
        n,e,bits,src,parent,seed,near,can=line.split('\t')
        n=int(n);e=int(e)
        if n not in (92,99):continue
        assert len(bits)==n and exact(bits)==e and orbit(bits)[0]==can
        x[n].append(dict(n=n,E=e,bits=bits,canonical=can,
            source=src,lineage=parent,source_row=seed))
    assert {n:len(v) for n,v in x.items()}=={92:2,99:2}
    for n,v in x.items():assert len({r['canonical'] for r in v})==len(v)
    return x
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--archive',type=pathlib.Path,required=True)
    p.add_argument('--frontier',type=pathlib.Path,required=True)
    p.add_argument('--out',type=pathlib.Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    pool=load_2004(a.archive)
    for n,items in load_frontier(a.frontier).items():pool[n].extend(items)
    output=[];diagnostics={}
    for n in sorted(pool):
        group=pool[n]
        assert all(len(z['bits'])==n for z in group)
        assert len({z['canonical'] for z in group})==len(group)
        # All distinct physical sequences under reversal, complement and alternation.
        # Align a parent B to any of its 8 symmetry copies for *maximum* agreement.
        distances=[min(sum(c!=d for c,d in zip(a['bits'],b)) for b in orbit(z['bits']))
                   for i,a in enumerate(group) for z in group[i+1:]]
        assert distances and min(distances)>0
        baseline=min(z['E'] for z in group)
        diagnostics[str(n)]={'count':len(group),'minE':baseline,'maxE':max(z['E'] for z in group),
           'min_orbit_hamming':min(distances),'max_orbit_hamming':max(distances),
           'distinct_canonical':len({z['canonical'] for z in group}),
           'provenances':sorted(set(z['source'] for z in group)),
           'lineage_warning':'distinct source orbit is not proof of independent optimizer run'}
        for idx,z in enumerate(sorted(group,key=lambda q:(q['E'],q['canonical']))):
            output.append(dict(id=f'{n}_{idx}',**z,near=int(near_skew(z['bits'])),best_known=baseline))
    out=a.out/'parents.tsv'
    with out.open('w') as f:
        f.write('id\tn\tE\tbits\tcanonical\tsource\tlineage\tsource_row\tnear\tbest_known\n')
        for z in output:
            f.write('\t'.join(str(z[k]) for k in ('id','n','E','bits','canonical','source','lineage','source_row','near','best_known'))+'\n')
    manifest={'sources':{'Knauer_archive':'borkob/git_labs pinned 1aa123407636e48630174e0bf122037e369c1d68',
                         'frontier':'preexisting independently verified GPU-MTS/QOBLIB fixed certificates'},
              'files':{'archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),
                       'frontier_sha256':hashlib.sha256(a.frontier.read_bytes()).hexdigest(),
                       'parents_sha256':hashlib.sha256(out.read_bytes()).hexdigest()},
              'counts':diagnostics,'total_orbits':len(output),
              'no_synthetic_parents':True,
              'notes':['Known all-global-optimal N<=60 source family cannot yield strictly better child E',
               'Parent orbit independence is established; statistical optimizer-run independence is NOT established']}
    (a.out/'parent_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
