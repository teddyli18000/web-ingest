"""Cost-normalized fixed-Hamming mask-search comparison: three true controls."""
import csv,json,pathlib,sys
import numpy as np
rows=list(csv.DictReader(open(sys.argv[1]),delimiter='\t'))
by={}
for r in rows:
    key=(int(r['id']),int(r['n']),int(r['sourceE']),int(r['rep']))
    by.setdefault(key,{})[int(r['method'])]=r
assert all(set(v)=={0,1,2} for v in by.values())
out={}
for q,n,e in sorted(set(k[:3] for k in by)):
    sub=[v for k,v in by.items() if k[:3]==(q,n,e)]
    xs={i:np.array([int(z[i]['bestE']) for z in sub]) for i in range(3)}
    post={i:np.array([int(z[i]['postRelaxE']) for z in sub]) for i in range(3)}
    scored={i:np.array([int(z[i]['proposals']) for z in sub]) for i in range(3)}
    def comp(i,j):
        delta=xs[j]-xs[i]
        rng=np.random.default_rng(20261104+q*11+i*3+j)
        boot=delta[rng.integers(len(delta),size=(5000,len(delta)))].mean(axis=1)
        return {'lower_is_better_mean_E_gain':float(delta.mean()),
            'CI95_seed_bootstrap':list(map(float,np.quantile(boot,[.025,.975]))),
            'win_tie_loss':[int((delta>0).sum()),int((delta==0).sum()),int((delta<0).sum())]}
    k=f'state{q}_N{n}_E{e}'
    out[k]={'best_mean_E':{str(i):float(a.mean()) for i,a in xs.items()},
            'post_relax_mean_E':{str(i):float(a.mean()) for i,a in post.items()},
            'mean_scored_proposals':{str(i):float(a.mean()) for i,a in scored.items()},
            'swaps_vs_fresh_uniform':comp(1,0),
            'swaps_vs_uniform_mask_walk':comp(1,2),
            'uniform_mask_walk_vs_fresh_uniform':comp(2,0)}
    print(k,'best E',out[k]['best_mean_E'],'proposals',out[k]['mean_scored_proposals'],
          'swap-vs-walk',out[k]['swaps_vs_uniform_mask_walk'])
pathlib.Path(sys.argv[2]).write_text(json.dumps({'methods':{
    '0':'fresh exact uniform Hamming-12 masks',
    '1':'local improving mask-space swap, occasional mask restart',
    '2':'stationary-uniform mask-space random walk, same 2-flip evaluation cost'},
    'scope':'Only candidate-level quality. Retrospective quench NOT charged and NOT solver performance.',
    'results':out},indent=2)+'\n')
