# Infinite boundary Pick diagnostics beyond smallest eigenvalues

Status: exact finite-dimensional identities plus an elementary infinite-kernel lemma; the compactness passage to an exact infinite boundary interpolant is a theorem target, not an RH claim.

## 1. Why smallest Pick eigenvalues are not the right infinite diagnostic

For a finite boundary Pick problem on distinct real nodes `x_0,...,x_N`, with real values `w_j` and derivative bounds `v_j`, the confluent Pick matrix is

\[
(P_N)_{jj}=v_j,
\qquad
(P_N)_{jk}=\frac{w_j-w_k}{x_j-x_k}\quad(j\ne k).
\]

Agler--Young prove for finitely many boundary nodes that the relaxed problem

\[
f(x_j)=w_j,
\qquad
f'(x_j)\le v_j
\]

is solvable exactly when `P_N >= 0`, while the exact problem is governed by positive definiteness or minimal positivity. Julia reduction corresponds, up to diagonal scaling, to Schur complementation.

A crucial warning comes from Golinskii--Peherstorfer--Yuditskiy (2008): for an infinite Nevanlinna--Pick problem, `lambda_min(P_N) -> 0` does **not** imply determinacy. They exhibit an indeterminate problem whose smallest finite Pick eigenvalues nevertheless tend to zero.

Therefore the extremely small positive eigenvalues observed for the finite CvS/Weil matrices cannot by themselves identify a unique infinite Pick representative.

## 2. Fixed-coordinate diagonal slack capacity

Assume every finite principal matrix `P_N` is positive definite. For a fixed coordinate `j <= N`, define

\[
\boxed{
 c_{j,N}:=\frac{1}{(P_N^{-1})_{jj}}.
}
\]

By the rank-one Schur complement / Sherman--Morrison criterion,

\[
\boxed{
 c_{j,N}
 =\sup\{\varepsilon\ge0:
 P_N-\varepsilon e_je_j^T\succeq0\}.
}
\]

Thus `c_{j,N}` is exactly the amount by which the prescribed derivative at node `j` may still be lowered while preserving finite Pick positivity.

Because the feasible set only shrinks when more interpolation nodes are appended,

\[
 c_{j,N+1}\le c_{j,N}
\]

for every fixed `j`.

### Infinite diagonal-minimality lemma

Let `P` be the infinite Pick kernel understood as a positive quadratic form on finitely supported sequences, and let `P_N` be its nested principal restrictions. Then the following are equivalent:

1. there is no nonzero diagonal operator/form
   \[
   D=\operatorname{diag}(d_0,d_1,\ldots),\qquad d_j\ge0,
   \]
   such that `P-D` remains positive on every finitely supported vector;
2. for every fixed `j`,
   \[
   \boxed{c_{j,N}\longrightarrow0.}
   \]

Proof. If `P-D >= 0` and `d_j>0`, then for every sufficiently large `N`,

\[
P_N-d_je_je_j^T
=(P_N-D_N)+(D_N-d_je_je_j^T)\succeq0,
\]

so `d_j <= c_{j,N}` and the capacities cannot tend to zero. Conversely, if `c_{j,N} -> c_j>0` for some fixed `j`, monotonicity gives

\[
P_N-c_je_je_j^T\succeq0
\]

for every `N >= j`; hence the infinite kernel admits a nonzero diagonal decrement.

This is the infinite-kernel analogue of finite minimal positivity that is relevant to *exact derivative retention*.

## 3. Exactness theorem target

Finite positivity gives a solution of each relaxed finite boundary problem. After Cayley transforming the Pick class to the Schur class, the finite solutions form a normal family. A subsequential interior limit should preserve the Julia inequalities for every fixed boundary datum and therefore give an infinite relaxed interpolant

\[
f(x_j)=w_j,
\qquad d_j:=f'(x_j)\le v_j.
\]

Its boundary Pick kernel on the prescribed nodes is

\[
P-\operatorname{diag}(v_j-d_j).
\]

Consequently, once the normal-family/boundary-passage step is written rigorously, the diagonal-minimality lemma gives

