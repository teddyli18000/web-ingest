#!/usr/bin/env python3
"""Threshold-free logarithmic derivative probe for nested even Schur pivots.

For u=log c and the cutoff-free even CvS matrix E_N(u), let s_N(u) be the
last nested LDL/Schur pivot.  This script estimates

    g_N(u) = d/du log s_N(u) = s_N'(u)/s_N(u)

by centered differences while keeping the active prime-power set fixed.  This
is a scalar alternative to the extremely ill-conditioned matrix-wide relative
derivative norm.  Since s_N is much larger than lambda_min(E_N), it is also
numerically much easier to resolve.

The finite-difference derivative is exploratory; the pivot values themselves
are rigorous Arb balls.
"""
from __future__ import annotations

import argparse, importlib.util, json
from pathlib import Path
import mpmath as mp
from flint import arb, arb_mat, ctx


def load_module(path: Path):
    spec=importlib.util.spec_from_file_location('upstream',path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def prime_powers_fixed(c0:int):
    primes=[]
    for x in range(2,c0+1):
        isprime=True
        for p in primes:
            if p*p>x: break
            if x%p==0: isprime=False; break
        if isprime: primes.append(x)
    out=[]
    for p in primes:
        q=p
        while q<=c0:
            out.append((q,p)); q*=p
    return out


def build_tau_real_c(mod,c_str,N,prec,pdata):
    ctx.prec=prec
    S,CC,XC,L=mod.arb_closed_forms(N,c_str,prec)
    PI=arb.pi(); sp2=16*PI*PI; l2=L*L
    pref02=32*L*(L/4).sinh()**2
    kappa=mod.arb_kappa(L); J=mod.arb_J(L)
    weights=[arb(p).log()*(arb(q)**arb('-0.5')) for q,p in pdata]
    positions=[arb(q).log() for q,p in pdata]
    def Ss(n): return S[n] if n>=0 else -S[-n]
    D=2*N+1; A=arb_mat(D,D)
    for i in range(D):
        n=i-N
        for j in range(i,D):
            m=j-N
            W02=pref02*(l2-sp2*m*n)/((l2+sp2*m*m)*(l2+sp2*n*n))
            if n==m:
                WR=kappa+2*CC[abs(n)]+J-(2/L)*XC[abs(n)]
            else:
                WR=(Ss(m)-Ss(n))/(PI*(n-m))
            Wp=arb(0)
            for idx in range(len(weights)):
                y=positions[idx]
                if n==m:
                    qv=2*(1-y/L)*(2*PI*n*y/L).cos()
                else:
                    qv=((2*PI*m*y/L).sin()-(2*PI*n*y/L).sin())/(PI*(n-m))
                Wp += weights[idx]*qv
            v=W02-WR-Wp
            A[i,j]=v; A[j,i]=v
    return A


def project_even(A,N):
    root2=arb(2).sqrt(); c=N; E=arb_mat(N+1,N+1)
    E[0,0]=A[c,c]
    for k in range(1,N+1):
        v=(A[c,c+k]+A[c,c-k])/root2
        E[0,k]=v; E[k,0]=v
    for k in range(1,N+1):
        for j in range(k,N+1):
            v=(A[c+k,c+j]+A[c+k,c-j]+A[c-k,c+j]+A[c-k,c-j])/2
            E[k,j]=v; E[j,k]=v
    return E


def last_positive_pivot(E):
    n=E.nrows(); L=[[arb(0) for _ in range(n)] for _ in range(n)]; d=[]
    for i in range(n):
        L[i][i]=arb(1); s=E[i,i]
        for k in range(i): s -= L[i][k]*L[i][k]*d[k]
        if not (s>0): raise RuntimeError(f'undetermined/nonpositive pivot {i}: {s}')
        d.append(s)
        for j in range(i+1,n):
            t=E[j,i]
            for k in range(i): t -= L[j][k]*L[i][k]*d[k]
            L[j][i]=t/d[i]
    return d[-1]


def mid(x,digits): return mp.mpf(x.mid().str(digits,radius=False))

def ball(x,digits=60):
    return {'lower':x.lower().str(digits,radius=False),'mid':x.mid().str(digits,radius=False),'upper':x.upper().str(digits,radius=False),'rad':x.rad().str(20,radius=False)}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--upstream-script',type=Path,required=True); ap.add_argument('--upstream-commit',required=True)
    ap.add_argument('--c0',type=int,default=100); ap.add_argument('--N',type=int,required=True); ap.add_argument('--prec',type=int,required=True); ap.add_argument('--dps',type=int,required=True)
    ap.add_argument('--hs',default='1e-3,1e-4,1e-5'); ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); mp.mp.dps=args.dps; mod=load_module(args.upstream_script); pdata=prime_powers_fixed(args.c0)
    u0=mp.log(args.c0); digits=args.dps+30
    def pivot_at(u):
        c=mp.e**u
        A=build_tau_real_c(mod,mp.nstr(c,digits),args.N,args.prec,pdata)
        return last_positive_pivot(project_even(A,args.N))
    s0=pivot_at(u0); s0m=mid(s0,digits)
    rows=[]
    for hs in [x.strip() for x in args.hs.split(',') if x.strip()]:
        h=mp.mpf(hs); sp=pivot_at(u0+h); sm=pivot_at(u0-h)
        deriv=(mid(sp,digits)-mid(sm,digits))/(2*h)
        g=deriv/s0m
        curvature=(mid(sp,digits)-2*s0m+mid(sm,digits))/(h*h*s0m)
        rows.append({'h':hs,'pivot_plus':ball(sp),'pivot_minus':ball(sm),'s_prime_midpoint_fd':mp.nstr(deriv,70),'log_derivative_sprime_over_s':mp.nstr(g,70),'relative_second_derivative':mp.nstr(curvature,70)})
    out={'status':'exploratory_threshold_free_schur_log_derivative','warning':'Base and shifted pivots are rigorous Arb balls, but derivatives are midpoint finite differences; convergence across h is required before interpretation.','upstream_commit':args.upstream_commit,'c0':args.c0,'u0':mp.nstr(u0,60),'N':args.N,'prec_bits':args.prec,'mpmath_dps':args.dps,'active_prime_power_count':len(pdata),'pivot_at_c0':ball(s0),'rows':rows,'meaning':'g_N=s_N prime/s_N is the scalar relative flow rate of the last Schur pivot. A moderate, converged g_N would support pivot-by-pivot scalar flow even when the matrix-wide generalized derivative norm is numerically inaccessible.'}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
