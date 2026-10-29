#!/usr/bin/env python3
"""Independent hold-out audit for restricted 8NN+parent dynamic SEC solutions.

Does NOT import the search implementation, NumPy, OR-Tools or original
benchmark scorer. Parses original TSPLIB coordinates separately, uses
math.hypot / floor(d+0.5), verifies exact n-city Hamiltonian permutation,
objective, allowed candidate edge set and official certified optimum values.
No hidden optimal tour certificate is supplied to search jobs.
"""
import argparse,hashlib,json,math
from pathlib import Path
def edge(u,v):return (u,v) if u<v else (v,u)
def parse_instance(path):
    lines=Path(path).read_text().splitlines()
    dim=None;coords={};inside=False
    for ln in lines:
        row=ln.strip()
        if row.startswith("DIMENSION"):
            dim=int(row.replace(':',' ').split()[1])
        if row.startswith("EDGE_WEIGHT_TYPE"):
            assert row.replace(':',' ').split()[1]=="EUC_2D"
        elif row=="NODE_COORD_SECTION":inside=True
        elif inside and row=="EOF":break
        elif inside and row:
            bits=row.split()
            coords[int(bits[0])-1]=(float(bits[1]),float(bits[2]))
    assert dim and len(coords)==dim and set(coords)==set(range(dim))
    return [coords[i] for i in range(dim)]
def cost(a,b,coords):
    x,y=coords[a];z,w=coords[b]
    return math.floor(math.hypot(x-z,y-w)+0.5)
def route_score(t,coords):
    n=len(coords);assert len(t)==n and set(t)==set(range(n))
    return sum(cost(t[i],t[(i+1)%n],coords) for i in range(n))
def edges(t):
    return {edge(t[i],t[(i+1)%len(t)]) for i in range(len(t))}
def allowed_edges(pub,coords):
    n=len(coords)
    base=set().union(edges(pub['reference']),*(edges(r) for r in pub['parents']))
    neighbor=set()
    for u in range(n):
        closest=sorted(range(n),key=lambda v:(cost(u,v,coords),v))[:9]
        for v in closest:
            if u!=v:neighbor.add(edge(u,v))
    return base|neighbor
def main():
    p=argparse.ArgumentParser()
    for a in ('public','instance','output','results','optima'):p.add_argument('--'+a,required=True)
    args=p.parse_args()
    opt=json.loads(Path(args.optima).read_text())
    outcomes=[]
    for file in sorted(Path(args.results).rglob('result.json')):
        data=json.loads(file.read_text())
        if data.get('strategy')!='knn8_dynamic_SEC':continue
        name=data['instance']
        inst=Path(args.instance)/f'{name}.tsp'
        public=list(Path(args.public).rglob(f'{name}/public.json'))
        assert len(public)==1,public
        pub=json.loads(public[0].read_text())
        assert pub['instance']==name
        coords=parse_instance(inst)
        n=len(coords)
        assert n==pub['n']
        ref_cost=route_score(pub['reference'],coords)
        assert ref_cost==data['reference_score']==pub['reference_score']
        actual=route_score(data['tour'],coords)
        assert actual==data['score'],(name,actual,data['score'])
        allowed=allowed_edges(pub,coords)
        assert edges(data['tour'])<=allowed,(name,len(edges(data['tour'])-allowed))
        assert actual>=opt[name],(name,actual,opt[name])
        if data['proof_of_restricted_optimality']:
            assert data['status']=='OPTIMAL'
        outcome={'instance':name,'n':n,'certified_global_optimum':opt[name],
          'search_reported_score':data['score'],'independently_scored_tour':actual,
          'achieved_certified_optimum':actual==opt[name],
          'verified_hamiltonian':True,
          'all_edges_within_public_candidate_graph':True,
          'restricted_optimality_reported':data['proof_of_restricted_optimality'],
          'solver_status':data['status'],'SEC_cuts':data['separated_cuts'],
          'compute_seconds':data['elapsed_seconds'],
          'input_sha256':hashlib.sha256(inst.read_bytes()).hexdigest(),
          'certificate_sha256':hashlib.sha256(json.dumps(data['tour'],separators=(',',':')).encode()).hexdigest()}
        outcomes.append(outcome)
    assert len(outcomes)==15,(len(outcomes),[x['instance'] for x in outcomes])
    summary={'proven_global_optimal_score_cases':sum(x['achieved_certified_optimum'] for x in outcomes),
      'restricted_OPTIMAL_cases':sum(x['restricted_optimality_reported'] for x in outcomes),
      'independently_verified_full_tour_cases':len(outcomes),
      'cases':outcomes,
      'limitation':'Restricted optimum proven by CP-SAT status+valid SEC logic, not formal proof logs. Matching TSPLIB published optimal score gives independent global-optimum value cross-check. No globally new TSP record.'}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'stage':'independent_TSPLIB_Score_and_CandidatePool_audit',
        'verified':len(outcomes),'global_opt_matches':summary['proven_global_optimal_score_cases'],
        'reported_restricted_proofs':summary['restricted_OPTIMAL_cases']}),flush=True)
if __name__=='__main__':main()
