#!/usr/bin/env python3
"""Public Nagata-vs-strong-algorithm tour disagreement × Concorde fractional LP.

Inputs are ORIGINAL Mona Lisa Challenge public data, not an inferred LP.
- Tours are TSPLIB explicit TOUR_SECTION 1-based city IDs.
- Concorde mona.{4z,5z,6n}sub.x files have header n m, and m lines
  with ZERO-BASED city IDs and primal edge x∈[0,1].
- Every tour is independently evaluated by the Few Shots official verifier.
- LP edges and vertex degrees are independently audited for feasibility.
- Spatially stratified permutation tests check whether overlap persists
  after controlling for the spatial layout / city density.
"""
import argparse, hashlib, importlib.util, json, math, os
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

N=100000
def ek(a,b):return (a,b) if a<b else (b,a)
def parse_tour(path):
    lines=Path(path).read_text().splitlines()
    at=next(i for i,x in enumerate(lines) if x.strip().upper()=='TOUR_SECTION')
    t=[]
    for line in lines[at+1:]:
        for tok in line.split():
            if tok in ('-1','EOF'):return np.asarray(t,dtype=np.int32)
            t.append(int(tok)-1)
    raise ValueError('Missing TOUR terminator '+str(path))
def encode(u,v):
    a=np.minimum(u,v).astype(np.int64)
    b=np.maximum(u,v).astype(np.int64)
    return a*N+b
def tour_edges(t):return encode(t,np.roll(t,-1))
def tour_neigh(t):
    a=np.empty(N,dtype=np.int32);b=np.empty(N,dtype=np.int32)
    a[t]=np.roll(t,1);b[t]=np.roll(t,-1)
    return np.minimum(a,b),np.maximum(a,b)
