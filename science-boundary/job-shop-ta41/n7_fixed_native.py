#!/usr/bin/env python3
"""Audit original author N7 run with a FIXED (not timed) iteration limit."""
import csv,subprocess
from pathlib import Path
from search import evaluate

def original_n7_fixed(binary,instance_file,orders,pos,dur,seed,iterations,tmpdir):
    warm=Path(tmpdir)/'warm-orders-fixed.txt'
    native=Path(tmpdir)/'operations-fixed.csv'
    warm.write_text('\n'.join(' '.join(map(str,row)) for row in orders)+'\n')
    cmd=[str(binary),str(instance_file),str(native),str(iterations),str(seed),str(warm)]
    p=subprocess.run(cmd,capture_output=True,text=True,check=False,timeout=120)
    assert p.returncode==0,(cmd,p.stdout,p.stderr[-1400:])
    z=p.stdout.strip().split()
    assert len(z)==6 and z[0]=='RESULT',z
    score,used,seconds,startscore,limit=int(z[1]),int(z[2]),float(z[3]),int(z[4]),int(z[5])
    assert limit==iterations and used>=iterations,(used,iterations)
    assert startscore==evaluate(orders,pos,dur)
    bymachine=[[] for _ in range(20)]
    seen=set()
    with native.open() as f:
        for x in csv.DictReader(f):
            j=int(x['Job'])-1;k=int(x['Operation'])-1;m=int(x['Machine'])
            start=int(x['StartTime']);end=int(x['EndTime'])
            assert (j,k) not in seen and 0<=j<30 and 0<=k<20
            assert pos[j][m]==k and end-start==dur[j*20+k]
            seen.add((j,k));bymachine[m].append((start,j))
    assert len(seen)==600 and all(len(x)==30 for x in bymachine)
    result=[[j for _,j in sorted(items)] for items in bymachine]
    actual=evaluate(result,pos,dur)
    assert actual==score and score<=startscore
    return {'initial':startscore,'best':score,'iterations':used,
            'native_seconds':seconds,'exact_DAG_verified':True},result
