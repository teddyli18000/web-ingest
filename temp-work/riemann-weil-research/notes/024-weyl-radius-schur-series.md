# Weyl radii and fixed-node slack as positive Schur-normal series

Status: exact finite-dimensional algebra for real confluent Loewner matrices, plus a direct comparison with classical Weyl-circle criteria. No RH claim.

This note sharpens note 022. The two infinite diagnostics introduced there -- fixed-node derivative slack and interior value-disk radius -- are not merely quantities that can be evaluated from `P_N^{-1}`. They admit monotone positive-term expansions in the same Schur normals and Schur pivots already studied in notes 015--021.

This is the finite algebraic bridge to the classical Jacobi/Weyl-circle determinacy criterion.

## 1. Real Loewner data and the displacement identity

Let

\[
x_0,\ldots,x_N\in\mathbb R
\]

be distinct and let `w_j` be real target values. Let `P_N` be a positive-definite confluent Loewner/Pick matrix,

\[
(P_N)_{ij}=\frac{w_i-w_j}{x_i-x_j}\quad(i\ne j),
\qquad
(P_N)_{ii}=v_i.
\]

Put

\[
X=\operatorname{diag}(x_0,\ldots,x_N),
\qquad
\mathbf 1=(1,\ldots,1)^T,
\qquad
w=(w_0,\ldots,w_N)^T.
\]

Then the off-diagonal Loewner identity and the vanishing diagonal commutator give

\[
\boxed{
XP_N-P_NX=w\mathbf1^T-\mathbf1w^T.
}
\]

Equivalently, with

\[
U=(\mathbf1\ \ w),
\qquad
J=\begin{pmatrix}0&-1\\1&0\end{pmatrix},
\]

we have

\[
\boxed{XP_N-P_NX=UJU^T.}
\]

This rank-two displacement identity is the source of the exact Weyl-circle formula below.

## 2. Finite value disk at an interior point

Fix

\[
z=p+iq\in\mathbb C_+,
\qquad q>0,
\]

and let

\[
M=P_N^{-1}.
\]

Define

\[
a=(X-\overline z I)^{-1}\mathbf1,
\qquad
c=(X-\overline z I)^{-1}w,
\]

and

\[
A=a^*Ma,
\qquad
B=a^*Mc,
\qquad
C=c^*Mc.
\]

The augmented Pick-matrix Schur complement gives the admissible-value disk from note 022:

\[
A|\zeta|^2-2\Re(\zeta B)+C-\frac{\Im\zeta}{q}\le0.
\]

Its center is

\[
m_N(z)=\frac{\overline B+i/(2q)}{A},
\]

and its a priori radius is

\[
r_N(z)=\frac{\sqrt{|B-i/(2q)|^2-AC}}{A}.
\]

The numerical probe found, to hundreds of digits, that the discriminant was exactly `1/(4q^2)` for every tested cutoff, prefix, and interior point. This is an algebraic identity, not a numerical coincidence.

## 3. Exact Loewner Weyl-circle identity

We prove

\[
\boxed{
AC-|B|^2=-\frac{\Im B}{q}.
}
\]

Consequently

\[
\boxed{
|B-i/(2q)|^2-AC=\frac1{4q^2},
}
\]

and therefore

\[
\boxed{
r_N(z)=\frac{1}{2q\,A_N(z)},
\qquad
A_N(z):=a^*P_N^{-1}a.
}
\]

### Proof by the Loewner displacement relation

Let

\[
R=(X-\overline z I)^{-1},
\qquad
W=RU=(a\ \ c),
\qquad
G=W^*MW=
\begin{pmatrix}A&B\\\overline B&C\end{pmatrix}.
\]

The inverse displacement relation is

\[
MX-XM=MUJU^TM.
\]

Set

\[
H=U^TMW.
\]

Since `U=(X-\bar z I)W` and hence `U^T=W^*(X-zI)`, a direct substitution of the inverse displacement identity gives

\[
H=H^*-2iqG-H^*JH.
\]

Define

\[
T=I-JH.
\]

Then

\[
T^*JT
=J+H-H^*+H^*JH
=J-2iqG.
\]

