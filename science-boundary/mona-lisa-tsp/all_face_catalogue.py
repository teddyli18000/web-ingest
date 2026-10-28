#!/usr/bin/env python3
"""Reproducible complete alternating quadrilateral-face catalogue.
Source: Cook et al. ElimTSP reduced graph; compare to Few Shots 100K baseline.
Output: 0-based flattened edge source and face catalogue for independent C++ exhaustive sweep.
"""
import argparse,gzip,json
from pathlib import Path
import networkx as nx

def edge(u,v):return (u,v) if u<v else (v,u)
def main():
 p=argparse.ArgumentParser()
 for k in ['graph','tour','output-graph','output-faces','report']:p.add_argument('--'+k,required=True)
 a=p.parse_args()
 tour=[int(x)-1 for x in json.loads(Path(a.tour).read_text())['tour']]
 n=len(tour);assert n==100000 and len(set(tour))==n
 with gzip.open(a.graph,'rt') as f:
  head=list(map(int,f.readline().split()))
  source=[tuple(map(int,line.split())) for line in f if line.strip()]
 assert head==[n,len(source)]
 offset=0 if min(min(u,v) for u,v,w in source)==0 else 1
 W={edge(u-offset,v-offset):w for u,v,w in source}
 assert len(W)==len(source)
 base={edge(tour[i],tour[(i+1)%n]) for i in range(n)}
 assert len(base)==n and base<=W.keys()
 graph=nx.Graph();graph.add_nodes_from(range(n));graph.add_edges_from(W)
 planar,embedding=nx.check_planarity(graph);assert planar
 seen=set(); faces=[]; all_lengths={}
 for a,b in graph.edges():
  for u,v in ((a,b),(b,a)):
   if (u,v) in seen:continue
   vs=embedding.traverse_face(u,v);L=len(vs)
   for i in range(L):seen.add((vs[i],vs[(i+1)%L]))
   all_lengths[L]=all_lengths.get(L,0)+1
   if L!=4 or len(set(vs))!=4:continue
   eds=[edge(vs[i],vs[(i+1)%4]) for i in range(4)]
   flags=[x in base for x in eds]
   if any(flags[i]==flags[(i+1)%4] for i in range(4)):continue
   old=[x for x,f in zip(eds,flags) if f]
   new=[x for x,f in zip(eds,flags) if not f]
   assert len(old)==len(new)==2
   gain=sum(W[e] for e in old)-sum(W[e] for e in new)
   faces.append((gain,*old[0],*old[1],*new[0],*new[1]))
 faces.sort(key=lambda x:(-x[0],x[1:]))
 Path(a.output_graph).write_text(f'{n} {len(W)}\n'+''.join(f'{u} {v} {w}\n' for (u,v),w in W.items()))
 Path(a.output_faces).write_text(str(len(faces))+'\n'+''.join(' '.join(map(str,rec))+'\n' for rec in faces))
 report={'nodes':n,'edges':len(W),'faces_total':sum(all_lengths.values()),
         'quadrilateral_alternating_faces':len(faces),
         'face_gain_histogram':{str(v):sum(rec[0]==v for rec in faces) for v in sorted({rec[0] for rec in faces})},
         'positive_face_count':sum(rec[0]>0 for rec in faces),
         'zero_face_count':sum(rec[0]==0 for rec in faces),
         'negative_face_count':sum(rec[0]<0 for rec in faces),
         'max_face_gain':max(rec[0] for rec in faces),'min_face_gain':min(rec[0] for rec in faces)}
 Path(a.report).write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='face_gain_histogram'}),flush=True)
if __name__=='__main__':main()
