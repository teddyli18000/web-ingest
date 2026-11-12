#!/usr/bin/env python3
"""Independent native memetic-tabu LABS-100 parent harvest.

Pinned historical unrestricted lMAts is run only as a source of independent
candidate lineages. Every terminal certificate is rescored by a second exact
99-lag integer implementation and normalized under the eight LABS symmetries.
Not the 2025 GPU MTS implementation.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import pathlib
import re
import subprocess
import time

N=100
RECORD=578

def energy(s):
    a=[1 if c=='+' else -1 for c in s]
    return sum(sum(a[i]*a[i+k] for i in range(N-k))**2 for k in range(1,N))

def canonical(s):
    t=str.maketrans('+-','-+')
    orbit=[]
    for r in (s,s[::-1]):
        for a in (r,''.join(c if i%2==0 else c.translate(t) for i,c in enumerate(r))):
            orbit.extend((a,a.translate(t)))
    return min(orbit)

def run(exe,seed,duration):
    start=time.monotonic()
    proc=subprocess.run([str(exe),str(N),str(seed),str(duration),'1','0'],
                        capture_output=True,text=True,timeout=duration+65)
    matches=list(re.finditer(r'(?<![+-])([+-]{100})\s+(\d+)\s+([0-9]+(?:\.[0-9]+)?)',proc.stdout))
    assert proc.returncode==0 and matches,(proc.returncode,proc.stdout[-400:],proc.stderr[-400:])
    s,printed=matches[-1].group(1),int(matches[-1].group(2))
    e=energy(s)
    assert e==printed,(seed,e,printed)
    return dict(seed=seed,seconds=duration,elapsed_s=round(time.monotonic()-start,2),
                energy=e,sequence=s,canonical=canonical(s),
                source_pin='borkob/git_labs@1aa123407636e48630174e0bf122037e369c1d68',
                stdout_sha256=hashlib.sha256(proc.stdout.encode()).hexdigest())

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--exe',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--shard',type=int,required=True)
    p.add_argument('--seconds',type=int,default=900)
    p.add_argument('--workers',type=int,default=4)
    a=p.parse_args()
    seeds=[2026111201+1009*(4*a.shard+i) for i in range(a.workers)]
    with ThreadPoolExecutor(max_workers=a.workers) as executor:
        rows=list(executor.map(lambda seed:run(a.exe,seed,a.seconds),seeds))
    out=dict(length=N,shard=a.shard,source_pin='1aa123407636e48630174e0bf122037e369c1d68',
             runs=len(rows),independent_seed_orbits=len({z['canonical'] for z in rows}),
             public_record=RECORD,target=574,best_energy=min(z['energy'] for z in rows),
             best_sequence=min(rows,key=lambda z:z['energy'])['sequence'],rows=rows)
    path=pathlib.Path(a.out);path.mkdir(parents=True,exist_ok=True)
    (path/f'shard-{a.shard}.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))

if __name__=='__main__':
    main()
