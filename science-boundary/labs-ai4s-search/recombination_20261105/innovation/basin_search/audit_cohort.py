#!/usr/bin/env python3
"""Independent exact scorer and orbit-distance audit of genuine elite parent cohort."""
import csv,hashlib,json,pathlib,collections,argparse,statistics

def inv(s):return ''.join('1' if c=='0' else '0' for c in s)
def alt(s):return ''.join(inv(c) if i%2 else c for i,c in enumerate(s))
def orbit(s):return sorted(set(q for z in (s,s[::-1]) for q in (z,inv(z),alt(z),inv(alt(z)))))
def energy(s):
    a=[1 if c=='1' else -1 for c in s];n=len(a)
    return sum(sum(a[i]*a[i+k] for i in range(n-k))**2 for k in range(1,n))
def hd(a,b):return sum(x!=y for x,y in zip(a,b))
def main():
    p=argparse.ArgumentParser();p.add_argument('parents');p.add_argument('--output',required=True)
    a=p.parse_args();content=pathlib.Path(a.parents).read_bytes()
    rows=list(csv.DictReader(content.decode().splitlines(),delimiter='\t'))
    groups=collections.defaultdict(list)
    assert len(rows)==29
    for r in rows:
        n=int(r['n']);s=r['bits']
        assert len(s)==n and energy(s)==int(r['E'])
        assert min(orbit(s))==r['canonical']
        assert int(r['E'])>=int(r['best_known'])
        groups[n].append(r)
    assert {n:len(z) for n,z in groups.items()}=={46:3,47:6,50:4,59:6,60:6,92:2,99:2}
    data={}
    for n,grp in sorted(groups.items()):
        pairs=[]
        for i in range(len(grp)):
            for j in range(i+1,len(grp)):
                x,y=grp[i],grp[j]
                d=min(hd(x['bits'],z) for z in orbit(y['bits']))
                assert d>0
                pairs.append({'A':x['id'],'B':y['id'],'orbitHamming':d,
                    'energyDifference':abs(int(x['E'])-int(y['E']))})
        v=sorted(z['orbitHamming'] for z in pairs)
        data[str(n)]={'source_orbits':len(grp),'known_best_E':int(grp[0]['best_known']),
            'exact_best_orbits':sum(int(z['E'])==int(z['best_known']) for z in grp),
            'energy_range':[min(int(z['E']) for z in grp),max(int(z['E']) for z in grp)],
            'pairs':len(pairs),'orbit_hamming_range':[v[0],v[-1]],
            'median_orbit_hamming':float(statistics.median(v)),
            'source_kinds':sorted(set(z['source'] for z in grp)),'pair_details':pairs}
    assert data['99']['orbit_hamming_range']==[41,41]
    assert data['92']['orbit_hamming_range']==[38,38]
    r={'parent_file_sha256':hashlib.sha256(content).hexdigest(),'total_unique_parent_orbits':29,
       'by_length':data,
       'warning':'An archive optimum is a distinct genetic orbit but may not be a separately documented optimizer execution; do not conflate orbit and independent solver seed. N92 and N99 each contain only one cross-source pair. No second independent N100 E578 parent is available.'}
    o=pathlib.Path(a.output);o.parent.mkdir(parents=True,exist_ok=True)
    o.write_text(json.dumps(r,indent=2)+'\n')
    print('PASS 29 exact LABS parent scores, 8-fold orbits and pairwise distance audit')
if __name__=='__main__':main()
