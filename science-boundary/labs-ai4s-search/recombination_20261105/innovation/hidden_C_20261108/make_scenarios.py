#!/usr/bin/env python3
"""Prepare locked A/B/X inputs and separate oracle C vaults.

N46 train, N47 validation, N50 final TEST generated in a later workflow only
AFTER model hash is frozen. Solver never opens vault, no C string in inputs.
"""
import argparse,csv,hashlib,json,pathlib,random,collections

def neg(s):return ''.join('1' if c=='0' else '0' for c in s)
def alt(s):return ''.join(neg(c) if i%2 else c for i,c in enumerate(s))
def orbit(s):return sorted(set(v for z in (s,s[::-1]) for v in (z,neg(z),alt(z),neg(alt(z)))))
def canon(s):return orbit(s)[0]
def hamming(a,b):return sum(x!=y for x,y in zip(a,b))
def sym_align(a,b):return min(orbit(b),key=lambda z:(hamming(a,z),z))
def flip(s,positions):
    s=list(s)
    for i in positions:s[i]=neg(s[i])
    return ''.join(s)
def E(s):
    a=[1 if c=='1' else -1 for c in s];n=len(s)
    return sum(sum(a[i]*a[i+k] for i in range(n-k))**2 for k in range(1,n))
def blind_intermediate(a,b,k,rng):
    """Do NOT add or consult target C. A/B provenance only."""
    bb=sym_align(a,b)
    d=[i for i in range(len(a)) if a[i]!=bb[i]]
    q=[i for i in range(len(a)) if a[i]==bb[i]]
    n_d=min(len(d)//2,max(1,k//2))
    n_q=k-n_d
    assert len(q)>=n_q and len(d)>=n_d
    return flip(a,rng.sample(d,n_d)+rng.sample(q,n_q))
def c_shell_intermediate(a,c,k,rng):
    """Purposefully privileged diagnostic, never label as A/B-blind."""
    aligned=sym_align(a,c)
    return flip(aligned,rng.sample(range(len(a)),k))
def write(path,records,columns):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns,delimiter='\t');w.writeheader();w.writerows(records)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('parents');p.add_argument('--lengths',required=True)
    p.add_argument('--out',required=True);p.add_argument('--reps',type=int,default=8)
    p.add_argument('--rep-offset',type=int,default=0)
    a=p.parse_args()
    lengths=[int(n) for n in a.lengths.split(',')]
    parents=collections.defaultdict(list)
    with open(a.parents,newline='') as f:
        for r in csv.DictReader(f,delimiter='\t'):
            n=int(r['n'])
            if n not in lengths or int(r['E'])!=int(r['best_known']):continue
            assert E(r['bits'])==int(r['E']) and canon(r['bits'])==r['canonical']
            parents[n].append(r)
    expected={46:3,47:6,50:3}
    assert all(len(parents[n])==expected[n] for n in lengths)
    public=[];vault=[]
    for n in lengths:
        group=sorted(parents[n],key=lambda z:z['id'])
        for i in range(len(group)):
            A=group[i];B=group[(i+1)%len(group)];C=group[(i+2)%len(group)]
            assert len({A['canonical'],B['canonical'],C['canonical']})==3
            for rep in range(a.rep_offset,a.rep_offset+a.reps):
                for k in (4,8,12):
                    for mode in ('AB_blind','C_shell'):
                        sid=f'n{n}_tri{i}_rep{rep}_k{k}_{mode}'
                        seed=int(hashlib.sha256(sid.encode()).hexdigest()[:16],16)
                        rng=random.Random(seed)
                        X=(blind_intermediate(A['bits'],B['bits'],k,rng) if mode=='AB_blind'
                           else c_shell_intermediate(A['bits'],C['bits'],k,rng))
                        assert len(X)==n and canon(X) not in {A['canonical'],B['canonical'],C['canonical']}
                        e=E(X);assert e>=int(A['E'])
                        public.append(dict(id=sid,n=n,A=A['bits'],B=B['bits'],X=X,
                            A_orbit=A['canonical'],B_orbit=B['canonical'],
                            A_id=A['id'],B_id=B['id'],mode=mode,damage=k,
                            rep=rep,seed=seed,EX=e,
                            dA=min(map(lambda s:hamming(s,X),orbit(A['bits']))),
                            dB=min(map(lambda s:hamming(s,X),orbit(B['bits']))))
                        vault.append(dict(id=sid,n=n,C_id=C['id'],C=C['bits'],
                            C_orbit=C['canonical'],C_energy=int(C['E']),
                            dC=min(map(lambda s:hamming(s,X),orbit(C['bits'])))))
    out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
    inputcols=['id','n','A','B','X','A_orbit','B_orbit','A_id','B_id','mode','damage','rep','seed','EX','dA','dB']
    vaultcols=['id','n','C_id','C','C_orbit','C_energy','dC']
    write(out/'scenario-input.tsv',public,inputcols)
    write(out/'target-vault.tsv',vault,vaultcols)
    inp=(out/'scenario-input.tsv').read_bytes();hidden=(out/'target-vault.tsv').read_bytes()
    assert 'C_orbit' not in inp.decode() and 'C_id' not in inp.decode()
    manifest={'lengths':lengths,'count':len(public),'reps':a.reps,
       'rep_range':[a.rep_offset,a.rep_offset+a.reps-1],
       'regimes':{'AB_blind':sum(z['mode']=='AB_blind' for z in public),
                  'C_shell':sum(z['mode']=='C_shell' for z in public)},
       'input_sha256':hashlib.sha256(inp).hexdigest(),
       'vault_sha256':hashlib.sha256(hidden).hexdigest(),
       'warning':'C_shell is a privileged oracle-rooted denoising control, not blind basin discovery; never pass vault to solver'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
