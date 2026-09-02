#!/usr/bin/env python3
"""Exploratory high-precision interior susceptibility for the cutoff-free CvS even block.

For the Volterra source kernel K_v(omega), define H(omega) by

    v^T H(omega) v = K_v'(omega).

For a positive even Weil block E define the sharp generalized norm

    sigma(omega) = || E^{-1/2} H(omega) E^{-1/2} ||_op,

so |K_v'(omega)| <= sigma(omega) v^T E v.  At omega=0,
H(0)=2 r r^T and sigma(0)=2 chi with chi=r^T E^{-1}r.

This script uses high-precision midpoint matrices only.  It is designed to
falsify or support a relative-flow strategy before any interval certification.
"""
from __future__ import annotations

import argparse, importlib.util, json
from pathlib import Path
import mpmath as mp
from flint import arb_mat


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location('upstream', path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def mp_mid(x, digits=0):
    if digits <= 0:
        digits = max(80, mp.mp.dps + 20)
    return mp.mpf(x.mid().str(digits, radius=False))


def project_even_arb(A: arb_mat, N: int):
    root2 = mp.sqrt(2)
    center = N
    E = mp.matrix(N+1)
    E[0,0] = mp_mid(A[center,center])
    for k in range(1,N+1):
        v = (mp_mid(A[center,center+k]) + mp_mid(A[center,center-k])) / root2
        E[0,k]=E[k,0]=v
    for k in range(1,N+1):
        for j in range(k,N+1):
            v = (mp_mid(A[center+k,center+j]) + mp_mid(A[center+k,center-j])
                 + mp_mid(A[center-k,center+j]) + mp_mid(A[center-k,center-j])) / 2
            E[k,j]=E[j,k]=v
    return E


def full_H(N: int, omega):
    """Real symmetric full-basis matrix for d/domega K_v(omega)."""
    D=2*N+1
    H=mp.matrix(D)
    for i in range(D):
        n=i-N
        for j in range(i,D):
            m=j-N
            if n==m:
                val = 2*mp.cos(2*mp.pi*n*omega) - 4*mp.pi*n*omega*mp.sin(2*mp.pi*n*omega)
            else:
                val = 2*(n*mp.cos(2*mp.pi*n*omega)-m*mp.cos(2*mp.pi*m*omega))/(n-m)
            H[i,j]=H[j,i]=val
    return H


def project_even_mp(A, N:int):
    root2=mp.sqrt(2); center=N
    E=mp.matrix(N+1)
    E[0,0]=A[center,center]
    for k in range(1,N+1):
        v=(A[center,center+k]+A[center,center-k])/root2
        E[0,k]=E[k,0]=v
    for k in range(1,N+1):
        for j in range(k,N+1):
            v=(A[center+k,center+j]+A[center+k,center-j]+A[center-k,center+j]+A[center-k,center-j])/2
            E[k,j]=E[j,k]=v
    return E


def sigma_generalized(E, H):
    L=mp.cholesky(E)
    Lin=L**-1
    A=Lin*H*Lin.T
    vals=mp.eigsy(A, eigvals_only=True)
    lo=vals[0]; hi=vals[vals.rows-1]
    return max(abs(lo),abs(hi)),lo,hi


def prime_powers(c:int):
    primes=[]
    for x in range(2,c+1):
        if all(x%p for p in primes if p*p<=x):
            primes.append(x)
    out=[]
    for p in primes:
        q=p
        while q<c:
            out.append((q,p))
            q*=p
    return sorted(out)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--upstream-script',type=Path,required=True)
    ap.add_argument('--upstream-commit',required=True)
    ap.add_argument('--c',type=int,default=100)
    ap.add_argument('--N',type=int,required=True)
    ap.add_argument('--prec',type=int,required=True)
    ap.add_argument('--dps',type=int,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    mp.mp.dps=args.dps
    mod=load_module(args.upstream_script)
    A,_=mod.build_arb_tau(args.c,args.N,args.prec)
    E=project_even_arb(A,args.N)

    r=mp.matrix([mp.mpf(1)]+[mp.sqrt(2)]*args.N)
    chi=(r.T*mp.lu_solve(E,r))[0]
    H0=project_even_mp(full_H(args.N,mp.mpf(0)),args.N)
    sigma0,lo0,hi0=sigma_generalized(E,H0)
    endpoint_relerr=abs(sigma0-2*chi)/max(1,abs(2*chi))
    if endpoint_relerr > mp.mpf('1e-30'):
        raise RuntimeError('endpoint identity sigma(0)=2 chi failed: relerr='+mp.nstr(endpoint_relerr,30))

    Lc=mp.log(args.c)
    rows=[]
    total=mp.mpf(0)
    for q,p in prime_powers(args.c):
        omega=1-mp.log(q)/Lc
        H=project_even_mp(full_H(args.N,omega),args.N)
        sigma,lo,hi=sigma_generalized(E,H)
        coeff=mp.log(p)*mp.log(q)/(mp.sqrt(q)*Lc**2)
        contribution=coeff*sigma
        total+=contribution
        rows.append({
            'q':q,'p':p,
            'omega':mp.nstr(omega,40),
            'sigma':mp.nstr(sigma,50),
            'generalized_min':mp.nstr(lo,50),
            'generalized_max':mp.nstr(hi,50),
            'smooth_prime_coefficient':mp.nstr(coeff,40),
            'absolute_relative_bound_contribution':mp.nstr(contribution,50),
            'log10_sigma':float(mp.log10(sigma)) if sigma>0 else None,
        })
    ranked=sorted(rows,key=lambda x: float(mp.mpf(x['absolute_relative_bound_contribution'])),reverse=True)
    out={
        'status':'exploratory_midpoint_interior_susceptibility',
        'warning':'Midpoint generalized eigenvalues only; no interval sign/norm certificate. Endpoint identity is used as a stringent internal validation. This is a strategy stress test, not an RH result.',
        'upstream_commit':args.upstream_commit,'c':args.c,'N':args.N,'prec_bits':args.prec,'mpmath_dps':args.dps,
        'endpoint_chi':mp.nstr(chi,60),
        'endpoint_sigma0':mp.nstr(sigma0,60),
        'endpoint_identity_relative_error':mp.nstr(endpoint_relerr,20),
        'absolute_sum_bound_for_smooth_prime_motion':mp.nstr(total,60),
        'top_contributors':ranked[:12],
        'rows':rows,
        'meaning':'Between prime edges, the prime part derivative is a weighted sum of H(omega_q). sigma is the sharp midpoint generalized operator norm of each H relative to the current positive Weil block E. A huge sigma indicates that a naive absolute Gronwall bound loses the cancellation that makes E positive.'
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'c':args.c,'N':args.N,'chi':out['endpoint_chi'],'sigma0':out['endpoint_sigma0'],'endpoint_relerr':out['endpoint_identity_relative_error'],'smooth_prime_abs_sum':out['absolute_sum_bound_for_smooth_prime_motion'],'top':ranked[:5]},indent=2))

if __name__=='__main__':
    main()
