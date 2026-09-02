#!/usr/bin/env python3
"""Compare the actual Schur normal with the exact centered finite-difference stencil.

For the even cutoff-free CvS matrix E_N(u), the actual last Schur normal is
w=(-B^{-1}b,1).  In the even Fourier basis, compare it to the vector obtained
from the full centered binomial stencil

    d_m = (-1)^(N-m) binom(2N,N+m), -N<=m<=N.

After projection to the normalized even basis and scaling the last coefficient
to one, the stencil vector is

    v_0 = d_0/sqrt(2),  v_k=d_k (1<=k<=N).

The script compares overlaps, energies and threshold-free log-flow component
cancellations for w and v.  Derivatives use midpoint centered differences; base
matrix and pivot entries originate from rigorous Arb balls.
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


def prime_powers_fixed(c0:int):
    primes=[]
    for x in range(2,c0+1):
        isp=True
        for p in primes:
            if p*p>x: break
            if x%p==0: isp=False; break
        if isp: primes.append(x)
    out=[]
    for p in primes:
        q=p
        while q<=c0:
            out.append((q,p)); q*=p
    return out


def build_components(mod,c_str,N,prec,pdata):
    ctx.prec=prec
    S,CC,XC,L=mod.arb_closed_forms(N,c_str,prec)
    PI=arb.pi(); sp2=16*PI*PI; l2=L*L
    pref02=32*L*(L/4).sinh()**2; kappa=mod.arb_kappa(L); J=mod.arb_J(L)
    weights=[arb(p).log()*(arb(q)**arb('-0.5')) for q,p in pdata]
    positions=[arb(q).log() for q,p in pdata]
    def Ss(n): return S[n] if n>=0 else -S[-n]
    D=2*N+1
    mats={k:arb_mat(D,D) for k in ('pole_W02','arch_minus_WR','prime_minus_Wp','total')}
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
            for idx,y in enumerate(positions):
                if n==m:
                    qv=2*(1-y/L)*(2*PI*n*y/L).cos()
                else:
                    qv=((2*PI*m*y/L).sin()-(2*PI*n*y/L).sin())/(PI*(n-m))
                Wp += weights[idx]*qv
            vals={'pole_W02':W02,'arch_minus_WR':-WR,'prime_minus_Wp':-Wp}
            vals['total']=sum(vals.values(),arb(0))
            for key,v in vals.items():
                mats[key][i,j]=v; mats[key][j,i]=v
    return mats


def project_even(A,N):
    root2=arb(2).sqrt(); c=N; E=arb_mat(N+1,N+1); E[0,0]=A[c,c]
    for k in range(1,N+1):
        v=(A[c,c+k]+A[c,c-k])/root2; E[0,k]=v; E[k,0]=v
    for k in range(1,N+1):
        for j in range(k,N+1):
            v=(A[c+k,c+j]+A[c+k,c-j]+A[c-k,c+j]+A[c-k,c-j])/2
            E[k,j]=v; E[j,k]=v
    return E


def mid(x,digits): return mp.mpf(x.mid().str(digits,radius=False))
def to_mp(A,digits): return mp.matrix([[mid(A[i,j],digits) for j in range(A.ncols())] for i in range(A.nrows())])
def qform(v,A): return (v.T*A*v)[0]

def actual_schur_normal(M,N):
    if N==0: return mp.matrix([1])
    B=M[:N,:N]; b=M[:N,N]; x=mp.lu_solve(B,b)
    w=mp.matrix(N+1,1)
    for i in range(N): w[i]=-x[i]
    w[N]=1
    return w


def exact_even_stencil(N):
    v=mp.matrix(N+1,1); root2=mp.sqrt(2)
    for k in range(N+1):
        d=mp.mpf(((-1)**(N-k))*math.comb(2*N,N+k))
        v[k]=d/root2 if k==0 else d
    return v


def describe_vector(name,v,E0,Hs):
    energy=qform(v,E0)
    parts={k:qform(v,H)/energy for k,H in Hs.items() if k!='total'}
    total=qform(v,Hs['total'])/energy
    cancellation=sum(abs(x) for x in parts.values())/abs(sum(parts.values()))
    return {
        'name':name,
        'l2_norm':mp.nstr(mp.norm(v),70),
        'energy':mp.nstr(energy,80),
        'component_log_flow':{k:mp.nstr(x,80) for k,x in parts.items()},
        'component_sum':mp.nstr(sum(parts.values()),80),
        'total_directional_log_flow':mp.nstr(total,80),
        'sum_abs_over_abs_sum':mp.nstr(cancellation,60),
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--upstream-script',type=Path,required=True); ap.add_argument('--upstream-commit',required=True)
    ap.add_argument('--c0',type=int,default=100); ap.add_argument('--N',type=int,required=True); ap.add_argument('--prec',type=int,required=True); ap.add_argument('--dps',type=int,required=True); ap.add_argument('--h',required=True); ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); mp.mp.dps=args.dps; digits=args.dps+30; h=mp.mpf(args.h); mod=load_module(args.upstream_script); pdata=prime_powers_fixed(args.c0); u0=mp.log(args.c0)
    def at(u):
        raw=build_components(mod,mp.nstr(mp.e**u,digits),args.N,args.prec,pdata)
        return {k:project_even(v,args.N) for k,v in raw.items()}
    base=at(u0); plus=at(u0+h); minus=at(u0-h)
    E0=to_mp(base['total'],digits)
    Hs={k:(to_mp(plus[k],digits)-to_mp(minus[k],digits))/(2*h) for k in base}
    w=actual_schur_normal(E0,args.N); v=exact_even_stencil(args.N)
    # Both have last coefficient 1 by construction.
    overlap=abs((w.T*v)[0])/(mp.norm(w)*mp.norm(v))
    dist=mp.norm(w/mp.norm(w)-mp.sign((w.T*v)[0])*v/mp.norm(v))
    Dw=describe_vector('actual_schur_normal',w,E0,Hs)
    Dv=describe_vector('exact_centered_stencil',v,E0,Hs)
    out={
      'status':'exploratory_exact_stencil_vs_schur_normal_flow',
      'warning':'Matrix entries originate from Arb, but vector solves and derivative qforms use high-precision midpoints. This is a threshold-free exploratory comparison.',
      'upstream_commit':args.upstream_commit,'c0':args.c0,'N':args.N,'prec_bits':args.prec,'mpmath_dps':args.dps,'h':args.h,
      'absolute_normalized_overlap':mp.nstr(overlap,80),'sign_aligned_normalized_l2_distance':mp.nstr(dist,80),
      'actual_over_stencil_energy':mp.nstr(mp.mpf(Dw['energy'])/mp.mpf(Dv['energy']),80),
      'vectors':[Dw,Dv],
      'meaning':'If the exact centered stencil reproduces the moderate total flow and huge component cancellation, the mechanism is largely finite-difference algebra. If not, the correction from stencil to the actual Schur normal carries essential cancellation information.'
    }
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
