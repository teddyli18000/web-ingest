#!/usr/bin/env python3
"""Planar-dual face-flip diagnostic on the published Mona Lisa reduction.

Exploratory only: does not independently certify the ElimTSP reduction.
"""
import argparse
from collections import Counter
import gzip
import importlib.util
import json
import os
from pathlib import Path
import time

import networkx as nx


def tour_edges(t):
    return {tuple(sorted((t[i], t[(i + 1) % len(t)]))) for i in range(len(t))}


def count_components_after_flip(n, tour, removed, added):
    """Validate that the flipped 2-factor is a single Hamiltonian cycle."""
    adj = [[] for _ in range(n)]
    for a, b in tour:
        adj[a].append(b)
        adj[b].append(a)
    for a, b in removed:
        adj[a].remove(b)
        adj[b].remove(a)
    for a, b in added:
        adj[a].append(b)
        adj[b].append(a)
    if any(len(v) != 2 for v in adj):
        return None
    seen = bytearray(n)
    count = 0
    for i in range(n):
        if seen[i]:
            continue
        count += 1
        previous = -1
        vertex = i
        while not seen[vertex]:
            seen[vertex] = 1
            a, b = adj[vertex]
            step = a if a != previous else b
            previous, vertex = vertex, step
    return count


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--edges', required=True)
    p.add_argument('--baseline', required=True)
    p.add_argument('--report', required=True)
    args = p.parse_args()
    started = time.monotonic()
    n = 100000
    t = [x - 1 for x in json.loads(Path(args.baseline).read_text())['tour']]
    assert len(t) == n and set(t) == set(range(n))
    baseline = tour_edges(t)

    with gzip.open(args.edges, 'rt') as stream:
        header = list(map(int, stream.readline().split()))
        assert len(header) == 2 and header[0] == n
        raw = [tuple(map(int, line.split())) for line in stream if line.strip()]
    assert len(raw) == header[1] and all(len(z) == 3 for z in raw)
    amin = min(min(u,v) for u,v,w in raw)
    amax = max(max(u,v) for u,v,w in raw)
    offset = 0 if amin == 0 else 1 if amax == n else None
    assert offset is not None, (amin, amax)
    edges = {}
    for u,v,w in raw:
        u -= offset; v -= offset
        assert u != v and 0 <= u < n and 0 <= v < n
        edge = min(u,v),max(u,v)
        assert edge not in edges
        edges[edge] = w

    spec=importlib.util.spec_from_file_location(
        'p010_verify',Path(os.environ['FEWSHOTS_ROOT'])/
        'problems/p010-mona-lisa-tsp/verify/verify.py')
    verifier=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    xs,ys=verifier.coordinates()
    for i,((a,b),w) in enumerate(edges.items()):
        if i % 200 == 0:
            assert w == verifier.euc_2d(xs[a]-xs[b],ys[a]-ys[b])
    baseline_score=verifier.tour_length([x+1 for x in t])
    assert baseline_score == 5757191
    overlap=len(baseline.intersection(edges))
    print(json.dumps({'stage':'loaded','graph_edges':len(edges),
                      'baseline_edge_overlap':overlap}),flush=True)

    graph=nx.Graph()
    graph.add_nodes_from(range(n))
    graph.add_edges_from(edges.keys())
    connected=nx.is_connected(graph)
    degrees=dict(sorted(Counter(dict(graph.degree()).values()).items()))
    planar,embedding=nx.check_planarity(graph)
    print(json.dumps({'stage':'planarity','planar':planar,
                      'seconds':round(time.monotonic()-started,2)}),flush=True)
    result={'source':'https://github.com/bicobico2/ElimTSP/tree/main/results',
            'nodes':n,'candidate_edges':len(edges),
            'baseline_length':baseline_score,
            'baseline_edges_present':overlap,'baseline_edges_missing':n-overlap,
            'connected':connected,'planar':planar,'degree_histogram':degrees,
            'status':'exploratory only; elimination proof not independently checked'}

    if planar:
        visited=set()
        face_sizes=Counter()
        face_gains=Counter()
        candidates=[]
        faces=0
        for a,b in graph.edges():
            for u,v in ((a,b),(b,a)):
                if (u,v) in visited:
                    continue
                vs=embedding.traverse_face(u,v)
                faces += 1
                length=len(vs)
                face_sizes[length] += 1
                visited.update((vs[i],vs[(i+1)%length]) for i in range(length))
                if overlap != n or length < 4 or length%2 or len(set(vs))!=length:
                    continue
                boundary=[tuple(sorted((vs[i],vs[(i+1)%length]))) for i in range(length)]
                flags=[e in baseline for e in boundary]
                if any(flags[i] == flags[(i+1)%length] for i in range(length)):
                    continue
                gain=sum(edges[e] for e,f in zip(boundary,flags) if f)
                gain-=sum(edges[e] for e,f in zip(boundary,flags) if not f)
                face_gains[gain]+=1
                if gain >= 0:
                    candidates.append((gain,boundary,flags))
        result['faces']=faces
        result['face_sizes']=dict(sorted(face_sizes.items()))
        result['alternating_faces']=sum(face_gains.values())
        result['face_gain_distribution']=dict(sorted(face_gains.items()))
        # Only strict improvements can yield a new record. Zero-gain flips
        # are tracked because they may enable coupled moves.
        top=[]
        for gain,boundary,flags in sorted(candidates,reverse=True)[:20]:
            removed=[e for e,flag in zip(boundary,flags) if flag]
            added=[e for e,flag in zip(boundary,flags) if not flag]
            components=count_components_after_flip(n,baseline,removed,added)
            top.append({'gain':gain,'face_size':len(boundary),'components':components})
        result['top_face_moves']=top
    result['seconds']=round(time.monotonic()-started,2)
    Path(args.report).parent.mkdir(parents=True,exist_ok=True)
    Path(args.report).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'stage':'finished','result':result}),flush=True)


if __name__ == '__main__':
    main()
