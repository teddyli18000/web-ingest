"""Paired fixed-Hamming macro proposal evidence, NOT end-to-end solver performance."""
import csv,json,pathlib,sys
import numpy as np
d=list(csv.DictReader(open(sys.argv[1]),delimiter='\t'))
by={}
for a in d:
    key=(int(a['id']),int(a['n']),int(a['sourceE']),int(a['rep']))
    by.setdefault(key,{})[int(a['method'])]=a
assert all(set(v)=={0,1} for v in by.values())
out={}
for key in sorted(set(t[:3] for t in by)):
    q,n,e=key
    rows=[v for (qq,nn,ee,r),v in by.items() if (qq,nn,ee)==key]
    x=np.array([int(v[0]['bestE']) for v in rows])
    y=np.array([int(v[1]['bestE']) for v in rows])
    postx=np.array([int(v[0]['postRelaxE']) for v in rows])
    posty=np.array([int(v[1]['postRelaxE']) for v in rows])
    delta=x-y
    rng=np.random.default_rng(20261104+q)
    boot=delta[rng.integers(len(delta),size=(5000,len(delta)))].mean(axis=1)
    o={'sourceE':e,'n':n,'reps':len(rows),
        'random_meanE':float(x.mean()),'swap_meanE':float(y.mean()),
        'gain_mean':float(delta.mean()),'paired_bootstrap95':np.quantile(boot,[.025,.975]).tolist(),
        'wins_ties_losses':[int((delta>0).sum()),int((delta==0).sum()),int((delta<0).sum())],
        'random_relax_meanE':float(postx.mean()),'swap_relax_meanE':float(posty.mean()),
        'swap_nonidentical_postrelax':int(sum(int(v[1]['postDistance'])>0 for v in rows)),
        'random_nonidentical_postrelax':int(sum(int(v[0]['postDistance'])>0 for v in rows)),
        'random_proposals':float(np.mean([int(v[0]['proposals']) for v in rows])),
        'swap_proposals':float(np.mean([int(v[1]['proposals']) for v in rows]))}
    out[f'id{q}_N{n}_E{e}']=o
    print(q,n,e,'random',round(x.mean(),2),'swap',round(y.mean(),2),
          'improvement over random',round(delta.mean(),2),'CI',o['paired_bootstrap95'],
          'postrelax same-parent counts',(len(rows)-o['swap_nonidentical_postrelax']),
          'proposals',round(o['random_proposals']),round(o['swap_proposals']))
path=pathlib.Path(sys.argv[2]);path.write_text(json.dumps({'scope':'exactly Hamming-12, equal time; local-repair retrospective only, no deployed solver','results':out},indent=2)+'\n')