\[
\boxed{
 c_{j,N}\to0\ \forall j
 \quad\Longrightarrow\quad
 d_j=v_j\ \forall j.
}
\]

In words: vanishing fixed-node slack capacities would prevent loss of the prescribed angular derivatives in the infinite limit.

The remaining technical point is to write the normal-family passage using Julia inequalities (or an equivalent boundary-kernel compactness theorem) without silently assuming boundary convergence.

## 4. Interior Weyl value disks from a finite boundary Pick matrix

Fix an interior point

\[
z_0=p+iq,\qquad q>0,
\]

and ask which values `zeta=f(z_0)` are compatible with the first `N+1` relaxed boundary constraints.

Let

\[
M=P_N^{-1},
\qquad
 a_j=\frac{1}{x_j-\overline{z_0}},
\qquad
 c_j=\frac{w_j}{x_j-\overline{z_0}}.
\]

Put

\[
A=a^*Ma>0,
\qquad
B=a^*Mc,
\qquad
C=c^*Mc.
\]

The Schur complement of the augmented Pick matrix gives

\[
\frac{\Im\zeta}{q}
-(c-\overline\zeta a)^*M(c-\overline\zeta a)\ge0,
\]

i.e.

\[
A|\zeta|^2-2\Re(\zeta B)+C-\frac{\Im\zeta}{q}\le0.
\]

Completing the square, the admissible values lie in the disk

\[
\boxed{
|\zeta-m_N(z_0)|\le r_N(z_0),
}
\]

with

\[
\boxed{
m_N(z_0)=\frac{\overline B+i/(2q)}{A},
}
\]

and

\[
\boxed{
r_N(z_0)
=\frac{\sqrt{|B-i/(2q)|^2-AC}}{A}.
}
\]

The finite solution sets are nested when nodes are appended, so their value disks are nested as well.

A collapse `r_N(z_0) -> 0` is therefore a much more relevant uniqueness diagnostic than `lambda_min(P_N) -> 0`. Before using collapse at one point as a complete determinacy theorem for this boundary-data limit, however, the appropriate infinite Weyl-disk theorem must be cited or proved. Numerically we should test several interior points rather than rely on an accidental one-point degeneracy.

## 5. Application to the squared-grid CvS even sector

Note 019 proves

\[
E_N=D_NL_N(G_C)D_N,
\qquad
D_N=\operatorname{diag}(1,\sqrt2,\ldots,\sqrt2),
\]

where `L_N(G_C)` is the confluent Loewner/Pick matrix on

\[
x_k=k^2,
\qquad k=0,\ldots,N.
\]

Thus we can apply the diagnostics directly to

\[
P_N=L_N(G_C)=D_N^{-1}E_ND_N^{-1}.
\]

Since `G_C(0)=0`, the node data can be reconstructed from `P_N` itself:

\[
w_0=0,
\qquad
w_k=k^2(P_N)_{0k}\quad(k>0),
\qquad
v_k=(P_N)_{kk}.
\]

For the newly appended endpoint,

\[
\boxed{c_{N,N}=\sigma_N=s_N/2,}
\]

so the existing Schur-pivot computation provides an exact internal consistency check for the capacity code.

## 6. Immediate falsifiable experiment

Using the pinned cutoff-free Arb CvS matrix, but high-precision midpoints for the inverse diagnostics, compute for `C=13` and `C=100`:

- `c_{j,N}` for fixed `j=0,1,2,3` as `N` grows;
- the endpoint identity `c_{N,N}=s_N/2`;
- value-disk radii at `z_0=i`, `2i`, and `1+i`;
- nesting checks for all three disks.

Interpretation:

- fixed-node capacities tending to zero supports infinite diagonal minimality / exact derivative retention;
- capacities stabilizing above zero falsify that mechanism;
- value disks collapsing at several interior points supports determinacy;
- nonzero limiting radii indicate a genuine family of Pick representatives and kill the uniqueness route.

None of these finite numerical patterns proves RH. Their purpose is to decide which infinite theorem is worth attacking.