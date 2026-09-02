# 001 — Prime-power threshold dynamics

## Source normalization

Following Chuk (arXiv:2608.24827), for real even `f` supported in `[-L,L]`, with `F = f_hat`,

\[
Q(f)=2F(i/2)^2+\frac{1}{2\pi}\int_{\mathbb R}|F(t)|^2\Psi_L(t)\,dt,
\]

where

\[
\Psi_L(t)=\operatorname{Re}\psi\!\left(\tfrac14+\tfrac{it}{2}\right)-\log\pi
-\sum_{\log n<2L}\frac{2\Lambda(n)}{\sqrt n}\cos(t\log n).
\]

Only prime powers with `log n < 2L` occur.

Let `g = f * f_tilde`. With the Fourier convention above,

\[
g(x)=\frac{1}{2\pi}\int_{\mathbb R}|F(t)|^2 e^{-itx}\,dt.
\]

For real even `f`, `g` is real even, hence the exact contribution of a single active prime power `n` is

\[
-2\frac{\Lambda(n)}{\sqrt n}\,g(\log n).
\]

This is preferable to reasoning directly from the apparently discontinuous symbol `Psi_L`.

## Fixing the Hilbert space by scaling

Put

\[
f_L(x)=L^{-1/2}h(x/L),\qquad \operatorname{supp}h\subset[-1,1],
\]

so `||f_L||_2 = ||h||_2`. If `g_h = h * h_tilde`, then

\[
g_{f_L}(u)=g_h(u/L).
\]

Therefore the prime-power contribution becomes

\[
P_n(L;h)=-2\frac{\Lambda(n)}{\sqrt n}\,g_h\!\left(\frac{\log n}{L}\right)
\]

for `L > (log n)/2`, and is absent below that threshold.

At the threshold `L_n=(log n)/2`, the autocorrelation is evaluated at the edge `2`. Since an `L^2` autocorrelation is continuous and two compact supports only meet at a null set there,

\[
g_h(2)=0.
\]

Hence **the arithmetic contribution enters continuously across every prime-power threshold**. The step in `Psi_L` is not a jump in the actual quadratic form.

## First derivative: a downward kink

Assume temporarily that `h` has well-defined endpoint traces. For `y = 2-epsilon`, the overlap of the two copies of `h` has width `epsilon`, and

\[
g_h(2-\varepsilon)=\varepsilon\,h(1)\overline{h(-1)}+o(\varepsilon).
\]

For real even `h`,

\[
g_h'(2-)=-|h(1)|^2.
\]

For `L>L_n`, differentiating gives

\[
\frac{d}{dL}P_n(L;h)
=2\frac{\Lambda(n)}{\sqrt n}\frac{\log n}{L^2}
 g_h'\!\left(\frac{\log n}{L}\right).
\]

Thus the right derivative at activation is

\[
P_n'(L_n+;h)
=-8\frac{\Lambda(n)}{\sqrt n\log n}|h(1)|^2.
\]

For `n=p^k`, this simplifies to

\[
P_{p^k}'(L_n+;h)=-\frac{8}{k\sqrt{p^k}}|h(1)|^2.
\]

Below the threshold this contribution has derivative zero, so each prime power produces a downward derivative kink whenever the relevant endpoint trace is nonzero.

### Sanity check: normalized box

For

\[
h(x)=1/\sqrt2\quad (|x|\le1),
\]

\[
g_h(y)=1-|y|/2\quad (|y|\le2).
\]

The derivative jump is therefore

\[
-4\frac{\Lambda(n)}{\sqrt n\log n}=-\frac{4}{k\sqrt{p^k}},
\]

matching the general formula because `|h(1)|^2=1/2`.

## Candidate propagation mechanism

The compact-window infimum is

\[
\lambda^*(L)=\inf_{\|f\|_2=1,\ \operatorname{supp}f\subset[-L,L]}Q(f).
\]

The spaces are nested, so `lambda*(L)` is automatically non-increasing. Under RH it nevertheless stays strictly positive for every finite `L`.

A possible route to global positivity is therefore not ordinary monotonicity, but a **relative differential lower bound** after rescaling to a fixed Hilbert space:

\[
A'(L)\succeq-C(L)A(L),
\]

where `A(L)` is the rescaled Weil-form operator and `C(L)` is locally integrable. Gronwall would then propagate strict positivity from one certified base window to every finite `L`.

The threshold calculation isolates the hard local term: its negative derivative is governed by an endpoint trace. This suggests the concrete question

> Can the endpoint trace of the instantaneous ground state (or, more strongly, of every vector in the form domain) be controlled by the Weil energy strongly enough to obtain a relative form bound?

Schematically, one would want an estimate of the form

\[
|h(1)|^2\le B(L)\,Q_L(h)
\]

(or a variant including an auxiliary coercive norm), because the threshold kink would then be relatively bounded by `Q_L`.

## Immediate obstruction to check

Point evaluation is not bounded on plain `L^2[-1,1]`. Therefore the naive inequality above cannot hold on the whole raw `L^2` space without additional regularity supplied by the Weil form / eigen-equation / a stronger form domain.

This is the first make-or-break question:

1. identify the actual regularity of compact-window minimizers / eigenfunctions;
2. derive the Euler-Lagrange or integral-operator equation;
3. determine whether that equation implies a trace estimate whose constant is explicit in `L`;
4. test the corresponding generalized derivative bound numerically on finite Legendre compressions.

If the relative derivative bound fails badly already in finite compressions, record the counterexample and abandon this route.

## Status

- Exact prime contribution and threshold continuity: derived from the explicit formula normalization.
- Endpoint-kink formula: formal derivation under endpoint regularity assumptions; needs a rigorous function-space statement before being used as a theorem.
- Global positivity propagation: conjectural research direction, not established.
