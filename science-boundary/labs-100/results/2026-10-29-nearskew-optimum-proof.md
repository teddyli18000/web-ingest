# 2026-10-29 exact optimum of the N=100 near-skew manifold

## Result

The full canonical N=100 near-skew manifold has exact minimum LABS energy

```text
E_min = 578.
```

This is a proof, not a heuristic search result. It eliminates the entire `(+1, skew99)` manifold from any Few Shots improvement below 578.

The public N=100 incumbent attains 578, so the lower bound below is tight.

## Setup

Let

```text
s = (s_0, s_1, ..., s_99),  s_i in {+1,-1},
```

be canonical near-skew, meaning positions 1 through 99 form a length-99 skew-symmetric tail. In zero-based full-sequence coordinates,

```text
s_p s_{100-p} = (-1)^p,  p=1,...,49.
```

Define

```text
t = (s_1, ..., s_99)       # length 99
u = (s_0, ..., s_99, s_0)  # length 101.
```

The tail `t` is skew-symmetric by definition. The appended sequence `u` is also skew-symmetric: the new symmetric endpoint pair agrees, and every interior reflected pair inherits the near-skew relation with the correct alternating sign.

## Correlation identity

For `k=1,...,99`, write

```text
x_k = s_0 s_k = +/-1.
```

Removing the first term of the N=100 correlation gives

```text
C_k(s) = C_k(t) + x_k.
```

Appending `s_0` on the right adds one final product. The near-skew reflection gives that final product as `(-1)^k x_k`, hence

```text
C_k(u) = C_k(s) + (-1)^k x_k
       = C_k(t) + (1+(-1)^k) x_k.
```

Because `t` is skew-symmetric of odd length, every odd-lag autocorrelation of `t` is zero.

### Odd k

For every odd `k` in `1,3,...,99`,

```text
C_k(t) = 0,
C_k(s) = x_k,
C_k(u) = 0.
```

Thus each of the 50 odd lags contributes exactly `1` to `E(s)` and zero to `E(t)+E(u)`.

### Even k

For every even `k` in `2,4,...,98`, set

```text
c = C_k(t),  x = x_k.
```

Then

```text
C_k(s) = c+x,
C_k(u) = c+2x.
```

Since `x^2=1`,

```text
C_k(t)^2 + C_k(u)^2
  = c^2 + (c+2x)^2
  = 2(c+x)^2 + 2
  = 2 C_k(s)^2 + 2.
```

There are 49 even lags.

Finally, the length-101 sequence has the extra lag `k=100`, with

```text
C_100(u)^2 = (s_0 s_0)^2 = 1.
```

Summing all lags gives the exact identity

```text
E(t) + E(u) = 2 E(s) - 1.
```

Equivalently,

```text
E(s) = (E(t)+E(u)+1)/2.
```

## Imported exact skew-LABS bounds

Packebusch and Mertens exhaustively computed all optimal skew-symmetric LABS sequences through odd length 119. Their exact table gives

```text
N=99:  minimum skew energy = 577
N=101: minimum skew energy = 578.
```

Therefore every canonical N=100 near-skew `s` satisfies

```text
2 E(s) - 1
  = E(t)+E(u)
 >= 577+578
  = 1155,
```

so

```text
E(s) >= 578.
```

The public N=100 incumbent has energy 578, hence the bound is attained and the exact near-skew optimum is 578.

## Scope

This result proves optimality only for the N=100 near-skew manifold (and all its standard LABS symmetry images). It does **not** prove the unrestricted N=100 optimum is 578.

In particular, an unrestricted breakthrough below 578 must leave every near-skew symmetry orientation. The next frontier is therefore the low-energy non-near-skew space, beginning with:

1. odd-perfect sequences (`odd energy = 50`) outside the near-skew orbit;
2. the first odd-defect layer (`odd energy = 58`);
3. unrestricted representations that can cross between those structural components.

All near-skew CP-SAT, branch-and-bound, local-shell, block-descent, and crossover computations remain useful historical evidence, but they are no longer needed to establish the target exclusion: the identity plus the published exact skew optima settles the entire manifold.

## Independent checks

The identity was checked numerically on randomly generated skew-99 tails before being promoted to this proof. The proof itself is algebraic and does not depend on those numerical checks.

The incumbent also realizes the equality case: deleting its first sign gives the historical N=99 skew optimum with energy 577, while appending its first sign gives the N=101 skew optimum with energy 578, so

```text
577 + 578 = 2*578 - 1.
```

## Source

Tom Packebusch and Stephan Mertens, *Low Autocorrelation Binary Sequences*, Journal of Physics A 49 (2016), arXiv:1512.02475. The paper states that all optimal skew-symmetric sequences were computed through `N=119`; Table 3 lists exact skew energies `577` at `N=99` and `578` at `N=101`.

<https://arxiv.org/abs/1512.02475>
