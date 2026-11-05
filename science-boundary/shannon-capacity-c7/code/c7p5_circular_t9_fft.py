#!/usr/bin/env python3
"""Exact rounded-FFT t=9 BPZ auxiliary scan for NEW circular 367 source.

The pinned BPZ/Tandon nine-port component has 160 obstruction sets D.
A translated 367-point auxiliary X avoiding any one D yields an explicit
134,770-word independent set in C7^10 through Definition 2.

Existing public I0/X/Family-F scans never included this nonequivalent circular
367 basin. Search *all* 7^5 shifts against all 160 obstruction masks. Every
FFT zero is replayed using integer 5D words before materializing a certificate.
If there is no zero, preserve the closest obstruction as a targeted repair
instance, rather than silently extending random local search.
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

import bpz_t9_aux_translation_fft as f
from c7p5_circular_hall_io import read_circular

PINNED="c753408492dde92a239708986d16c15dbf6c3235"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("tandon_root",type=Path)
    p.add_argument("circular",type=Path)
    p.add_argument("status",type=Path)
    p.add_argument("certificate",type=Path)
    p.add_argument("near_miss",type=Path)
    a=p.parse_args()
    root=a.tandon_root.resolve()
    sys.path.insert(0,str(root))
    from shannon.certificates import Ring

    raw=json.loads((root/"data"/"base_c7.json").read_text())
    I0=set(map(int,raw["I0"]))
    S=set(read_circular(a.circular))
    ring=Ring(5)
    digits=tuple(ring.decode(v) for v in range(f.U))
    assert len(S)==367 and f.independent(S,digits)
    nbh=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]
    obs=f.obstruction_witnesses(I0,ring,digits,nbh)
    masks=list(obs.items())
    assert len(masks)==160

    FS=np.fft.fftn(f.arr(S,digits))
    best=None;hist=Counter();zero_fft=0;integer_replays=0;winning=None
    for i,(mask,witness) in enumerate(masks):
        corr=np.rint(np.fft.ifftn(np.conj(FS)*np.fft.fftn(
            f.arr(f.values(mask),digits))).real).astype(np.int16)
        mn=int(corr.min())
        hist[mn]+=1
        shift0=tuple(int(z) for z in np.unravel_index(int(corr.argmin()),corr.shape))
        if best is None or mn<best["minimum_fft_hits"]:
            best={"mask_index":i,"minimum_fft_hits":mn,"shift":list(shift0),
                  "mask_size":mask.bit_count()}
        if mn!=0:continue
        for idx in np.argwhere(corr==0):
            zero_fft+=1
            shift=tuple(int(z) for z in idx)
            for sign in (1,-1):
                integer_replays+=1
                X=set(f.shift_set(S,shift,digits,sign))
                if X.isdisjoint(set(f.values(mask))):
                    winning=(i,shift,sign,X,witness)
                    break
            if winning:break
        if winning:break
    candidate=winning is not None
    if candidate:
        i,shift,sign,X,w=winning
        Ibits,pairs,o,PH,PV=w
        words,partition=f.build(Ibits,sum(1<<z for z in X),pairs,PH,PV,ring)
        assert len(words)==134770 and len(set(words))==134770
        a.certificate.parent.mkdir(parents=True,exist_ok=True)
        a.certificate.write_text(json.dumps({"points":words},separators=(",",":"))+"\n")
        best.update({"winning_mask":i,"winning_shift":list(shift),
                     "winning_sign":sign,"score":len(words),
                     "port_partition":list(partition)})
    else:
        idx=best["mask_index"];mask,w=masks[idx]
        sh=tuple(best["shift"])
        scenarios=[]
        for sign in (1,-1):
            X=set(f.shift_set(S,sh,digits,sign))
            hits=sorted(X.intersection(set(f.values(mask))))
            scenarios.append({"sign":sign,"actual_hits":len(hits),
                              "hit_vertices":hits,"translated_auxiliary":sorted(X)})
        near={"source":"new-circular-367","source_commit":PINNED,
              "best_fft":best,"obstruction_mask_indices":sorted(f.values(mask)),
              "scenarios":scenarios,
              "obstruction_private_pairs":[list(x) for x in w[1]],
              "obstruction_port_orientation":list(w[2])}
        a.near_miss.parent.mkdir(parents=True,exist_ok=True)
        a.near_miss.write_text(json.dumps(near,indent=2,sort_keys=True)+"\n")
    result={"method":"new-circular-367-all-shifts-BPZ-t9-obstruction-FFT",
            "source_commit":PINNED,"new_auxiliary_size":len(S),
            "obstruction_masks":len(masks),"translations_each":f.U,
            "total_shift_mask_cases":len(masks)*f.U,
            "minimum_hit_histogram":dict(sorted(hist.items())),
            "best":best,"fft_zero_locations_seen":zero_fft,
            "integer_zero_replay_attempts":integer_replays,
            "candidate_134770":candidate,
            "candidate_score":134770 if candidate else None}
    a.status.parent.mkdir(parents=True,exist_ok=True)
    a.status.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("RESULT",json.dumps(result,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
