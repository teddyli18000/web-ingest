#!/usr/bin/env python3
"""Classify cascade-aware beam signals against known R->A/R->B root-glide signatures.

The cascade-aware search measures remote root glides that trigger or soften.
A high signal is only mechanistically novel if it is not explained by the root
same-count replacements already present in the known A or B endpoint
triangulations.  This utility labels each triggered/softened glide accordingly.
"""
from __future__ import annotations
import argparse,json,pathlib


def edge(x):
    a,b=map(int,x); return (min(a,b),max(a,b))

# Root-accessible same-count replacements obtained by comparing the aligned
# live/A/B triangulations.  Transient dependent events (e.g. q1) are not listed
# unless their final replacement is itself a legal root glide.
A_KNOWN={
    ((108,511),(282,502)),
    ((21,230),(74,363)),
    ((79,134),(35,323)),
}
B_KNOWN={
    ((108,511),(282,502)),
    ((21,230),(74,363)),
    ((191,748),(182,922)),
    ((428,602),(831,919)),
    ((379,959),(295,923)),
}
KNOWN=A_KNOWN|B_KNOWN


def label(z):
    k=(edge(z['delete']),edge(z['add']))
    in_a=k in A_KNOWN; in_b=k in B_KNOWN
    if in_a and in_b: cls='known-A+B'
    elif in_a: cls='known-A'
    elif in_b: cls='known-B'
    else: cls='novel'
    return cls,k


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result_json'); ap.add_argument('--out')
    args=ap.parse_args(); d=json.load(open(args.result_json))
    rows=[]
    for i,n in enumerate(d.get('nodes',[])):
        cas=n.get('cascade') or {}; trig=[]; soft=[]
        for z in cas.get('triggered',[]):
            cls,k=label(z); trig.append({'class':cls,'delete':list(k[0]),'add':list(k[1]),'root_threshold':z.get('root_threshold')})
        for z in cas.get('top_softened',[]):
            cls,k=label(z); soft.append({'class':cls,'delete':list(k[0]),'add':list(k[1]),
                'root_threshold':z.get('root_threshold'),'threshold':z.get('threshold'),
                'fractional_drop':z.get('fractional_drop')})
        novel_triggered=sum(z['class']=='novel' for z in trig)
        novel_softening=sum(float(z.get('fractional_drop') or 0.0) for z in soft if z['class']=='novel')
        known_triggered=len(trig)-novel_triggered
        known_softening=sum(float(z.get('fractional_drop') or 0.0) for z in soft if z['class']!='novel')
        rows.append({'node_index':i,'depth':n.get('depth'),'free_energy':n.get('free_energy'),
            'free_class':n.get('free_class'),'cascade_effective':n.get('cascade_effective'),
            'novel_triggered':novel_triggered,'known_triggered':known_triggered,
            'novel_softening':novel_softening,'known_softening':known_softening,
            'triggered':trig,'top_softened':soft,'path':n.get('path')})
    rows.sort(key=lambda r:(-r['novel_triggered'],-r['novel_softening'],r['free_energy'] if r['free_energy'] is not None else 1e99))
    out={'tag':d.get('tag'),'best_free_energy':d.get('best_free_energy'),'rows':rows}
    if args.out: pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    for r in rows[:30]:
        print('CAS',r['node_index'],'d',r['depth'],'free',r['free_class'],r['free_energy'],
              'novel_trig',r['novel_triggered'],'novel_soft',f"{r['novel_softening']:.4f}",
              'known_trig',r['known_triggered'],'known_soft',f"{r['known_softening']:.4f}")
        if r['triggered']: print(' TRIG',[(z['class'],z['delete'],z['add']) for z in r['triggered']])
        if r['top_softened']: print(' SOFT',[(z['class'],z['delete'],z['add'],round(float(z['fractional_drop'] or 0),4)) for z in r['top_softened']])

if __name__=='__main__': main()
