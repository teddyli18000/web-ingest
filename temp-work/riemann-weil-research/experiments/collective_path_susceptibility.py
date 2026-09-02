#!/usr/bin/env python3
"""Exploratory collective relative derivative norm of the cutoff-free CvS path.

Let u=log c and E_N(u) be the cutoff-free even Weil matrix on an interval that
contains no prime-power threshold.  Define

    Gamma_N(u) = || E_N(u)^(-1/2) E_N'(u) E_N(u)^(-1/2) ||_op.

Unlike termwise interior-prime susceptibilities, Gamma keeps the signed
cancellation between all prime terms and the archimedean/pole terms.  If Gamma
stays moderate while termwise norms are enormous, then a cancellation-aware
relative-flow strategy remains viable.

This is a high-precision midpoint stress test.  E'(u) is estimated by centered
finite differences at several h and checked for convergence.  No interval
certificate is claimed.
"""
from __future__ import annotations

import argparse, importlib.util, json, math
from pathlib import Path
import mpmath as mp
from flint import arb, arb_mat, ctx


def load_module(path: Path):
    spec=importlib.util.spec_from_file_location('upstream',path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def fixed_prime_powers(c0:int):
    primes=[]
    for x in range(2,c0+1):
        if all(x%p for p in primes): primes.append(x)
    out=[]
    for p in primes:
        q=p
        while q<=c0:
            out.append((q,p)); q*=p
    return out


def build_tau_real_c(mod, c_str:str, N:int, prec:int, pdata):
    ctx.prec=prec
    S,CC,XC,L=mod.arb_closed_forms(N,c_str,prec)
    PI=arb.pi(); sp2=16*PI*PI; l2=L*L
    pref02=32*L*(L/4).sinh()**2
    kappa=mod.arb_kappa(L); J=mod.arb_J(L)
    weights=[arb(p).log()*(arb(q)**arb('-0.5')) for q,p in pdata]
    positions=[arb(q).log() for q,p in pdata]
    def S_signed(nn): return S[nn] if nn>=0 else -S[-nn]
    D=2*N+1; A=arb_mat(D,D)
    for i in range(D):
        n=i-N
        for j in range(i,D):
            m=j-N
            num=l2-sp2*m*n
            den=(l2+sp2*m*m)*(l2+sp2*n*n)
            W02=pref02*num/den
            if n==m:
                WR=kappa+2*CC[abs(n)]+J-(2/L)*XC[abs(n)]
            else:
                WR=(S_signed(m)-S_signed(n))/(PI*(n-m))
            Wp=arb(0)
            for idx in range(len(weights)):
                y=positions[idx]
                if n==m:
                    qv=2*(1-y/L)*(2*PI*n*y/L).cos()
                else:
                    qv=((2*PI*m*y/L).sin()-(2*PI*n*y/L).sin())/(PI*(n-m))
                Wp+=weights[idx]*qv
            val=W02-WR-Wp
            A[i,j]=val; A[j,i]=val
    return A


def mp_mid(x, digits): return mp.mpf(x.mid().str(digits,radius=False))


def project_even(A,N,digits):
    root2=mp.sqrt(2); c=N; E=mp.matrix(N+1)
    E[0,0]=mp_mid(A[c,c],digits)
    for k in range(1,N+1):
        v=(mp_mid(A[c,c+k],digits)+mp_mid(A[c,c-k],digits))/root2
        E[0,k]=E[k,0]=v
    for k in range(1,N+1):
        for j in range(k,N+1):
            v=(mp_mid(A[c+k,c+j],digits)+mp_mid(A[c+k,c-j],digits)+mp_mid(A[c-k,c+j],digits)+mp_mid(A[c-k,c-j],digits))/2
            E[k,j]=E[j,k]=v
    return E


def generalized_norm(E,D):
    L=mp.cholesky(E); Lin=L**-1
    A=Lin*D*Lin.T
    vals=mp.eigsy(A,eigvals_only=True)
    lo=vals[0]; hi=vals[vals.rows-1]
    return max(abs(lo),abs(hi)),lo,hi


def fro_rel(A,B):
    num=mp.sqrt(mp.fsum([(A[i,j]-B[i,j])**2 for i in range(A.rows) for j in range(A.cols)]))
    den=max(mp.mpf(1),mp.sqrt(mp.fsum([B[i,j]**2 for i in range(B.rows) for j in range(B.cols)])))
    return num/den


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--upstream-script',type=Path,required=True)
    ap.add_argument('--upstream-commit',required=True)
    ap.add_argument('--c0',type=int,default=100)
    ap.add_argument('--N',type=int,required=True)
    ap.add_argument('--prec',type=int,required=True)
    ap.add_argument('--dps',type=int,required=True)
    ap.add_argument('--hs',type=str,default='1e-3,1e-4,1e-5')
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); mp.mp.dps=args.dps
    mod=load_module(args.upstream_script); pdata=fixed_prime_powers(args.c0)
    u0=mp.log(args.c0); digits=args.dps+30
    E0=project_even(build_tau_real_c(mod,mp.nstr(mp.e**u0,digits),args.N,args.prec,pdata),args.N,digits)
    hs=[mp.mpf(x.strip()) for x in args.hs.split(',') if x.strip()]
    rows=[]; derivs=[]
    for h in hs:
        cp=mp.e**(u0+h); cm=mp.e**(u0-h)
        Ep=project_even(build_tau_real_c(mod,mp.nstr(cp,digits),args.N,args.prec,pdata),args.N,digits)
        Em=project_even(build_tau_real_c(mod,mp.nstr(cm,digits),args.N,args.prec,pdata),args.N,digits)
        D=(Ep-Em)/(2*h)
        gamma,lo,hi=generalized_norm(E0,D)
        derivs.append(D)
        rows.append({'h':mp.nstr(h,20),'gamma':mp.nstr(gamma,70),'generalized_min':mp.nstr(lo,70),'generalized_max':mp.nstr(hi,70),'log10_gamma':float(mp.log10(gamma)) if gamma>0 else None})
    convergence=[]
    for i in range(1,len(derivs)):
        convergence.append({'h_coarse':rows[i-1]['h'],'h_fine':rows[i]['h'],'derivative_frobenius_relative_difference':mp.nstr(fro_rel(derivs[i-1],derivs[i]),40),'gamma_relative_difference':mp.nstr(abs(mp.mpf(rows[i-1]['gamma'])-mp.mpf(rows[i]['gamma']))/max(1,abs(mp.mpf(rows[i]['gamma']))),40)})
    # Locate thresholds around c0 for provenance.
    allq=sorted(set(q for q,p in fixed_prime_powers(max(args.c0*2,10))))
    prevq=max([q for q in allq if q<args.c0],default=None); nextq=min([q for q in allq if q>args.c0],default=None)
    out={'status':'exploratory_collective_path_susceptibility','warning':'High-precision midpoint centered differences, not an interval derivative certificate. Valid only inside the threshold-free neighborhood used here.','upstream_commit':args.upstream_commit,'c0':args.c0,'u0':mp.nstr(u0,60),'N':args.N,'prec_bits':args.prec,'mpmath_dps':args.dps,'active_prime_power_count':len(pdata),'previous_prime_power_threshold':prevq,'next_prime_power_threshold':nextq,'rows':rows,'convergence':convergence,'meaning':'Gamma is the generalized operator norm of the signed full derivative E_N prime+archimedean+pole path. Compare it with enormous termwise interior susceptibilities to quantify collective cancellation.'}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
