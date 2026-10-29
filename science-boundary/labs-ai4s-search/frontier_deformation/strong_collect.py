"""Reproduce a published unrestricted memetic-tabu LABS baseline; no private data.

Runner downloads borkob/git_labs (GPL code stays in ephemeral runner);
source: solvers/lMAts-lRRts/src, make, ./lMAts N SEED DURATION 1 0.
The explicit target 0 suppresses early termination when it reaches known BKV.
Every returned sequence is exact-integer verified and symmetry canonicalized.
"""
import argparse, concurrent.futures, hashlib, json, pathlib, re, subprocess, time
from collections import Counter
ROOT=pathlib.Path(__file__).resolve().parent
ANCHOR=ROOT/'anchors.tsv'
NAMES={int(x.split()[0]):int(x.split()[1]) for x in ANCHOR.read_text().splitlines()}
def energy(s):
    z=[1 if c=='+' else -1 for c in s]
    return sum(sum(z[i]*z[i+k] for i in range(len(z)-k))**2 for k in range(1,len(z)))
def canonical(s):
    def negate(t):return t.translate(str.maketrans('+-','-+'))
    def alternate(t):return ''.join(c if i%2==0 else ('+' if c=='-' else '-') for i,c in enumerate(t))
    return min(z for base in (s,s[::-1]) for z in (base,negate(base),alternate(base),negate(alternate(base))))
def skew(s):
    n=len(s);m=n//2
    return n%2==1 and all(s[m+j]==(s[m-j] if j%2==0 else ('+' if s[m-j]=='-' else '-')) for j in range(1,m+1))
def near_skew(s):
    return skew(s) if len(s)%2 else skew(s[:-1]) or skew(s[1:])
def solve(exe,n,seed,sec):
    cmd=[str(exe),str(n),str(seed),str(sec),'1','0']
    t=time.monotonic()
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=sec+25)
    except subprocess.TimeoutExpired:
        return {'n':n,'seed':seed,'error':'timeout','runtime':time.monotonic()-t}
    m=list(re.finditer(r'(?<![+-])([+-]{%d})\s+(\d+)\s+([0-9]+(?:\.[0-9]+)?)' % n,p.stdout))
    if p.returncode or not m:
        return {'n':n,'seed':seed,'error':'solver failure or unparsed output','code':p.returncode,'stdout_tail':p.stdout[-300:],'stderr_tail':p.stderr[-300:]}
    match=m[-1];bits=match.group(1);e=energy(bits)
    if e!=int(match.group(2)):
        return {'n':n,'seed':seed,'error':'independent energy mismatch','reported':match.group(2),'actual':e}
    return {'n':n,'seed':seed,'seconds':round(time.monotonic()-t,3),
        'energy':e,'bits':bits,'canonical':canonical(bits),'near_skew':near_skew(bits),
        'reference':NAMES[n], 'relative_gap':round((e-NAMES[n])/NAMES[n],5)}
def main():
    a=argparse.ArgumentParser();a.add_argument('--solver',required=True);a.add_argument('--duration',type=int,default=25)
    a.add_argument('--seeds',type=int,default=4);a.add_argument('--workers',type=int,default=4)
    a.add_argument('--out',default='results/2026-10-29-strong-corpus')
    opt=a.parse_args();exe=pathlib.Path(opt.solver).resolve()
    jobs=[(exe,n,10001+seed*1747+n*97,opt.duration) for n in [80,92,96,99,100] for seed in range(opt.seeds)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=opt.workers) as pool: result=list(pool.map(lambda x:solve(*x),jobs))
    result=sorted(result,key=lambda x:(x['n'],x['seed']))
    unique={}
    for r in result:
        if 'energy' in r:
            key=(r['n'],r['canonical'])
            if key not in unique or r['energy']<unique[key]['energy']:unique[key]=r
    target=ROOT/opt.out;target.parent.mkdir(parents=True,exist_ok=True)
    fields=['n','energy','bits','provenance','parent','seed','near_skew','canonical']
    with target.with_suffix('.tsv').open('w') as f:
        f.write('\t'.join(fields)+'\n')
        for r in sorted(unique.values(),key=lambda q:(q['n'],q['energy'],q['canonical'])):
            f.write('\t'.join(map(str,[r['n'],r['energy'],r['bits'].replace('+','1').replace('-','0'),
                'published_lMAts','none',r['seed'],int(r['near_skew']),
                r['canonical'].replace('+','1').replace('-','0')]))+'\n')
    verified=sum('energy' in x for x in result)
    meta={'source_repository':'https://github.com/borkob/git_labs','source_subdir':'solvers/lMAts-lRRts/src',
        'source_license':'GPL (source not copied)','solver_revision_recorded_externally':None,
        'duration_per_job_sec':opt.duration,'workers':opt.workers,'planned_jobs':len(jobs),
        'verified_jobs':verified,'unique_symmetry_classes':len(unique),
        'results':[{k:v for k,v in r.items() if k not in ('bits','canonical')} for r in result],
        'low_relative_gap_leq_0_2':sum(r.get('relative_gap',10)<=0.2 for r in result),
        'IMPORTANT':'This is the published 2009-era lMAts implementation, not the 2025 GPU MTS.'}
    target.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({'jobs':len(jobs),'verified':verified,'unique':len(unique),'gap<=20%':meta['low_relative_gap_leq_0_2']}))
    if verified!=len(jobs):raise RuntimeError('some jobs failed; inspect meta JSON')
if __name__=='__main__':main()
