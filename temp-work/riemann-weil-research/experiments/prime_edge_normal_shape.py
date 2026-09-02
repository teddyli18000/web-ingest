#!/usr/bin/env python3
"""Compare prime-edge Schur normals with the maximally-blind finite-difference stencil.

For each N, the nested Schur normal in the orthonormal even basis is
w_N=(-B^{-1}b,1).  It satisfies E_N w_N=(0,...,0,s_N)^T.

We transform w_N back to full even Fourier coefficients on {-N,...,N}, then
compare its normalized direction with the unique centered finite-difference
stencil that attains the 4N+1 prime-edge visibility ceiling.  We also record
scale-free even moments.  This is a falsification diagnostic: small M0 alone
does not imply approach to the extremal stencil.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path

import mpmath as mp
from flint import arb, arb_mat, ctx


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location('upstream', path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def project_even(A: arb_mat, N: int) -> arb_mat:
    E = arb_mat(N + 1, N + 1)
    root2 = arb(2).sqrt()
    center = N
    E[0,0] = A[center,center]
    for k in range(1,N+1):
        E[0,k]=(A[center,center+k]+A[center,center-k])/root2
        E[k,0]=E[0,k]
    for k in range(1,N+1):
        for j in range(k,N+1):
            v=(A[center+k,center+j]+A[center+k,center-j]+A[center-k,center+j]+A[center-k,center-j])/2
            E[k,j]=v; E[j,k]=v
    return E


def signed_ldlt(E):
    n=E.nrows(); L=[[arb(0) for _ in range(n)] for _ in range(n)]; d=[None]*n
    for i in range(n):
        L[i][i]=arb(1)
        s=E[i,i]
        for k in range(i): s-=L[i][k]*L[i][k]*d[k]
        if not (s>0 or s<0): raise RuntimeError(f'undetermined pivot {i}')
        d[i]=s
        for j in range(i+1,n):
            t=E[j,i]
            for k in range(i): t-=L[j][k]*L[i][k]*d[k]
            L[j][i]=t/d[i]
    return L,d


def schur_normal_even(L,N):
    if N==0: return [arb(1)]
    ell=[L[N][j] for j in range(N)]
    x=[arb(0) for _ in range(N)]
    for i in range(N-1,-1,-1):
        t=ell[i]
        for j in range(i+1,N): t-=L[j][i]*x[j]
        x[i]=t
    return [-z for z in x]+[arb(1)]


def even_to_full_mid(w):
    N=len(w)-1
    root2=mp.sqrt(2)
    out=[]
    for m in range(-N,N+1):
        if m==0: out.append(mp.mpf(w[0].mid().str(100,radius=False)))
        else: out.append(mp.mpf(w[abs(m)].mid().str(100,radius=False))/root2)
    return out


def central_diff(N):
    return [mp.mpf(((-1)**(N-m))*math.comb(2*N,N+m)) for m in range(-N,N+1)]


def dot(a,b): return mp.fsum(x*y for x,y in zip(a,b))
def norm(a): return mp.sqrt(dot(a,a))


def diagnostics(w,N):
    full=even_to_full_mid(w)
    wn=norm(full)
    fd=central_diff(N)
    fn=norm(fd)
    overlap=abs(dot(full,fd)/(wn*fn)) if N>0 else mp.mpf(1)
    l1=mp.fsum(abs(x) for x in full)
    moments=[]
    # Dimensionless moments: M_{2j}/(N^{2j} ||w||_1), with N=0 handled separately.
    maxj=min(N,8)
    for j in range(maxj+1):
        power=2*j
        M=mp.fsum((mp.mpf(m)**power)*full[m+N] for m in range(-N,N+1))
        scale=l1*(mp.mpf(max(N,1))**power)
        moments.append({'order':power,'value':mp.nstr(M,50),'normalized_abs':mp.nstr(abs(M)/scale,40)})
    return {
        'N':N,
        'central_difference_absolute_overlap':mp.nstr(overlap,50),
        'L2_norm':mp.nstr(wn,50),
        'L1_norm':mp.nstr(l1,50),
        'moments':moments,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--upstream-script',type=Path,required=True)
    ap.add_argument('--q',type=int,required=True)
    ap.add_argument('--Nmax',type=int,default=32)
    ap.add_argument('--prec',type=int,default=3000)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    mp.mp.dps=120; ctx.prec=args.prec
    mod=load_module(args.upstream_script)
    A,_=mod.build_arb_tau(args.q,args.Nmax,args.prec)
    E=project_even(A,args.Nmax)
    L,d=signed_ldlt(E)
    selected=[n for n in (1,2,4,8,12,16,20,24,28,32) if n<=args.Nmax]
    rows=[]
    for N in selected:
        w=schur_normal_even(L,N)
        row=diagnostics(w,N)
        row['schur_pivot_mid']=d[N].mid().str(70,radius=False)
        rows.append(row)
    out={
        'status':'prime_edge_schur_normal_shape_diagnostic',
        'q':args.q,'Nmax':args.Nmax,'prec_bits':args.prec,
        'rows':rows,
        'interpretation':'Overlap near 1 plus simultaneous decay of successive normalized even moments would support approach to the unique maximally-blind centered finite-difference stencil. Tiny M0 without these features falsifies that stronger hypothesis.',
        'warning':'Normal shapes use high-precision Arb midpoints for direction diagnostics; Schur pivots themselves come from strictly signed Arb balls.',
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'q':args.q,'rows':[{'N':r['N'],'fd_overlap':r['central_difference_absolute_overlap'],'M0_norm':r['moments'][0]['normalized_abs'],'M2_norm':r['moments'][1]['normalized_abs'] if len(r['moments'])>1 else None} for r in rows]},indent=2))

if __name__=='__main__': main()
