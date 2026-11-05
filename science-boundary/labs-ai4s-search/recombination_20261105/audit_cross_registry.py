#!/usr/bin/env python3
"""Audit child novelty against UNION of preexisting historical archive and fresh
independent native-seed parents, not just the active experiment's source pool.
No claim of mathematical novelty: source registry is finite and public.
"""
import csv,hashlib,json,pathlib,collections
BASE=pathlib.Path(__file__).resolve().parent
def read(p):
    with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def energy(s):
    v=[2*int(c)-1 for c in s];n=len(v)
    return sum(sum(v[i]*v[i+k] for i in range(n-k))**2 for k in range(1,n))
def canon(s):
    neg=lambda q:''.join('1' if c=='0' else '0' for c in q)
    alt=lambda q:''.join(c if i%2==0 else ('1' if c=='0' else '0') for i,c in enumerate(q))
    return min(z for b in (s,s[::-1]) for t in (b,alt(b)) for z in (t,neg(t)))
def main():
    roots=[BASE/'data/parents.tsv',BASE/'data/native_10pct_parents.tsv',
           BASE/'data/native_independent_2009_v1/independent_highquality_orbits.tsv']
    referenced=collections.defaultdict(set)
    for path in roots:
        for r in read(path):
            n=int(r['n']);e=int(r['E']);b=r['bits']
            assert energy(b)==e and canon(b)==r['canonical']
            referenced[n].add(r['canonical'])
    datasets={'archive_children':BASE/'results/new_source_orbits_v1.tsv',
              'native_children':BASE/'results/native_10pct_new_orbits_v1.tsv'}
    seen=collections.defaultdict(dict);out={}
    for group,path in datasets.items():
        rows=read(path)
        unique={}
        for r in rows:
            n=int(r['N']);e=int(r['E']);b=r['bits'];can=r['canonical']
            assert energy(b)==e and canon(b)==can
            k=(n,can)
            assert k not in unique or unique[k]['E']==e
            unique[k]={'N':n,'E':e,'canonical':can}
        new={k:v for k,v in unique.items() if k[1] not in referenced[k[0]]}
        out[group]={'rows':len(rows),'distinct_orbits':len(unique),
            'distinct_orbits_absent_from_all_parent_registries':len(new),
            'known_parent_registry_rediscoveries':len(unique)-len(new),
            'new_energy_classes':sorted({(n,e) for (n,_),z in new.items() for e in [z['E']]}),
            'new_orbits':sorted(new.values(),key=lambda z:(z['N'],z['E'],z['canonical']))}
        seen[group]=new
    combined=dict(seen['archive_children'])
    combined.update(seen['native_children'])
    out['combined']={'distinct_not_in_parent_registry':len(combined),
                     'by_length':{str(n):len([1 for (m,_),v in combined.items() if m==n]) for n in sorted(set(n for n,_ in combined))},
                     'caveat':'Absent from a finite parent registry is not a claim of first discovery, new global optimum, or independent generation lineage'}
    dest=BASE/'results/cross_registry_novelty_audit.json'
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:{z:y for z,y in v.items() if z!='new_orbits'} for k,v in out.items()},indent=2))
if __name__=='__main__':main()
