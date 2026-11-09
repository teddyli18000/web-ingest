#!/usr/bin/env python3
"""Independent O(N^2) LABS and all-eight-symmetry audit of postrepair crossover.

No invocation of C++ score, steepest, or tabu functions.
"""
import argparse,csv,hashlib,json,math,pathlib,statistics
from collections import defaultdict,Counter
import numpy as np

def E(bits):
    a=[1 if c=='1' else -1 for c in bits];n=len(bits)
    assert len(bits)==n and set(bits)<={'0','1'}
    return sum(sum(a[i]*a[i+k] for i in range(n-k))**2 for k in range(1,n))
def orbit(s):
    out=set()
    for z in (s,s[::-1]):
        for t in (z,''.join(str(int(c)^(i%2)) for i,c in enumerate(z))):
            out.add(t)
            out.add(''.join('1' if c=='0' else '0' for c in t))
    assert len(out) in (2,4,8)
    return out
def canon(s):return min(orbit(s))
def dist(a,b):return min(sum(x!=y for x,y in zip(a,t)) for t in orbit(b))
def read(path):
    with open(path,newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--parents',required=True)
    ap.add_argument('--sessions',required=True)
    ap.add_argument('--novel',required=True)
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    parents=read(a.parents);rows=read(a.sessions);nov=read(a.novel)
    byid={p['id']:p for p in parents}
    library=defaultdict(set);optimum={}
    for p in parents:
        n=int(p['n']);word=p['bits'];v=int(p['E'])
        assert len(word)==n and E(word)==v and canon(word)==p['canonical']
        assert v>=int(p['best_known'])
        library[n].add(p['canonical']);optimum[n]=int(p['best_known'])
    assert len(rows)>0
    grouping=defaultdict(dict)
    for r in rows:
        n=int(r['N']);arm=int(r['arm']);rep=int(r['rep'])
        key=(r['pair'],rep)
        assert arm not in grouping[key]
        grouping[key][arm]=r
        assert n in optimum and r['A_id'] in byid and r['B_id'] in byid
        assert int(r['evaluated'])>0 and float(r['elapsed_ms'])>0
        assert int(r['novel5'])<=int(r['novel10'])<=int(r['novel20'])
        word=r['bestBits'];v=int(r['bestE'])
        assert E(word)==v and len(word)==n and canon(word)==r['bestCanon']
        assert int(r['bestDist'])==min(dist(word,byid[r['A_id']]['bits']),dist(word,byid[r['B_id']]['bits']))
        if r['bestNovelBits']:
            assert E(r['bestNovelBits'])==int(r['bestNovelE'])
            assert canon(r['bestNovelBits'])==r['bestNovelCanon']
            assert r['bestNovelCanon'] not in library[n]
        else:
            assert int(r['bestNovelE'])==-1
    assert all(set(arms)==set(range(6)) for arms in grouping.values())
    novelBy=defaultdict(set);seen=defaultdict(set)
    for r in nov:
        key=(r['pair'],int(r['rep']),int(r['arm']))
        n=int(r['N']);bits=r['bits'];v=int(r['E']);raw=r['rawBits']
        assert len(raw)==n and E(raw)==int(r['rawE'])
        assert len(bits)==n and E(bits)==v
        assert canon(bits)==r['canonical'] and r['canonical'] not in library[n]
        assert v<=math.floor(optimum[n]*1.2+1e-12)
        assert r['canonical'] not in seen[key]
        seen[key].add(r['canonical'])
        novelBy[key].add((v,r['canonical']))
    grouped=[]
    bylength=defaultdict(list)
    for (pair,rep),arms in sorted(grouping.items()):
        perarm=[]
        for arm,row in sorted(arms.items()):
            key=(pair,rep,arm)
            vals=novelBy[key]
            assert len(vals)==int(row['novel20'])
            assert sum(v<=optimum[int(row['N'])]*1.1 for v,_ in vals)==int(row['novel10'])
            assert sum(v<=optimum[int(row['N'])]*1.05 for v,_ in vals)==int(row['novel5'])
            perarm.append(row)
        bylength[int(perarm[0]['N'])].append(perarm)
    statistics_by_n={}
    for n,instances in sorted(bylength.items()):
        methods={}
        for arm in range(6):
            vals=[v[arm] for v in instances]
            methods[str(arm)]={'meanBestE':float(np.mean([int(t['bestE']) for t in vals])),
                'meanBestNovelE':float(np.mean([int(t['bestNovelE']) for t in vals if int(t['bestNovelE'])>=0])) if any(int(t['bestNovelE'])>=0 for t in vals) else None,
                'totalNovel5':sum(int(t['novel5']) for t in vals),
                'totalNovel10':sum(int(t['novel10']) for t in vals),
                'totalNovel20':sum(int(t['novel20']) for t in vals),
                'positiveSessionsNovel10':sum(int(t['novel10'])>0 for t in vals),
                'meanRepairedCandidates':float(np.mean([int(t['evaluated']) for t in vals])),
                'meanWallMs':float(np.mean([float(t['elapsed_ms']) for t in vals])),
                'allNovelOrbits':len({ca for t in vals for v,ca in novelBy[t['pair'],int(t['rep']),arm] if v<=optimum[n]*1.1})}
        statistics_by_n[str(n)]={'pair_seed_contexts':len(instances),'arms':methods}
    # Replicates of the same source pair are NOT independent source families.
    bypair={}
    for pair in sorted(set(row['pair'] for row in rows)):
        rr=[r for r in rows if r['pair']==pair]
        arms={}
        for arm in range(6):
            z=[r for r in rr if int(r['arm'])==arm]
            arms[str(arm)]={'novel5':sum(int(r['novel5']) for r in z),
                'novel10':sum(int(r['novel10']) for r in z),
                'meanE':float(np.mean([int(r['bestE']) for r in z])),
                'meanCandidateE':float(np.mean([float(r['mean_repair_E']) for r in z]))}
        bypair[pair]=arms
    result={'exact_verification':'PASS all parent, session-final and source-novel repaired integer energies; eightfold orbit and source novelty',
        'sources':29,'full_session_rows':len(rows),'pair_seed_contexts':len(grouping),
        'source_pair_families':len(bypair),'certified_novel_rows':len(nov),
        'by_length':statistics_by_n,'by_source_pair':bypair,
        'sha256':{pathlib.Path(p).name:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
          for p in (a.parents,a.sessions,a.novel)},
        'interpretation':'Source-pair clusters not session rows are scientific replication units. Correct for multiple arms.'
    }
    output=pathlib.Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'PASS','sessions':len(rows),'pairs':len(bypair),
        'novel_rows':len(nov),
        'by_n':{n:{a:(z['totalNovel5'],z['totalNovel10'],z['meanBestE'])
           for a,z in v['arms'].items()} for n,v in statistics_by_n.items()}},indent=2))

if __name__=='__main__':main()
