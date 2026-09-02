# 002 — Operator-norm obstruction at prime-power thresholds

This note corrects an overly optimistic interpretation of threshold continuity from note 001.

## Fixed-vector continuity is not operator-norm continuity

After scaling to `[-1,1]`, let

\[
(T_y h)(x)=h(x-y)
\]

where the translated point remains inside `[-1,1]` (equivalently extend `h` by zero outside the interval). The autocorrelation is

\[
g_h(y)=\langle h,T_y h\rangle.
\]

A prime-power term with `a = log n` uses `y=a/L`. At activation, `L downarrow a/2` from above and therefore `y \uparrow 2`.

For every fixed `h in L^2[-1,1]`,

\[
\langle h,T_y h\rangle\to0\qquad(y\uparrow2),
\]

because the overlap region shrinks to measure zero. This is the continuity observed in note 001.

However, for every `y<2`, write `delta=2-y>0`. The operator maps the left interval `[-1,-1+delta]` isometrically onto the right interval `[1-delta,1]`. Choosing a unit vector supported entirely in that shrinking left interval gives

\[
\|T_y\|=1\qquad\text{for every }y<2,
\]

while at `y=2` the overlap has measure zero and `T_2=0` as an `L^2` operator.

Thus

\[
T_y\to0\quad\text{strongly, but not in operator norm, as }y\uparrow2.
\]

The self-adjoint part entering the real quadratic form has the same qualitative obstruction: its norm remains bounded away from zero although every fixed-vector matrix element vanishes.

## Consequence

A naive plan to place all rescaled Weil forms on one fixed `L^2[-1,1]` and prove global positivity by standard norm-continuous Kato perturbation theory cannot work across prime-power thresholds without additional structure.

Likewise, a uniform whole-space relative inequality of the schematic form

\[
A'(L)\succeq-C(L)A(L)
\]

cannot be justified merely by saying that a newly activated prime term is small near its threshold. It is not small in operator norm.

## What remains viable

The obstruction is caused by vectors concentrating in arbitrarily small endpoint intervals. Therefore a spectral-flow strategy can only survive if low-energy vectors of the Weil form are quantitatively prevented from doing this.

The next target should be a **low-energy endpoint concentration estimate**, for example a statement of the following type:

\[
\int_{1-\delta}^{1}|h(x)|^2\,dx
+\int_{-1}^{-1+\delta}|h(x)|^2\,dx
\le E(L,\delta)\,\mathcal E_L(h),
\]

for vectors in a suitable low-energy/form domain, with `E(L,delta) -> 0` as `delta -> 0` strongly enough to defeat the norm-one partial shift.

Possible sources of such control:

1. an archimedean coercive term hidden in the Weil form;
2. regularity of eigenfunctions from the integral/eigenvalue equation;
3. compactness of a low-energy spectral projection;
4. a Sobolev-type estimate derived from the high-frequency logarithmic growth of the digamma symbol.

The fourth possibility is particularly attractive: the archimedean part has asymptotic symbol roughly `log |t|`, so the natural form domain resembles a logarithmic Sobolev space. The key question is whether that weak logarithmic regularity is enough to make endpoint concentration quantitatively expensive. Ordinary point traces require much more than logarithmic regularity, so a pointwise endpoint bound may be too strong; a shrinking-interval mass estimate is the more realistic object.

## Important correction

- For each fixed test vector, the arithmetic quadratic contribution enters continuously at a threshold.
- This does **not** imply operator-norm continuity of the rescaled quadratic-form operator.
- It also does **not** by itself prove continuity of the variational infimum `lambda*(L)`, because minimizing vectors may depend on `L` and concentrate near the shrinking overlap.

Any later argument must keep these three notions separate.

## Status

This is a rigorous elementary obstruction at the level of translation operators. The connection to the full Weil form is structural; whether the archimedean energy suppresses the bad concentrating vectors strongly enough is the next research problem.