It remains to compute `det T`. By `det(I-AB)=det(I-BA)` and the original displacement identity,

\[
\begin{aligned}
\det T
&=\det\left(I-JU^TMRU\right)\\
&=\det\left(I-RUJU^TM\right)\\
&=\det\left(I-R(XP_N-P_NX)M\right).
\end{aligned}
\]

Using `P_NM=I` and `R=(X-\bar zI)^{-1}`,

\[
\begin{aligned}
I-R(XP_N-P_NX)M
&=I-RX+RP_NXM\\
&=RP_N(X-\bar zI)M.
\end{aligned}
\]

Therefore

\[
\det T
=\det R\,\det P_N\,\det(X-\bar zI)\,\det M
=1.
\]

Since `det J=1`, taking determinants in

\[
T^*JT=J-2iqG
\]

gives

\[
\det(J-2iqG)=1.
\]

Expanding the left side yields

\[
1-4q\Im B-4q^2(AC-|B|^2)=1,
\]

which is exactly the claimed identity.

## 4. Schur recursion for the Weyl evaluation quantity

Write the nested matrix as

\[
P_N=
\begin{pmatrix}
P_{N-1}&b_N\\
b_N^T&d_N
\end{pmatrix},
\]

with Schur pivot

\[
\sigma_N=d_N-b_N^TP_{N-1}^{-1}b_N>0.
\]

Normalize the Schur normal by its new coordinate:

\[
\boxed{
u_N=
\binom{-P_{N-1}^{-1}b_N}{1}.}
\]

Let

\[
a_N(z)=
\left(
\frac1{x_0-\bar z},\ldots,
\frac1{x_N-\bar z}
\right)^T.
\]

The block-inverse identity gives

\[
\begin{aligned}
A_N(z)
&=a_N(z)^*P_N^{-1}a_N(z)\\
&=A_{N-1}(z)
+\frac{\left|a_N^{(N)}-b_N^TP_{N-1}^{-1}a_{N-1}\right|^2}{\sigma_N}.
\end{aligned}
\]

But the numerator is `|u_N^T a_N(z)|^2`. Define the barycentric denominator associated with the Schur normal,

\[
R_{u_N}(\zeta)
=\sum_{k=0}^N\frac{(u_N)_k}{\zeta-x_k}.
\]

Because `u_N` is real,

\[
|u_N^Ta_N(z)|=|R_{u_N}(z)|.
\]

Hence

\[
\boxed{
A_N(z)=A_{N-1}(z)
+\frac{|R_{u_N}(z)|^2}{\sigma_N}.
}
\]

Iterating,

\[
\boxed{
A_N(z)
=\frac{|R_{u_0}(z)|^2}{\sigma_0}
+\sum_{n=1}^N\frac{|R_{u_n}(z)|^2}{\sigma_n},
}
\]

where the one-node initialization is understood in the obvious way.

Combining with the exact radius formula,

\[
\boxed{
r_N(z)
=\frac{1}{
2\Im z\displaystyle\sum_{n=0}^N
|R_{u_n}(z)|^2/\sigma_n}.
}
\]

Thus Weyl-disk collapse is a positive-series divergence problem; there are no large-sign cancellations left to control.

## 5. Fixed-node slack capacities have the same positive-series structure

The block inverse recursion also gives, for every old coordinate `j<N`,

\[
(P_N^{-1})_{jj}
=(P_{N-1}^{-1})_{jj}
+\frac{|(P_{N-1}^{-1}b_N)_j|^2}{\sigma_N}.
\]

Since

\[
(u_N)_j=-(P_{N-1}^{-1}b_N)_j,
\]

and at the step when coordinate `j` is introduced

\[
(P_j^{-1})_{jj}=\frac1{\sigma_j},
\]

we obtain

\[
\boxed{
\frac1{c_{j,N}}
=\frac1{\sigma_j}
+\sum_{n=j+1}^N\frac{|(u_n)_j|^2}{\sigma_n}.
}
\]

Therefore the infinite diagonal-minimality condition of note 022 is equivalent to

\[
\boxed{
\forall j:\qquad
\sum_{n=j}^\infty\frac{|(u_n)_j|^2}{\sigma_n}=\infty,
}
\]

