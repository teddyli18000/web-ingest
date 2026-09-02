# Exact CvS dictionary bridge to the compact-window source

Status: exact algebraic identification using the definitions in Akiva Groskin's 2026 finite Guinand--Weil dictionary. This note fixes the normalization needed by the source-escape experiment.

## 1. Dictionary definitions

For cutoff `c>1`, Groskin sets

\[
L_g=\log c,\qquad \Delta=\frac{L_g}{2\pi}.
\]

For a real even Galerkin coefficient vector, use symmetric coefficients
`u_{-m}=u_m` and define

\[
T_v(t)=\sum_{m=-N}^{N}u_m e^{2\pi i mt}.
\]

The dictionary then defines

\[
K_v(\omega)=2\int_0^\omega T_v(t)T_v(\omega-t)\,dt
\]

and

\[
\widehat g_v(\xi)=
\begin{cases}
\pi K_v(1-|\xi|/\Delta),&|\xi|\le\Delta,\\
0,&|\xi|>\Delta.
\end{cases}
\]

These are the definitions in the source of *A finite Guinand--Weil dictionary and archimedean tail order for the truncated Weil quadratic form* (2026).

## 2. `K_v` is exactly the source autocorrelation

Symmetry of the coefficients gives

\[
T_v(1-s)
=\sum_m u_m e^{-2\pi i ms}
=T_v(s),
\]

because `u_{-m}=u_m` and the even-sector source is real.

For `0<=r<=1`,

\[
\begin{aligned}
K_v(1-r)
&=2\int_0^{1-r}T_v(t)T_v(1-r-t)\,dt\\
&=2\int_0^{1-r}T_v(t)T_v(t+r)\,dt.
\end{aligned}
\]

If

\[
h_v(t)=T_v(t)\mathbf 1_{[0,1]}(t),
\]

then its real autocorrelation is

\[
C_v(r)=\int_{\mathbb R}h_v(t)h_v(t+r)\,dt
=\int_0^{1-r}T_v(t)T_v(t+r)\,dt
\]

for `0<=r<=1`, and `C_v` is even. Hence

\[
\boxed{K_v(1-|r|)=2C_v(r).}
\]

This makes the apparently Volterra-form dictionary into an ordinary compact-support autocorrelation after the even-sector symmetry is used.

## 3. Exact compact-support source whose autocorrelation is `ghat_v`

Define a scaled source on the `xi` variable by

\[
\phi_v(x)=\sqrt{\frac{2\pi}{\Delta}}\,
T_v(x/\Delta)\mathbf 1_{[0,\Delta]}(x).
\]

For `|xi|<=Delta`,

\[
\begin{aligned}
(\phi_v*\widetilde\phi_v)(\xi)
&=\int\phi_v(x)\phi_v(x+\xi)\,dx\\
&=2\pi C_v(\xi/\Delta)\\
&=\pi K_v(1-|\xi|/\Delta)\\
&=\widehat g_v(\xi),
\end{aligned}
\]

up to the harmless sign convention in the definition of the reflected convolution. Both sides are even, so the convention does not affect the identity.

Outside `[-Delta,Delta]`, both autocorrelations vanish. Therefore

\[
\boxed{\widehat g_v=\phi_v*\widetilde\phi_v.}
\]

Thus the Galerkin coefficient vector already determines an explicit compact-support **source** for Weil's autocorrelation criterion. Endpoint/source regularity diagnostics are not ad hoc proxies.

A translation of `phi_v` centers its support without changing the autocorrelation, so it may equivalently be viewed as supported in

\[
[-\Delta/2,\Delta/2].
\]

## 4. Normalization bridge to the additive window `[-L,L]`

Groskin reconstructs the test function with Fourier convention

\[
g_v(z)=\int\widehat g_v(\xi)e^{2\pi iz\xi}\,d\xi.
\]

If the additive compact-window convention uses angular frequency `e^{itx}`, the spatial coordinate is scaled by

\[
x=2\pi\xi.
\]

Therefore the centered source support width is

\[
2\pi\Delta=\log c.
\]

Writing the standard symmetric window as `[-L_win,L_win]` gives the exact support relation

\[
\boxed{
2L_{\rm win}=\log c,
\qquad
L_{\rm win}=\frac12\log c.
}
\]

This also matches the arithmetic threshold exactly:

\[
n\le c
\quad\Longleftrightarrow\quad
\log n\le\log c=2L_{\rm win}.
\]

So the finite prime-power cutoff in the CvS/CCM matrix is precisely the prime-power support cutoff of the compact-window Weil form, modulo endpoint strict-vs-nonstrict conventions at the measure-zero threshold.

Examples:

- `c=13` corresponds to `L_win = log(13)/2 ~= 1.28247`;
- `c=100` corresponds to `L_win = log(100)/2 ~= 2.30259`;
- the Chuk `L=0.8` certificate corresponds to `c=e^1.6 ~= 4.95303` in this normalization.

## 5. Source-space metrics available directly from an eigenvector

The `connes-cvs` package returns a normalized full even coefficient vector

\[
u=(u_{-N},\dots,u_N),\qquad\sum|u_k|^2=1.
\]

Because the exponentials are orthonormal on `[0,1]`,

\[
\int_0^1|T_v(t)|^2dt=1.
\]

Two diagnostics are therefore immediate.

### Endpoint mass

For `0<eps<=1/2`,

\[
M_{\rm edge}(\varepsilon)
=\int_0^\varepsilon|T_v|^2
+\int_{1-\varepsilon}^1|T_v|^2.
\]

This can be evaluated exactly as a finite coefficient double sum, with no sampling grid.

### Periodic logarithmic frequency energy

Define

\[
E_{\log}^{\mathbb T}(v)
=\sum_{k=-N}^{N}|u_k|^2\log(e+|k|).
\]

This is the quadratic form of a logarithmic-order Fourier multiplier on the source circle. It is **not** being identified with the exact Dirichlet logarithmic-Laplacian energy from Note 003; constants and boundary realization differ. Its role is simpler and rigorous: because the weights tend to infinity, bounded `E_log^T` gives a compact subset of `L2(S^1)`.

Hence a normalized source sequence that converges weakly to zero or concentrates on finer and finer spatial scales cannot keep `E_log^T` bounded.

## 6. Numerical protocol now running

The temporary experiment

`experiments/source_escape_diagnostic.py`

uses the public `connes-cvs==0.3.1` package and, for nested Galerkin sizes, records:

- finite-`T` ground-state eigenvalue (explicitly **not** treated as a sign certificate);
- periodic logarithmic source energy;
- mass in the outer quarter of Fourier modes;
- exact endpoint mass at fixed strips `eps=0.10,0.05`;
- exact endpoint mass at the shrinking scale `eps=1/N`;
- source values at `0` and `1/2`.

A temporary no-schedule GitHub Actions probe runs this in the public repository because the local sandbox has no package-network access.

## 7. What would count as interesting

As `N` grows at fixed `c`:

- if a suspicious finite-dimensional mode has growing endpoint mass at scale `1/N`, growing high-frequency coefficient mass, and growing `E_log^T`, it is behaving like Bombieri's boundary-escape sequence and should not be mistaken for a convergent RH counterexample candidate;
- if a negative/c near-zero mode has bounded source logarithmic energy and stable endpoint profile, compactness makes it materially more interesting, after which one still needs a cutoff/tail certificate and direct arithmetic Weil evaluation.

This supplies a second certification axis complementary to Groskin's archimedean tail budget: tail certification controls the `T -> infinity` approximation at fixed Galerkin dimension, while source compactness controls possible escape as `N -> infinity`.
