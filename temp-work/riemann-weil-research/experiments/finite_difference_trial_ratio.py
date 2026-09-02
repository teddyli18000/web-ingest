#!/usr/bin/env python3
"""Rigorous energy ratio of centered finite-difference trial vs Schur pivot.

For the orthonormal even prefix E_N, the Schur pivot is

  s_N = min { v^T E_N v : v_N = 1 }.

The full centered finite-difference stencil has coefficient 1 at m=N; in the
orthonormal even basis its last coordinate is sqrt(2).  Scale the stencil by
1/sqrt(2) so the new-mode coordinate is exactly one, and compare its Arb
Rayleigh energy to the exact Arb Schur pivot.
"""
from __future__ import annotations
import argparse, importlib.util, json, math
from pathlib import Path
from flint import arb, arb_mat, ctx


def load(path):
    s=importlib.util.spec_from_file_location('upstream',path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def project_even(A,N):
    E=arb_mat(N+1,N+1); r2=arb(2).sqrt(); c=N
    E[0,0]=A[c,c]
    for k in range(1,N+1):
        E[0,k]=(A[c,c+k]+A[c,c-k])/r2; E[k,0]=E[0,k]
    for k in range(1,N+1):
        for j in range(k,N+1):
            v=(A[c+k,c+j]+A[c+k,c-j]+A[c-k,c+j]+A[c-k,c-j])/2
            E[k,j]=v; E[j,k]=v
    return E

def ldlt_last(E):
    n=E.nrows(); L=[[arb(0) for _ in range(n)] for _ in range(n)]; d=[None]*n
    for i in range(n):
        L[i][i]=arb(1); s=E[i,i]
        for k in range(i): s-=L[i][k]*L[i][k]*d[k]
        if not (s>0 or s<0): raise RuntimeError(f'undetermined {i}')
        d[i]=s
        for j in range(i+1,n):
            t=E[j,i]
            for k in range(i): t-=L[j][k]*L[i][k]*d[k]
            L[j][i]=t/d[i]
    return d[-1]

def ball(x,digits=70):
    return {'lower':x.lower().str(digits,radius=False),'mid':x.mid().str(digits,radius=False),'upper':x.upper().str(digits,radius=False),'rad':x.rad().str(25,radius=False)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--upstream-script',type=Path,required=True); ap.add_argument('--c',type=int,required=True); ap.add_argument('--N',type=int,default=24); ap.add_argument('--prec',type=int,default=3000); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    ctx.prec=a.prec; mod=load(a.upstream_script); A,_=mod.build_arb_tau(a.c,a.N,a.prec); E=project_even(A,a.N); s=ldlt_last(E)
    r2=arb(2).sqrt()
    # Full d_m=(-1)^(N-m) C(2N,N+m). Even-coordinate components are d0 and sqrt(2)d_k.
    # Divide all by sqrt(2), making the Nth even coordinate exactly 1.
    v=[arb(0) for _ in range(a.N+1)]
    v[0]=arb(((-1)**a.N)*math.comb(2*a.N,a.N))/r2
    for k in range(1,a.N+1): v[k]=arb(((-1)**(a.N-k))*math.comb(2*a.N,a.N+k))
    energy=arb(0)
    for i in range(a.N+1):
        for j in range(a.N+1): energy += v[i]*E[i,j]*v[j]
    ratio=energy/s
    out={'status':'rigorous_centered_difference_trial_vs_schur','c':a.c,'N':a.N,'prec_bits':a.prec,'schur_pivot':ball(s),'centered_difference_scaled_energy':ball(energy),'energy_over_schur_pivot':ball(ratio),'variational_check_energy_ge_schur':bool(energy>=s),'meaning':'s_N is the constrained minimum with last even coordinate 1. Ratio approaching 1 means the centered finite-difference stencil is becoming the actual Schur minimizer in energy, not merely in Euclidean direction.'}
    a.output.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