with the convention `(u_j)_j=1`.

Again, this is a positive divergence criterion rather than a smallest-eigenvalue statement.

## 6. Direct comparison with the human Weyl-circle criterion

Derevyagin's Jacobi-matrix treatment of the infinite interior Nevanlinna--Pick problem gives finite Weyl-circle radii of the form

\[
r_N(z)
=\frac{1}{2\Im z\sum_{k<N}|\mathcal P_k(z)|^2},
\]

for normalized rational functions generated by the multipoint Jacobi recursion. Determinacy is equivalent to divergence of the corresponding square sum, equivalently collapse of the nested Weyl disks at one nonreal point.

The exact finite formula above shows that our normalized squared-grid Schur-normal functions

\[
\boxed{
\mathcal R_n(z)=\frac{R_{u_n}(z)}{\sqrt{\sigma_n}}
}
\]

play precisely the same algebraic role:

\[
A_N(z)=\sum_{n=0}^N|\mathcal R_n(z)|^2.
\]

This does **not** yet permit direct invocation of Derevyagin's infinite theorem, because his interpolation nodes are interior points in the upper half-plane and carry value data, whereas the CvS squared-grid nodes are real boundary nodes with angular-derivative data. The remaining bridge is now sharply identified: construct the associated moment/symmetric-operator realization for the boundary Hermite kernel, or use an existing boundary-to-Hamburger reduction.

Relevant human work includes:

- Sarason, *Nevanlinna-Pick interpolation with boundary data* (1998);
- Agler--Young, *Boundary Nevanlinna-Pick interpolation via reduction and augmentation*;
- Chen--Hu, *Multiple Nevanlinna-Pick interpolation with both interior and boundary data and its connection with the power moment problem* (2001);
- Hu--Wei--Chen, *Boundary Nevanlinna-Pick interpolation for Nevanlinna matrix functions and the related Hamburger matrix moment problem* (2009);
- Derevyagin, *The Jacobi matrices approach to Nevanlinna-Pick problems* (2010).

The 2001 and 2009 papers are especially relevant because they explicitly reduce finite boundary interpolation problems to Hamburger-type moment problems.

## 7. Numerical evidence from the cutoff-free CvS matrices

The high-precision midpoint experiment of note 022 was run at `C=13` and `C=100` through `N=48`, using the pinned cutoff-free Arb matrix as its source.

At `C=100`, for fixed node `j=0`,

\[
\log_{10}c_{0,N}
\approx
-18.0,-30.8,-42.1,-51.7,-69.8,-86.1,-115.0
\]

at

\[
N=4,8,12,16,24,32,48.
\]

At the same prefixes,

\[
\log_{10}r_N(i)
\approx
-18.0,-30.8,-42.0,-51.7,-69.7,-86.1,-114.9.
\]

The disks at `i`, `2i`, and `1+i` were nested at every reported transition, and their centers stabilized rapidly while their radii continued collapsing.

At `C=13`, the fixed-node capacities likewise fall to roughly `10^-55` by `N=48`, even though the newly appended endpoint Schur pivot eventually becomes much larger. This cleanly separates endpoint positivity from infinite diagonal minimality.

These are midpoint diagnostics, not asymptotic proofs. Their value is that they strongly favor the positive-series divergence target rather than a positive limiting radius/capacity.

## 8. Next theorem target

For fixed cutoff `C`, prove one or both of

\[
\boxed{
\sum_{n=0}^\infty
\frac{|R_{u_n}(z_0)|^2}{\sigma_n}=\infty
}
\]

at one nonreal point `z_0`, and

\[
\boxed{
\forall j:\quad
\sum_{n=j}^\infty
\frac{|(u_n)_j|^2}{\sigma_n}=\infty.
}
\]

The first is the exact Weyl-radius collapse condition. The second is exact infinite diagonal minimality and would prevent loss of boundary derivatives in a relaxed compactness limit.

The squared-grid Hermite factorization of note 019 and the explicit analytic normal form of the source in notes 017--018 are the natural inputs for estimating the terms. Unlike `lambda_min(P_N)`, these series are monotone and cannot be defeated by hidden cancellation.