def lp_read(path):
    with Path(path).open() as f:
        header=list(map(int,f.readline().split()))
        assert header[0]==N and header[1]>N
        data=np.loadtxt(f,dtype=np.float64)
    assert data.shape==(header[1],3),(path,data.shape,header)
    u=data[:,0].astype(np.int32);v=data[:,1].astype(np.int32);x=data[:,2]
    assert (u>=0).all() and (v>=0).all() and (u<N).all() and (v<N).all()
    assert (u!=v).all() and (x>=-1e-6).all() and (x<=1+1e-6).all()
    ids=encode(u,v)
    assert len(np.unique(ids))==len(ids),'duplicate LP edge'
    degree=np.bincount(np.r_[u,v],weights=np.r_[x,x],minlength=N)
    err=np.abs(degree-2)
    assert err.max()<5e-4,('LP degree equations fail',path,float(err.max()))
    fraction=(x>1e-5)&(x<1-1e-5)
    node_fraction=np.zeros(N,dtype=np.bool_)
    node_fraction[u[fraction]]=True;node_fraction[v[fraction]]=True
    frac_mass=np.bincount(np.r_[u,v],weights=np.r_[x*(1-x),x*(1-x)],minlength=N)
    return {'u':u,'v':v,'x':x,'edge_ids':ids,'frac':fraction,'node_frac':node_fraction,
            'frac_mass':frac_mass,'degree_max_error':float(err.max()),
            'edge_count':len(x),'fractional_edges':int(fraction.sum()),
            'fractional_nodes':int(node_fraction.sum()),
            'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}
def permute_by_cell(labels,groups,target,rng,B=300):
    obs=int(np.sum(labels&target))
    expected=0.
    samples=np.empty(B,dtype=np.int32)
    for j in range(B):
        total=0
        for ids in groups:
            if len(ids)<=1:total+=int(labels[ids[0]]&target[ids[0]]) if len(ids) else 0;continue
            # Under the within-cell null, preserve exact number of target positives.
            count=int(target[ids].sum())
            if count:
                chosen=rng.choice(ids,size=count,replace=False)
                total+=int(labels[chosen].sum())
        samples[j]=total
    return {'observed':obs,'null_mean':round(float(samples.mean()),3),
            'null_sd':round(float(samples.std(ddof=1)),3),
            'fold_vs_null_mean':round(obs/max(1e-9,float(samples.mean())),4),
            'empirical_p_ge':round(float((1+(samples>=obs).sum())/(B+1)),6),
            'permutations':B}
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--baseline',required=True)
    p.add_argument('--tours',required=True,help='JSON mapping name to TSPLIB tour path')
    p.add_argument('--lps',required=True,help='JSON mapping snapshot to .x path')
    p.add_argument('--out',required=True)
    p.add_argument('--map',required=True)
    p.add_argument('--regions',required=True)
    p.add_argument('--cells',type=int,default=24)
    a=p.parse_args()
    spec=importlib.util.spec_from_file_location('verify',Path(os.environ['FEWSHOTS_ROOT'])/
         'problems/p010-mona-lisa-tsp/verify/verify.py')
    verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
    xs,ys=verify.coordinates()
    assert len(xs)==N and len(ys)==N
    base=np.asarray(json.loads(Path(a.baseline).read_text())['tour'],dtype=np.int32)-1
    assert len(base)==N and np.array_equal(np.sort(base),np.arange(N))
    assert verify.tour_length((base+1).tolist())==5757191
    base_a,base_b=tour_neigh(base)
    base_edges=tour_edges(base)
    assert len(np.unique(base_edges))==N
    tours=json.loads(Path(a.tours).read_text())
    overview=[]
    different=np.zeros(N,dtype=np.int16)
    edge_votes=Counter()
    raw_changes={}
    for name,path in tours.items():
        t=parse_tour(path)
        assert len(t)==N and np.array_equal(np.sort(t),np.arange(N)),name
        score=verify.tour_length((t+1).tolist())
        digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
        ta,tb=tour_neigh(t)
        delta=(ta!=base_a)|(tb!=base_b)
        different+=delta.astype(np.int16)
        te=tour_edges(t)
        shared=int(np.isin(base_edges,te).sum())
        raw_changes[name]=delta
        for item in te:edge_votes[int(item)]+=1
        overview.append({'name':name,'score':score,'sha256':digest,
          'shared_edges_with_nagata':shared,'changed_edges_with_nagata':N-shared,
          'changed_vertices_with_nagata':int(delta.sum()),
          'changed_vertex_fraction':round(float(delta.mean()),7)})
    M=len(tours)
    assert M>=4
    lp_paths=json.loads(Path(a.lps).read_text())
    lps={name:lp_read(path) for name,path in lp_paths.items()}
    # Choose strongest historical public snapshot as the primary LP signal.
    assert '2012-04-18' in lps
    primary=lps['2012-04-18']
    lp_frac=primary['node_frac']
    persistent=np.ones(N,dtype=np.bool_)
    for v in lps.values():persistent &=v['node_frac']
    coords=np.column_stack((xs,ys))
    low=coords.min(axis=0);high=coords.max(axis=0)
    denom=np.maximum(high-low,1)
    bins=np.floor((coords-low)/denom*a.cells).astype(np.int32)
    bins=np.clip(bins,0,a.cells-1)
    cell_ids=bins[:,0]*a.cells+bins[:,1]
    groups=[np.flatnonzero(cell_ids==i) for i in range(a.cells*a.cells)]
    rng=np.random.default_rng(20261029)
    thresholds=[1,2,3,max(1,M//2),M]
    tests={}
    for k in sorted(set(thresholds)):
        selector=different>=k
        tests[str(k)]={
         'disagreement_nodes':int(selector.sum()),
         'fraction_nodes_intersection':int(np.sum(selector&lp_frac)),
         'fraction_node_rate_given_disagreement':round(float(lp_frac[selector].mean()),6) if selector.any() else None,
         'fraction_node_rate_given_no_disagreement':round(float(lp_frac[~selector].mean()),6) if (~selector).any() else None,
         'stratified_null':permute_by_cell(selector,groups,lp_frac,rng)}
    # Negative control: fix a sample-preserving 51-switch subfamily and test
    # whether LP fractionality is already concentrated near neutral move sites.
    rows=[]
    for i in range(a.cells*a.cells):
        ids=groups[i]
        if len(ids)<20:continue
        disagree=np.sum(different[ids]>=2)
        fract=np.sum(lp_frac[ids])
        co=np.sum((different[ids]>=2)&lp_frac[ids])
        strong=np.sum(different[ids]>=max(1,M//2))
        value=float(co/max(1,len(ids)))/max(1e-5,float((disagree/max(1,len(ids)))*(fract/max(1,len(ids)))))
        rows.append({'cell_x':i//a.cells,'cell_y':i%a.cells,'n':len(ids),
           'disagreement_2plus':int(disagree),'fraction_lp_nodes':int(fract),
           'overlap_2plus_and_fraction':int(co),
           'strong_disagreement_nodes':int(strong),
           'overlap_rate':round(float(co/len(ids)),5),
           'independent_expected':round(float(disagree*fract/len(ids)),3),
           'lift_vs_cell_independence':round(value,3),
           'mean_x':round(float(coords[ids,0].mean()),2),
           'mean_y':round(float(coords[ids,1].mean()),2)})
    rows.sort(key=lambda x:(-x['overlap_2plus_and_fraction'],-x['overlap_rate']))
    # Edge votes frequency and LP support alignment.
    votes=np.fromiter(edge_votes.keys(),dtype=np.int64)
    counts=np.fromiter(edge_votes.values(),dtype=np.int32)
    freq=Counter(counts.tolist())
    vote_map=dict(edge_votes)
    lp_edge=dict(zip(primary['edge_ids'].tolist(),primary['x'].tolist()))
    edge_stats={}
    for label,edges in [('nagata',base_edges),
                         ('all_historical_edge_union',votes)]:
        values=np.fromiter((lp_edge.get(int(e),0) for e in edges),dtype=np.float64,count=len(edges))
        edge_stats[label]={'edge_count':len(edges),
            'LP_x_zero_or_absent':int((values<1e-5).sum()),
            'LP_x_fractional':int(((values>1e-5)&(values<1-1e-5)).sum()),
            'LP_x_one':int((values>=1-1e-5).sum())}
    edge_stats['historical_edge_frequency_histogram']={str(k):int(v) for k,v in sorted(freq.items())}
    pair=[]
    tours_sets={name:set(tour_edges(parse_tour(path)).tolist()) for name,path in tours.items()}
    for i,n1 in enumerate(tours):
        for n2 in list(tours)[i+1:]:
            joint=len(tours_sets[n1]&tours_sets[n2])
            pair.append({'a':n1,'b':n2,'shared_edges':joint,'edge_difference_each':N-joint})
    stable=sorted(set.intersection(set(base_edges.tolist()),*tours_sets.values()))
    known_frac_lp_edges=primary['edge_ids'][primary['frac']]
    frac_vote={str(k):int(np.sum(np.isin(known_frac_lp_edges,np.fromiter((e for e in vote_map if vote_map[e]>=k),dtype=np.int64))))
               for k in (1,2,M)}
    overview_lps={key:{k:v[k] for k in ('edge_count','fractional_edges','fractional_nodes',
         'degree_max_error','sha256')} for key,v in lps.items()}
    out={'sources':{'tours':tours,'lps':lp_paths,
                   'lp_format':'0-based endpoint IDs, primal x in [0,1]',
                   'tour_format':'1-based TSPLIB tour'},
       'n':N,'tour_count':M,'lp_snapshots':overview_lps,
       'tour_statistics':overview,'pairwise_tour_statistics':pair,
       'Nagata_stable_edges_all_tours':len(stable),
       'Nagata_edges_changed_in_at_least_one_tour':N-len(stable),
       'edge_statistics':edge_stats,'fractional_lp_edge_in_historical_tour_votes':frac_vote,
       'lp_fractional_node_rate':round(float(lp_frac.mean()),6),
       'persistent_fractional_nodes_all_lp_snapshots':int(persistent.sum()),
       'tour_disagreement_threshold_tests':tests,'top_regions':rows[:60],
       'spatial_permutation_note':'Within rectangular grid cells, LP fractional node labels are shuffled, preserving each cell marginal. This tests local overlap beyond coarse spatial co-location, not causality.',
       'claim_limit':'LP x values are a single Concorde primal solution, not probabilities of an edge in optimal tours. Historical LKH tours form a correlated lineage; significance is descriptive.'}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(out,indent=2)+'\n')
    Path(a.regions).parent.mkdir(parents=True,exist_ok=True)
    Path(a.regions).write_text('cell_x,cell_y,n,disagreement_2plus,fraction_lp_nodes,overlap_2plus_and_fraction,overlap_rate,mean_x,mean_y\n'+
        ''.join(f"{r['cell_x']},{r['cell_y']},{r['n']},{r['disagreement_2plus']},{r['fraction_lp_nodes']},{r['overlap_2plus_and_fraction']},{r['overlap_rate']},{r['mean_x']},{r['mean_y']}\n" for r in rows))
    # Clear three-way geographic diagnostic, no invented region names.
    fig,ax=plt.subplots(figsize=(9,11),dpi=135)
    x=coords[:,0];y=coords[:,1]
    ax.scatter(x,y,c='#a7a7a7',s=.07,alpha=.18,rasterized=True)
    both=(different>=2)&lp_frac
    only_diff=(different>=2)&(~lp_frac)
    only_lp=(different<2)&lp_frac
    ax.scatter(x[only_diff],y[only_diff],s=.4,c='#e8883d',alpha=.65,rasterized=True,label=f'Algorithm disagreement (>=2): {int(only_diff.sum()):,}')
    ax.scatter(x[only_lp],y[only_lp],s=.4,c='#3378bb',alpha=.50,rasterized=True,label=f'LP fractional only: {int(only_lp.sum()):,}')
    ax.scatter(x[both],y[both],s=1.4,c='#bb214c',alpha=.92,rasterized=True,label=f'Both signals: {int(both.sum()):,}')
    ax.set_aspect('equal','box');ax.set_axis_off()
    ax.set_title('Mona Lisa 100K: historical tour disagreement and 2012 Concorde LP fractions')
    ax.legend(loc='lower center',bbox_to_anchor=(.5,-.065),fontsize=8,markerscale=6,ncol=1,frameon=False)
    fig.savefig(a.map,bbox_inches='tight',facecolor='white')
    plt.close(fig)
    print(json.dumps({'status':'verified','historical_tours':M,
      'stable_all':len(stable),'frac_nodes':int(lp_frac.sum()),
      'persistent_frac':int(persistent.sum()),
      'overlap_2plus':int(both.sum()),
      'permutation':tests.get('2',{}).get('stratified_null'),
      'top_region':rows[0] if rows else None}),flush=True)
if __name__=='__main__':main()
