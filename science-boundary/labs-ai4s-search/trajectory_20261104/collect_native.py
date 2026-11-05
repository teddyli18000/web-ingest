#!/usr/bin/env python3
"""Collect native unrestricted memetic-Tabu trajectories with per-run provenance."""
import argparse, concurrent.futures, gzip, hashlib, json, os, pathlib, re, shutil, subprocess, time

def energy(bits):
    n=len(bits)
    a=[1 if x in '+1' else -1 for x in bits]
    return sum(sum(a[j]*a[j+k] for j in range(n-k))**2 for k in range(1,n))

def run_job(spec):
    exe,output,n,seed,duration,stride,genstride=spec
    output=pathlib.Path(output);stem=f'n{n}_seed{seed}'
    outpath=output/(stem+'.tsv');logpath=output/(stem+'.stdout.txt')
    env=os.environ.copy();env.update(LABS_TRACE_FILE=str(outpath.resolve()),LABS_TRACE_STRIDE=str(stride),LABS_TRACE_GENSTRIDE=str(genstride))
    start=time.monotonic();cmd=[str(pathlib.Path(exe).resolve()),str(n),str(seed),str(duration),'1','0']
    try:
        p=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=duration+90)
    except subprocess.TimeoutExpired:
        return dict(n=n,seed=seed,error='timeout',elapsed=round(time.monotonic()-start,3))
    took=time.monotonic()-start
    logpath.write_text(p.stdout+'\n--STDERR--\n'+p.stderr)
    matches=list(re.finditer(r'BEST:([+-]{'+str(n)+r'})\s+(\d+)\s+',p.stdout))
    if p.returncode or not matches or not outpath.exists():
        return dict(n=n,seed=seed,error='solver_failed_or_missing_best',code=p.returncode,stdout_tail=p.stdout[-300:])
    best=matches[-1];bits=best.group(1);score=int(best.group(2))
    if energy(bits)!=score:
        return dict(n=n,seed=seed,error='final_solution_energy_mismatch',observed=energy(bits),claimed=score)
    rowcount=0;events={}
    with outpath.open() as f:
        hdr=f.readline().rstrip('\n').split('\t')
        assert hdr==['event','gen','episode','step','n','energy','best_energy','wall_s','seq','best_seq','tabu_remaining']
        for line in f:
            cols=line.rstrip('\n').split('\t')
            if len(cols)!=11 or len(cols[8])!=n or len(cols[9])!=n:
                raise RuntimeError(f'Malformed trace {stem} at line {rowcount+2}')
            if rowcount<200 or cols[0]=='GA_RECORD':
                if energy(cols[8])!=int(cols[5]) or energy(cols[9])!=int(cols[6]):
                    raise RuntimeError(f'Bad direct energy in {stem} event={cols[0]}')
            rowcount+=1;events[cols[0]]=events.get(cols[0],0)+1
    compressed=outpath.with_suffix('.tsv.gz')
    with outpath.open('rb') as src, gzip.open(compressed,'wb',compresslevel=6) as dst:
        shutil.copyfileobj(src,dst,1024*1024)
    outpath.unlink()
    sha=hashlib.sha256(compressed.read_bytes()).hexdigest()
    return dict(n=n,seed=seed,duration_s=duration,elapsed_s=round(took,3),score=score,
      bits=bits,events=events,total_events=rowcount,trace=compressed.name,sha256=sha,
      compressed_bytes=compressed.stat().st_size,stdout=logpath.name,threads=1,
      generation_stride=genstride,native_step_stride=stride,returncode=p.returncode)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--solver',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--lengths',default='48,64,80,92,99,100')
    parser.add_argument('--seeds',type=int,default=2)
    parser.add_argument('--duration',type=int,default=45)
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--genstride',type=int,default=4)
    parser.add_argument('--stepstride',type=int,default=32)
    parser.add_argument('--manifest',default='manifest.json')
    args=parser.parse_args()
    out=pathlib.Path(args.output);out.mkdir(parents=True,exist_ok=True)
    Ns=[int(v) for v in args.lengths.split(',')]
    jobs=[(args.solver,str(out),n,110011+n*101+rep*104729,args.duration,args.stepstride,args.genstride)
          for n in Ns for rep in range(args.seeds)]
    print('Native trajectory jobs',len(jobs),'workers',args.workers,flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        records=list(executor.map(run_job,jobs))
    d={'upstream':'borkob/git_labs/solvers/lMAts-lRRts',
       'pin':'1aa123407636e48630174e0bf122037e369c1d68',
       'source_commit':os.environ.get('LABS_SOURCE_COMMIT',''),
       'count':len(jobs),'valid':sum('error' not in v for v in records),
       'parameters':vars(args),'jobs':records}
    (out/args.manifest).write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({'count':d['count'],'valid':d['valid'],
        'events':sum(z.get('total_events',0) for z in records),
        'score_by_length':{str(n):[v['score'] for v in records if v['n']==n and 'score' in v] for n in Ns}},indent=2),flush=True)
    if d['valid']!=len(jobs):raise RuntimeError('Not all solver jobs valid')

if __name__=='__main__':main()
