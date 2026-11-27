# User guide

English | [日本語](guide.ja.md)

How to describe score distributions, equate them and read the results with flexpyequate. The code
blocks on this page run top to bottom as one script. For the arguments of each function see the
[API reference](reference.md).

1. [Setup and data](#1-setup-and-data)
2. [Score distributions](#2-score-distributions)
3. [Equivalent groups](#3-equivalent-groups)
4. [Reading the result](#4-reading-the-result)
5. [Single group](#5-single-group)
6. [Non-equivalent groups with an anchor test](#6-non-equivalent-groups-with-an-anchor-test)
7. [Standard errors of equating](#7-standard-errors-of-equating)
8. [Log-linear presmoothing](#8-log-linear-presmoothing)
9. [Kernel equating](#9-kernel-equating)
10. [Errors and warnings](#10-errors-and-warnings)
11. [Differences from the R packages](#11-differences-from-the-r-packages)

## 1. Setup and data

flexpyequate needs no configuration. Functions that draw random numbers take `rng` (a
`numpy.random.Generator` or an integer seed), so results can be reproduced.

The examples use simulated number-correct scores. Three data sets cover the three ways of
collecting data:

- **equivalent groups**: two random groups from one population, one takes form X and the other
  form Y;
- **single group**: the same examinees take both forms;
- **non-equivalent groups with an anchor test**: two groups that may differ in ability each take
  one form and a common anchor test.

```python
import warnings

import numpy as np

import flexpyequate as fe
from flexpyequate import errors

rng = np.random.default_rng(20261127)


def simulate_scores(ability, n_items, difficulty):
    """Number-correct scores on n_items items of the same difficulty."""
    p = 1.0 / (1.0 + np.exp(-(ability - difficulty)))
    return rng.binomial(n_items, p)


# Equivalent groups: 2000 examinees per form, 40 items each; form Y is easier.
x_scores = simulate_scores(rng.normal(0.0, 1.0, 2000), 40, 0.0)
y_scores = simulate_scores(rng.normal(0.0, 1.0, 2000), 40, -0.3)

# Single group: 1500 examinees take both forms.
ability = rng.normal(0.0, 1.0, 1500)
both_x = simulate_scores(ability, 40, 0.0)
both_y = simulate_scores(ability, 40, -0.3)

# Anchor test: population P takes form X, population Q (more able) takes form Y.
# Each form has 30 items of its own, and both groups take the same 10 anchor items.
ability_p = rng.normal(0.0, 1.0, 2000)
ability_q = rng.normal(0.3, 1.0, 1600)
x_unique = simulate_scores(ability_p, 30, 0.0)
x_anchor = simulate_scores(ability_p, 10, 0.0)
y_unique = simulate_scores(ability_q, 30, -0.2)
y_anchor = simulate_scores(ability_q, 10, 0.0)
```

## 2. Score distributions

Every equating function takes score distributions, not raw data. A score distribution is a set of
**possible scores**, equally spaced and increasing, with the frequency of each. Scores that nobody
obtained are part of it, with frequency zero.

### One score: `ScoreDistribution`

`from_scores` tabulates one score per examinee. Give the possible scores with `score_range`
(lowest and highest, `increment` apart; the increment is 1 by default) or with `scores`. Without
either, the observed range is used, which leaves out possible scores below the lowest and above
the highest observed score.

```python
x = fe.ScoreDistribution.from_scores(x_scores, score_range=(0, 40))
y = fe.ScoreDistribution.from_scores(y_scores, score_range=(0, 40))
print(x)
# ScoreDistribution(scores=0..40 by 1, n=2000, mean=19.8150, sd=8.8167)
```

`from_frequencies` takes a frequency table. Scores need not be integers, as long as they are
equally spaced.

```python
half_points = fe.ScoreDistribution.from_frequencies(
    scores=[0.0, 0.5, 1.0, 1.5, 2.0], frequencies=[3, 8, 12, 9, 4]
)
half_points.increment  # 0.5
```

Missing values are not allowed; drop them before building a distribution.

A distribution knows its moments, its percentile ranks and its percentiles.

```python
x.n_scores, x.n  # number of possible scores, sample size
x.mean, x.sd(), x.variance()  # population forms (divisor N)
x.sd(ddof=1)  # sample form (divisor N - 1)
x.skewness, x.kurtosis  # kurtosis is 3 for a normal distribution
x.probabilities, x.cumulative  # relative and cumulative relative frequencies

x.percentile_rank([20, 20.5])  # 0-100, also between possible scores
x.percentile([25, 50, 75])  # the inverse: scores at given percentile ranks
x.to_frame().head()  # score, frequency, probability, cumulative, percentile_rank
```

The percentile rank follows Kolen & Brennan (2014): a possible score $x_j$ stands for the interval
$[x_j - \delta/2,\ x_j + \delta/2)$, where $\delta$ is the score increment, and examinees are
taken to be spread evenly over it. At a possible score the percentile rank is therefore the
percentage below the score plus half the percentage at it. `percentile` is the inverse; where zero
frequencies make the cumulative distribution flat, it returns the middle of the flat stretch (the
mean of the upper and lower percentiles of Kolen & Brennan).

### Two scores: `BivariateScoreDistribution`

When the same examinees have two scores, their joint distribution is a
`BivariateScoreDistribution`. It is used for a single group (form X and form Y) and for an anchor
test (a form and the anchor).

```python
xy = fe.BivariateScoreDistribution.from_scores(both_x, both_y, x_range=(0, 40), y_range=(0, 40))
print(xy)
# BivariateScoreDistribution(x=0..40, y=0..40, n=1500, correlation=0.8832)

xy.x, xy.y  # the two marginal ScoreDistribution objects
xy.correlation, xy.covariance()
xy.frequencies.shape  # (41, 41): rows are X scores, columns are Y scores
xy.to_frame().head()  # long form: x_score, y_score, frequency, probability
```

For an anchor test, the form is the first variable and the **anchor is the second variable**.

```python
# External anchor: the anchor items do not count towards the form score.
xa = fe.BivariateScoreDistribution.from_scores(x_unique, x_anchor, x_range=(0, 30), y_range=(0, 10))
ya = fe.BivariateScoreDistribution.from_scores(y_unique, y_anchor, x_range=(0, 30), y_range=(0, 10))

# Internal anchor: the anchor items count towards the total score.
xa_internal = fe.BivariateScoreDistribution.from_scores(
    x_unique + x_anchor, x_anchor, x_range=(0, 40), y_range=(0, 10)
)
ya_internal = fe.BivariateScoreDistribution.from_scores(
    y_unique + y_anchor, y_anchor, x_range=(0, 40), y_range=(0, 10)
)
```

`BivariateScoreDistribution.from_frequencies(x_scores=..., y_scores=..., frequencies=...)` takes a
two-way table instead.

## 3. Equivalent groups

`equate(x, y, method=...)` equates form X to the scale of form Y. The design follows from what you
pass: two `ScoreDistribution` objects mean equivalent groups.

| `method` | Equating function |
|---|---|
| `"identity"` | $e_Y(x) = x$ |
| `"mean"` | $e_Y(x) = x - \mu_X + \mu_Y$ |
| `"linear"` | $e_Y(x) = \dfrac{\sigma_Y}{\sigma_X}(x - \mu_X) + \mu_Y$ |
| `"equipercentile"` (default) | $e_Y(x) = Q^{-1}(P(x))$ |

Here $\mu$ and $\sigma$ are means and standard deviations, $P$ is the percentile-rank function of
form X and $Q^{-1}$ the percentile function of form Y (section 2).

```python
mean = fe.equate(x, y, method="mean")
linear = fe.equate(x, y, method="linear")
equipercentile = fe.equate(x, y, method="equipercentile")

print(linear)
# EquatingResult(method='linear', design='equivalent_groups', slope=0.985374, intercept=2.888805, n_scores=41)
mean.slope, mean.intercept  # slope 1; the intercept is the difference of the means
```

Linear equating uses population standard deviations (divisor $N$) by default, as Kolen & Brennan
do. `ddof=1` uses the sample form (divisor $N - 1$), as R `equate` does.

```python
linear_sample = fe.equate(x, y, method="linear", ddof=1)
```

## 4. Reading the result

`equate()` returns an `EquatingResult`.

```python
equipercentile.table.head()  # conversion table: score (form X) and equated (form-Y equivalent)
equipercentile.scores, equipercentile.equated  # the same two columns as arrays

# Equate any form-X score, also between possible scores.
equipercentile.transform([19.5, 20.0])

# Mean, sd, skewness and kurtosis of X, of Y and of the equated X scores.
print(equipercentile.moments)
#               mean        sd  skewness  kurtosis
# x        19.815000  8.816676 -0.031222  2.182716
# y        22.414000  8.687727 -0.165331  2.257228
# equated  22.413024  8.682557 -0.164098  2.253566
```

After a successful equating the `equated` row of `moments` is close to the `y` row: the equated
form-X scores are distributed like form-Y scores. Mean equating matches the mean only, linear
equating the mean and the standard deviation, equipercentile equating the whole distribution as
far as the discreteness of the scores allows.

Other attributes say how the result was obtained.

| Attribute | Contents |
|---|---|
| `method`, `design` | The method, and `"equivalent_groups"`, `"single_group"` or `"nonequivalent_groups"` |
| `x`, `y` | The `ScoreDistribution` objects that were equated |
| `slope`, `intercept` | Coefficients of a linear method; `None` for the equipercentile methods |
| `ddof` | The `ddof` that was used |
| `see`, `standard_error`, `n_replications`, `bootstrap_mean` | Standard errors (section 7); `None` unless they were asked for |
| `synthetic_weight`, `anchor`, `gamma`, `synthetic_moments`, `anchor_distributions` | Anchor-test methods (section 6); `None` otherwise |

For equipercentile equating, `transform` gives a score more than half an increment below the
lowest possible form-X score the form-Y equivalent of percentile rank 0, and a score half an
increment or more above the highest one that of percentile rank 100.

## 5. Single group

Pass one `BivariateScoreDistribution` and no `y`. The two margins are equated with the same four
methods as for equivalent groups.

```python
single = fe.equate(xy, method="equipercentile")
single.design  # 'single_group'
single_linear = fe.equate(xy, method="linear")
single_linear.slope, single_linear.intercept
```

The equating function is computed from the margins exactly as for equivalent groups. The joint
distribution matters for the standard errors (section 7), because the two scores come from the
same examinees.

## 6. Non-equivalent groups with an anchor test

Pass two `BivariateScoreDistribution` objects: form X with the anchor in the population that took
form X, and form Y with the anchor in the population that took form Y. Both need the same
possible anchor scores.

| `method` | Kind | Uses `synthetic_weight` | Needs `anchor` |
|---|---|---|---|
| `"tucker"` | linear | yes | no |
| `"levine_observed"` | linear | yes | yes |
| `"levine_true"` | linear | no | yes |
| `"braun_holland"` | linear | yes | no |
| `"chained_linear"` | linear | no | no |
| `"frequency_estimation"` | equipercentile | yes | no |
| `"chained_equipercentile"` | equipercentile | no | no |

### Linear methods

The Tucker, Levine observed-score and Braun–Holland methods equate linearly in a **synthetic
population** that mixes the two populations with weights $w_1$ (the population that took form X)
and $w_2 = 1 - w_1$. By default the weights are proportional to the sample sizes; set $w_1$ with
`synthetic_weight`.

```python
tucker = fe.equate(xa, ya, method="tucker")
tucker.slope, tucker.intercept
tucker.synthetic_weight  # 2000 / (2000 + 1600)
tucker.gamma  # (gamma_1, gamma_2): regression slopes of the form score on the anchor score
print(tucker.synthetic_moments)  # mean and sd of X and Y in the synthetic population
#         mean        sd
# x  15.719047  6.693560
# y  17.697187  6.407046

# The population that took form X as the synthetic population:
tucker_p = fe.equate(xa, ya, method="tucker", synthetic_weight=1.0)
```

The Levine methods need to know whether the anchor is part of the score. Use `anchor="internal"`
when the anchor items count towards the total score (the first variable then includes them) and
`anchor="external"` when the anchor is scored separately.

```python
levine = fe.equate(xa, ya, method="levine_observed", anchor="external")
levine_internal = fe.equate(xa_internal, ya_internal, method="levine_observed", anchor="internal")
levine_true = fe.equate(xa, ya, method="levine_true", anchor="external")
```

The Braun–Holland method takes the means and standard deviations of X and Y from the
synthetic distributions of frequency estimation (below) and equates linearly. Chained linear
equating equates X to the anchor in the first population and the anchor to Y in the second; it
has no synthetic population.

```python
braun_holland = fe.equate(xa, ya, method="braun_holland")
chained_linear = fe.equate(xa, ya, method="chained_linear")
```

### Equipercentile methods

Frequency estimation (post-stratification) estimates the distributions of X and of Y in the
synthetic population, assuming that the distribution of each form given the anchor score is the
same in both populations, and equates them by the equipercentile method. Chained equipercentile
equating equates X to the anchor in the first population and the anchor to Y in the second.

```python
frequency_estimation = fe.equate(xa, ya, method="frequency_estimation")
frequency_estimation.x  # distribution of X in the synthetic population
frequency_estimation.synthetic_moments

chained = fe.equate(xa, ya, method="chained_equipercentile")
chained.anchor_distributions  # the anchor in the two populations
```

For frequency estimation, `x` and `y` of the result are the synthetic distributions (their total
frequency is $N_1 + N_2$). For every other anchor-test method they are form X in the population
that took it and form Y in the population that took it.

Frequency estimation and the Braun–Holland method need every anchor score in both populations.
If an anchor score was observed in one population only, that part of the other population is left
out and a `SparseDataWarning` is issued. Presmoothing the joint distributions (section 8) avoids
this, and is the usual practice with the equipercentile methods anyway.

## 7. Standard errors of equating

`standard_error=` adds the standard error of equating at each possible score of form X. It
appears as the column `see` of `table` and as the attribute `see`.

```python
linear_se = fe.equate(x, y, method="linear", standard_error="analytic")
linear_se.table.head()  # score, equated, see
linear_se.see  # the same as an array
```

There are three options.

- `"analytic"`: the delta method without a distributional assumption. For linear methods it uses
  the third and fourth moments of the observed distributions; for equipercentile equating of
  equivalent groups it is the formula of Lord (1982).
- `"analytic_normal"`: the delta method assuming (bivariate) normal scores. It exists for the
  methods that depend on means, variances and covariances only.
- `"bootstrap"`: resamples the examinees of each sample with replacement, equates every
  bootstrap sample and takes the standard deviation of the equated scores. It works for every
  method, and needs `rng`.

| Method (design) | `"analytic"` | `"analytic_normal"` | `"bootstrap"` |
|---|---|---|---|
| identity | 0 | 0 | 0 |
| mean, linear (equivalent groups) | yes | yes | yes |
| mean, linear (single group) | yes | yes | yes |
| equipercentile (equivalent groups) | yes (Lord) | no | yes |
| equipercentile (single group) | no | no | yes |
| tucker, levine_observed, levine_true | yes | yes | yes |
| chained_linear | yes | yes | yes |
| braun_holland | yes | no | yes |
| frequency_estimation | no | no | yes |
| chained_equipercentile | no | no | yes |

Asking for a combination marked "no" raises `SpecificationError`.

```python
normal_se = fe.equate(x, y, method="linear", standard_error="analytic_normal")
lord_se = fe.equate(x, y, method="equipercentile", standard_error="analytic")
tucker_se = fe.equate(xa, ya, method="tucker", standard_error="analytic")
single_se = fe.equate(xy, method="linear", standard_error="analytic")
```

The bootstrap takes `n_replications` (default 1000) and `rng`. The examples use fewer
replications to stay quick.

```python
boot = fe.equate(
    x, y, method="equipercentile", standard_error="bootstrap", n_replications=200, rng=1
)
boot.see  # bootstrap standard errors
boot.n_replications  # number of bootstrap samples the standard errors are based on
boot.bootstrap_mean - boot.equated  # estimate of the bias of the equating function

chained_boot = fe.equate(
    xa,
    ya,
    method="chained_equipercentile",
    standard_error="bootstrap",
    n_replications=200,
    rng=np.random.default_rng(2),
)
```

For a joint distribution the bootstrap resamples examinees (pairs of scores), so the dependence
between the two scores is kept. Bootstrap samples that cannot be equated (for example a score
without variance) are left out with a `SparseDataWarning`; `n_replications` of the result is the
number actually used.

All three options treat the frequencies as observed. If you pass a presmoothed distribution to
`equate()`, the standard errors ignore that a model was fitted, and take the total frequency as
the sample size. Kernel equating (section 9) has standard errors that account for presmoothing.

## 8. Log-linear presmoothing

`presmooth()` fits a polynomial log-linear model to a distribution (Holland & Thayer, 2000) and
returns the fitted, smooth distribution. For one score with frequencies $n_j$ and fitted
frequencies $m_j$ the model is

$$
\log m_j = \beta_0 + \sum_{i=1}^{C} \beta_i\, x_j^{\,i} .
$$

The fitted distribution has the same total and the same first $C$ moments as the observed one.
`degree` is $C$ (default 6).

```python
smooth_x = fe.presmooth(x, degree=6)
smooth_y = fe.presmooth(y, degree=6)

smooth_x.distribution  # the smoothed ScoreDistribution
smooth_x.observed  # the distribution that was smoothed
smooth_x.terms  # ('x^1', 'x^2', 'x^3', 'x^4', 'x^5', 'x^6')
smooth_x.converged, smooth_x.n_iterations
print(smooth_x.fit_statistics)
# likelihood_ratio       45.554860
# pearson                45.597152
# freeman_tukey          44.287608
# degrees_of_freedom     34.000000
# n_parameters            7.000000
# log_likelihood       -133.625372
# aic                   281.250744
# dtype: float64
```

`fit_statistics` holds the likelihood-ratio, Pearson and Freeman–Tukey chi-squares with their
degrees of freedom, and the AIC. A common way to choose the degree is to compare the AIC of
several models.

```python
aic = {degree: fe.presmooth(x, degree=degree).fit_statistics["aic"] for degree in range(2, 8)}
best_degree = min(aic, key=aic.get)  # 6 for these data
```

The smoothed distribution is a `ScoreDistribution` and can be passed to `equate()`.

```python
smoothed_equipercentile = fe.equate(
    smooth_x.distribution, smooth_y.distribution, method="equipercentile"
)
```

### Joint distributions

For a `BivariateScoreDistribution`, `degree` is a pair $(C_X, C_Y)$ (default `(6, 6)`) and
`cross_terms` lists the powers $(a, b)$ of the cross terms $x^a y^b$ (default `[(1, 1)]`):

$$
\log m_{jk} = \beta_0 + \sum_{i=1}^{C_X} \beta_{Xi}\, x_j^{\,i}
              + \sum_{i=1}^{C_Y} \beta_{Yi}\, y_k^{\,i}
              + \sum_{(a, b)} \beta_{ab}\, x_j^{\,a} y_k^{\,b} .
$$

The model preserves the first $C_X$ and $C_Y$ moments of the two margins and the cross moments
$E[X^a Y^b]$ of the cross terms; with the term $(1, 1)$, the correlation. An empty `cross_terms`
makes the two scores independent.

```python
xa_fit = fe.presmooth(xa, degree=(4, 3), cross_terms=[(1, 1)])
ya_fit = fe.presmooth(ya, degree=(4, 3), cross_terms=[(1, 1)])
xa_fit.terms  # ('x^1', 'x^2', 'x^3', 'x^4', 'y^1', 'y^2', 'y^3', 'x^1*y^1')
xy_fit = fe.presmooth(xy, degree=(4, 4))

# Frequency estimation and chained equating with presmoothed joint distributions:
smoothed_fe = fe.equate(xa_fit.distribution, ya_fit.distribution, method="frequency_estimation")
smoothed_chained = fe.equate(
    xa_fit.distribution, ya_fit.distribution, method="chained_equipercentile"
)
```

A degree that the number of possible scores cannot support raises `SpecificationError`. If the
fit does not converge within `max_iterations` (default 100), a `ConvergenceWarning` is issued and
`converged` is `False`.

## 9. Kernel equating

`kernel_equate()` implements the kernel method of von Davier, Holland & Thayer (2004). Each
discrete distribution is made continuous with a kernel of bandwidth $h$, in a way that keeps its
mean and variance, and form X is equated to form Y through the two continuous distribution
functions:

$$
e_Y(x) = G_{h_Y}^{-1}\bigl(F_{h_X}(x)\bigr) .
$$

Pass the results of `presmooth()` (the `LoglinearResult` objects, not their `.distribution`), so
that the standard errors account for the fitted models. Plain distributions are also accepted and
are used as observed.

```python
kernel = fe.kernel_equate(smooth_x, smooth_y)
print(kernel)
# KernelEquatingResult(design='equivalent_groups', kernel='gaussian', bandwidth_x=0.6253, bandwidth_y=0.6174, n_scores=41)

kernel.table.head()  # score, equated, see (standard error of equating)
kernel.bandwidth_x, kernel.bandwidth_y
kernel.transform([19.5, 20.0])
kernel.x_presmoothed, kernel.y_presmoothed  # True, True

unsmoothed = fe.kernel_equate(x, y)  # observed distributions
```

Unlike `equate()`, `kernel_equate()` always returns standard errors (`see`).

### Bandwidths

By default each bandwidth minimizes the penalty of von Davier et al. (2004), which has two terms:
the first keeps the continuous density close to the score probabilities at the possible scores,
the second (with weight `penalty_weight`, default 1) counts the scores around which the density is
U-shaped. `penalty_weight=0` drops the second term. `penalty_bandwidth()` computes the bandwidth
of one distribution on its own.

```python
fe.penalty_bandwidth(smooth_x)  # the same value as kernel.bandwidth_x
first_term_only = fe.kernel_equate(smooth_x, smooth_y, penalty_weight=0.0)

# Give the bandwidths yourself:
fixed = fe.kernel_equate(smooth_x, smooth_y, bandwidth_x=1.0, bandwidth_y=1.0)
```

`bandwidth_method` chooses another rule for the bandwidths that are not given.

| `bandwidth_method` | Rule | Kernels |
|---|---|---|
| `"penalty"` (default) | Minimizes the penalty above | all |
| `"rule_of_thumb"` | $h = 9\sigma / \sqrt{100 N^{2/5} - 81}$ (Andersson & von Davier, 2014) | Gaussian |
| `"double_smoothing"` | Minimizes the double-smoothing criterion of Häggström & Wiberg (2014) | Gaussian |
| `"cross_validation"` | Minimizes the leave-one-out criterion of R `kequate` | Gaussian |

```python
rule = fe.kernel_equate(smooth_x, smooth_y, bandwidth_method="rule_of_thumb")
double = fe.kernel_equate(smooth_x, smooth_y, bandwidth_method="double_smoothing")
cross = fe.kernel_equate(smooth_x, smooth_y, bandwidth_method="cross_validation")
rule.bandwidth_x, double.bandwidth_x, cross.bandwidth_x
```

The rule of thumb is not available for the counterbalanced design. The standard errors treat the
selected bandwidths as fixed, whatever the rule.

### Kernels

`kernel` is `"gaussian"` (default), `"logistic"` (standard logistic) or `"uniform"` (uniform on
$(-1/2, 1/2)$), following Lee & von Davier (2011).

```python
logistic = fe.kernel_equate(smooth_x, smooth_y, kernel="logistic")
uniform = fe.kernel_equate(smooth_x, smooth_y, kernel="uniform")
```

With the uniform kernel the continuous density is zero outside its support and, for a bandwidth
below the score increment, between the possible scores. Where the density of form Y is zero at an
equated score, `see` is `nan`.

### Linear equating and the difference between two functions

`linear=True` uses very large bandwidths (1000 standard deviations), which gives the linear
equating function of the design together with its standard error. It cannot be combined with
explicit bandwidths or with the uniform kernel.

`seed()` compares two equating functions computed **from the same inputs**: it returns their
difference and the standard error of the difference (SEED). A difference that is small relative to
its standard error says that the simpler function would do.

```python
kernel_linear = fe.kernel_equate(smooth_x, smooth_y, linear=True)
kernel.seed(kernel_linear).head()  # score, difference (kernel minus linear), seed
```

### Diagnostics

`percent_relative_error` compares the first ten moments of the equated scores with those of
form Y, in percent. `continuized` gives the continuous distribution function and density at the
possible scores of each form.

```python
kernel.percent_relative_error  # indexed by the moment order 1..10
kernel.continuized.head()  # form, score, probability, cdf, density
```

### Other designs

`kernel_equate()` covers five designs. With two univariate inputs the design is equivalent groups
and with one joint distribution it is a single group. With two joint distributions the design
must be named.

| `design` | Inputs |
|---|---|
| `"equivalent_groups"` | `x`: form X, `y`: form Y, from two independent samples |
| `"single_group"` | `x`: joint distribution of (X, Y) in one sample |
| `"counterbalanced"` | `x`: joint distribution of (X, Y) in the sample that took X first; `y`: the same in the sample that took Y first |
| `"chained"` | `x`: joint distribution of (X, anchor); `y`: joint distribution of (Y, anchor) |
| `"post_stratification"` | The same inputs as `"chained"` |

```python
single_kernel = fe.kernel_equate(xy_fit)  # single group

chained_kernel = fe.kernel_equate(xa_fit, ya_fit, design="chained")
post_kernel = fe.kernel_equate(xa_fit, ya_fit, design="post_stratification")
post_kernel.synthetic_weight  # weight of the population that took X; set it with synthetic_weight=

chained_kernel.anchor_distributions  # the anchor in the two populations
chained_kernel.anchor_bandwidths  # their bandwidths; set them with anchor_bandwidths=
chained_kernel.chain_percent_relative_error.head()  # columns x_to_anchor, anchor_to_y

# Chained against post-stratification equating, and kernel against linear:
chained_kernel.seed(post_kernel).head()
post_linear = fe.kernel_equate(xa_fit, ya_fit, design="post_stratification", linear=True)
post_kernel.seed(post_linear).head()
```

Chained equating has two links (X to the anchor, the anchor to Y), so its percent relative error
is `chain_percent_relative_error`; `percent_relative_error` raises `SpecificationError` for it.
Post-stratification needs every observed anchor score in both populations, which presmoothed
joint distributions provide; otherwise it raises `SpecificationError`.

In the counterbalanced design each sample takes both forms, in opposite orders. The score
probabilities of X and Y are weighted means over the two samples;
`counterbalance_weights=(w_X, w_Y)` gives the weights of the sample that took X first (default
`(0.5, 0.5)`).

```python
ability_1 = rng.normal(0.0, 1.0, 1000)
ability_2 = rng.normal(0.0, 1.0, 1000)
x_first = fe.BivariateScoreDistribution.from_scores(
    simulate_scores(ability_1, 40, 0.0),
    simulate_scores(ability_1, 40, -0.3),
    x_range=(0, 40),
    y_range=(0, 40),
)
y_first = fe.BivariateScoreDistribution.from_scores(
    simulate_scores(ability_2, 40, 0.0),
    simulate_scores(ability_2, 40, -0.3),
    x_range=(0, 40),
    y_range=(0, 40),
)
x_first_fit = fe.presmooth(x_first, degree=(4, 4))
y_first_fit = fe.presmooth(y_first, degree=(4, 4))

counterbalanced = fe.kernel_equate(x_first_fit, y_first_fit, design="counterbalanced")
# Use each form only from the sample that took it first:
first_only = fe.kernel_equate(
    x_first_fit, y_first_fit, design="counterbalanced", counterbalance_weights=(1.0, 0.0)
)
```

## 10. Errors and warnings

The exception and warning classes are in `flexpyequate.errors`.

| Class | Raised or issued when |
|---|---|
| `ScoreDistributionError` | Scores or frequencies do not form a valid distribution: scores not equally spaced, a negative frequency, an observed score that is not a possible score, no observation |
| `SpecificationError` | The arguments do not fit each other or the data: a method that does not belong to the design, an unknown option, a missing `anchor` or `rng`, a degree that is too high, an analytic standard error that does not exist |
| `SparseDataWarning` | Part of a computation was done on what is available: an anchor score observed in one population only, or bootstrap samples that could not be equated |
| `ConvergenceWarning` | Presmoothing stopped before it converged |

All errors derive from `FlexpyequateError` and all warnings from `FlexpyequateWarning`. The two
error classes are also `ValueError`s.

```python
try:
    fe.ScoreDistribution.from_frequencies(scores=[0, 1, 3], frequencies=[1, 2, 3])
except errors.ScoreDistributionError as error:
    print(error)
# scores must be equally spaced.

try:
    fe.equate(xy, method="equipercentile", standard_error="analytic")
except errors.SpecificationError as error:
    print(error)
# standard_error="analytic" is not available for method='equipercentile' with single group: Lord's (1982) formula assumes two independent samples. Use standard_error="bootstrap".
```

A small example of the sparse-data warning: nobody in the second population scored 0 on the
anchor.

```python
sparse_x = fe.BivariateScoreDistribution.from_frequencies(
    x_scores=range(3), y_scores=range(3), frequencies=[[2, 1, 0], [1, 3, 1], [0, 1, 2]]
)
sparse_y = fe.BivariateScoreDistribution.from_frequencies(
    x_scores=range(3), y_scores=range(3), frequencies=[[0, 2, 0], [0, 3, 2], [0, 1, 3]]
)
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    fe.equate(sparse_x, sparse_y, method="frequency_estimation")
print(caught[0].category.__name__)
# SparseDataWarning
```

## 11. Differences from the R packages

flexpyequate is checked against R `equate`, `kequate` and `SNSequate`, but it follows the
published formulas where the packages differ from them. To reproduce the R results:

- **Variances.** R `equate` divides variances by $N - 1$; flexpyequate uses the population form of
  Kolen & Brennan by default. Pass `ddof=1` to reproduce `equate`'s linear equating.
- **Mean equating.** R `equate`'s `type = "mean"` multiplies scores by the ratio of the two score
  ranges; flexpyequate's mean equating always has slope 1. The two agree for forms with the same
  score range.
- **Percentile rank 0 or 100.** Where a form-X score has percentile rank exactly 0 or 100,
  flexpyequate returns the mean of the upper and lower percentiles of form Y, as defined by
  Kolen & Brennan; `equate` returns the end of the form-Y range. The two differ only when nobody
  obtained the lowest (or highest) form-Y scores.
- **Synthetic weights.** For the Braun–Holland and frequency-estimation methods, R `equate` mixes
  the two groups as counts, which changes the weight of the first group from $w$ to
  $wN_1 / (wN_1 + (1 - w)N_2)$ when the sample sizes differ. flexpyequate uses $w$ itself; pass
  that effective weight as `synthetic_weight` to reproduce `equate`.
- **Variance in the kernel.** R `kequate` multiplies the variance used to make the distribution
  continuous by $N / (N - 1)$; flexpyequate uses the variance of the score distribution itself,
  as von Davier, Holland & Thayer (2004) and `SNSequate` do. The difference in equated scores
  shrinks with the sample size.
- **Counterbalanced design.** R `kequate` has a single weight, and its standard errors are
  consistent with its equating function only when that weight is 1/2. flexpyequate has two
  weights (`counterbalance_weights`) and its standard errors hold for any of them.
- **Penalty.** `kernel_equate()` selects bandwidths with both penalty terms
  (`penalty_weight=1`); `kequate` uses the first term only by default (`penalty_weight=0`
  reproduces it).

## References

- Andersson, B., & von Davier, A. A. (2014). Improving the bandwidth selection in kernel
  equating. *Journal of Educational Measurement, 51*, 223–238.
- Häggström, J., & Wiberg, M. (2014). Optimal bandwidth selection in observed-score kernel
  equating. *Journal of Educational Measurement, 51*, 201–211.
- Holland, P. W., & Thayer, D. T. (2000). Univariate and bivariate loglinear models for discrete
  test score distributions. *Journal of Educational and Behavioral Statistics, 25*, 133–183.
- Kolen, M. J., & Brennan, R. L. (2014). *Test equating, scaling, and linking* (3rd ed.). Springer.
- Lee, Y.-H., & von Davier, A. A. (2011). Equating through alternative kernels. In A. A. von
  Davier (Ed.), *Statistical models for test equating, scaling, and linking* (pp. 159–173).
  Springer.
- Lord, F. M. (1982). The standard error of equipercentile equating. *Journal of Educational
  Statistics, 7*, 165–174.
- von Davier, A. A., Holland, P. W., & Thayer, D. T. (2004). *The kernel method of test equating*.
  Springer.
