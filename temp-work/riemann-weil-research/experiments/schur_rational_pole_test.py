#!/usr/bin/env python3
"""Pole/residue diagnostic for the Schur barycentric rational interpolant.

For the cutoff-free CvS confluent Loewner matrix Q_psi on {-N,...,N}, build
the last even Schur normal u and

    R(z) = sum_m u_m/(z-m),
    S(z) = sum_m u_m psi(m)/(z-m),
    r(z) = S(z)/R(z).

The poles of r are zeros of the even numerator polynomial P in R=P/D_N.
Write P(z)=q(z^2), interpolate q from the exact node values
P(k)=u_k D_N'(k), and compute its roots at high precision.

For a rational odd Pick/Herglotz function with representation

    r(z)=a z + sum_j 2 c_j z/(t_j^2-z^2), c_j>0,

all finite poles are real symmetric pairs and their residues (at z=+/-t_j)
are negative.  This script is an exploratory falsification diagnostic; the
matrix/pivots originate from Arb but polynomial roots/residues use high-
precision midpoints.
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


def project_even(A,N):
    E=arb_mat(N+1,N+1); root2=arb(2).sqrt(); c=N
    E[0,0]=A[c,c]
    for k in range(1,N+1):
        v=(A[c,c+k]+A[c,c-k])/root2; E[0,k]=v; E[k,0]=v
    for k in range(1,N+1):
        for j in range(k,N+1):
            v=(A[c+k,c+j]+A[c+k,c-j]+A[c-k,c+j]+A[c-k,c-j])/2
            E[k,j]=v; E[j,k]=v
    return E


def signed_ldlt(E):
    n=E.nrows(); L=[[arb(0) for _ in range(n)] for _ in range(n)]; d=[None]*n
    for i in range(n):
        L[i][i]=arb(1); s=E[i,i]
        for k in range(i): s-=L[i][k]*L[i][k]*d[k]
        if not (s>0 or s<0): raise RuntimeError(f'undetermined pivot {i}')
        d[i]=s
        for j in range(i+1,n):
            t=E[j,i]
            for k in range(i): t-=L[j][k]*L[i][k]*d[k]
            L[j][i]=t/d[i]
    return L,d


def schur_normal_even(L,N):
    if N==0:return [arb(1)]
    ell=[L[N][j] for j in range(N)]; x=[arb(0) for _ in range(N)]
    for i in range(N-1,-1,-1):
        t=ell[i]
        for j in range(i+1,N): t-=L[j][i]*x[j]
        x[i]=t
    return [-z for z in x]+[arb(1)]


def amid(x,digits): return mp.mpf(x.mid().str(digits,radius=False))


def poly_add(a,b):
    n=max(len(a),len(b)); out=[mp.mpf('0')]*n
    for i in range(n): out[i]=(a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0)
    return out


def poly_scale(a,c): return [c*x for x in a]

def poly_mul_linear(a,root):
    # ascending coefficients times (x-root)
    out=[mp.mpf('0')]*(len(a)+1)
    for i,x in enumerate(a):
        out[i] += -root*x; out[i+1] += x
    return out


def interpolate_ascending(xs,ys):
    # Newton divided differences -> monomial ascending coefficients.
    dd=list(ys); n=len(xs)
    for j in range(1,n):
        for i in range(n-1,j-1,-1):
            dd[i]=(dd[i]-dd[i-1])/(xs[i]-xs[i-j])
    poly=[mp.mpf('0')]; basis=[mp.mpf('1')]
    for i in range(n):
        poly=poly_add(poly,poly_scale(basis,dd[i]))
        basis=poly_mul_linear(basis,xs[i])
    return poly


def Dprime(N,k):
    # prod_{j=-N,j!=k}^N (k-j)
    return mp.mpf((-1)**(N-k))*mp.factorial(N+k)*mp.factorial(N-k)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--upstream-script',type=Path,required=True)
    ap.add_argument('--upstream-commit',required=True)
    ap.add_argument('--c',type=int,default=100)
    ap.add_argument('--N',type=int,required=True)
    ap.add_argument('--prec',type=int,required=True)
    ap.add_argument('--dps',type=int,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); ctx.prec=args.prec; mp.mp.dps=args.dps; digits=args.dps+30
    mod=load_module(args.upstream_script)
    A,_=mod.build_arb_tau(args.c,args.N,args.prec)
    E=project_even(A,args.N); L,d=signed_ldlt(E); v=schur_normal_even(L,args.N)
    root2=mp.sqrt(2)
    # full symmetric residues u_m
    u={0:amid(v[0],digits)}
    for k in range(1,args.N+1): u[k]=u[-k]=amid(v[k],digits)/root2

    # q(x)=P(z) at x=z^2 from P(k)=u_k D_N'(k), k=0..N.
    xs=[mp.mpf(k*k) for k in range(args.N+1)]
    ys=[u[k]*Dprime(args.N,k) for k in range(args.N+1)]
    coeff_asc=interpolate_ascending(xs,ys)
    # normalize to monic-ish scale for root solver
    coeff_desc=list(reversed(coeff_asc)); lead=coeff_desc[0]; coeff_desc=[x/lead for x in coeff_desc]
    roots_x=mp.polyroots(coeff_desc,maxsteps=3000,error=False,extraprec=100)
    roots_x=sorted(roots_x,key=lambda z:(float(mp.re(z)),float(mp.im(z))))

    cidx=args.N
    # psi(0)=0 for odd combined source; for m != 0, psi(m)=m Q_{m0}.
    psi={0:mp.mpf('0')}
    for m in range(-args.N,args.N+1):
        if m!=0:
            psi[m]=mp.mpf(m)*amid(A[m+cidx,cidx],digits)

    def R(z): return mp.fsum(u[m]/(z-m) for m in range(-args.N,args.N+1))
    def Rp(z): return -mp.fsum(u[m]/((z-m)**2) for m in range(-args.N,args.N+1))
    def S(z): return mp.fsum(u[m]*psi[m]/(z-m) for m in range(-args.N,args.N+1))

    root_rows=[]; all_positive_x=True; max_im_x=mp.mpf('0'); residues=[]
    for x in roots_x:
        max_im_x=max(max_im_x,abs(mp.im(x)))
        is_pos=abs(mp.im(x)) < mp.mpf(10)**(-(args.dps//3)) and mp.re(x)>0
        all_positive_x = all_positive_x and is_pos
        row={'x_root':mp.nstr(x,80),'imag_abs':mp.nstr(abs(mp.im(x)),30),'positive_real_x':bool(is_pos)}
        if is_pos:
            t=mp.sqrt(mp.re(x)); res=S(t)/Rp(t); residues.append(res)
            row.update({'positive_pole':mp.nstr(t,70),'residue_at_positive_pole':mp.nstr(res,70),'residue_negative':bool(mp.re(res)<0 and abs(mp.im(res))<mp.mpf(10)**(-(args.dps//3)))})
        root_rows.append(row)

    residue_all_negative=bool(residues and all(mp.re(r)<0 and abs(mp.im(r))<mp.mpf(10)**(-(args.dps//3)) for r in residues))
    # Interlacing diagnostic: count positive poles in each node interval (k,k+1), and beyond N.
    pos_poles=sorted([mp.sqrt(mp.re(x)) for x in roots_x if abs(mp.im(x))<mp.mpf(10)**(-(args.dps//3)) and mp.re(x)>0])
    interval_counts=[]
    for k in range(args.N):
        count=sum(1 for t in pos_poles if mp.mpf(k)<t<mp.mpf(k+1))
        interval_counts.append({'interval':f'({k},{k+1})','count':count})
    beyond=sum(1 for t in pos_poles if t>args.N)

    # asymptotic coefficient: if r(z)~C/z, C=(sum m u_m psi(m))/(sum u_m), provided denominator nonzero.
    sumu=mp.fsum(u.values()); mom=mp.fsum(mp.mpf(m)*u[m]*psi[m] for m in range(-args.N,args.N+1))
    asym_c=mom/sumu if sumu else mp.nan

    out={
      'status':'exploratory_schur_barycentric_rational_pole_test',
      'warning':'Schur pivots/matrix use Arb; polynomial roots and residues are high-precision midpoint diagnostics, not root-isolation certificates.',
      'upstream_commit':args.upstream_commit,'c':args.c,'N':args.N,'prec_bits':args.prec,'mpmath_dps':args.dps,
      'schur_pivot_mid':d[args.N].mid().str(80,radius=False),
      'q_degree':args.N,'all_q_roots_positive_real':all_positive_x,'max_abs_imag_q_root':mp.nstr(max_im_x,40),
      'all_finite_pole_residues_negative':residue_all_negative,
      'positive_pole_count':len(pos_poles),'expected_positive_pole_count':args.N,
      'interval_counts_between_nonnegative_integer_nodes':interval_counts,'positive_poles_beyond_N':beyond,
      'sum_barycentric_weights':mp.nstr(sumu,70),'r_asymptotic_C_over_z':mp.nstr(asym_c,70),
      'roots':root_rows,
      'meaning':'All q-roots positive real plus negative residues is the finite-pole signature expected for an odd rational Pick/Herglotz function in the convention r(z)=a z+sum 2c_j z/(t_j^2-z^2), c_j>0. This diagnostic can falsify but does not rigorously prove Pick membership.'
    }
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
