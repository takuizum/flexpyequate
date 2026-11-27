# API reference

English | [日本語](reference.ja.md)

The public API of flexpyequate: everything importable with `from flexpyequate import ...`. For
the workflow see the [user guide](guide.md). The docstrings carry the same information plus the
formulas and their sources (`help(flexpyequate.equate)` and so on).

Apart from the first one or two, arguments of public functions are keyword-only (after `*`).
Arrays returned by the library are `numpy.ndarray` of `float64`; the arrays held by distributions
and results are read-only.

- Score distributions: [`ScoreDistribution`](#scoredistribution), [`BivariateScoreDistribution`](#bivariatescoredistribution)
- Equating: [`equate`](#equate), [`EquatingResult`](#equatingresult)
- Presmoothing: [`presmooth`](#presmooth), [`LoglinearResult`](#loglinearresult)
- Kernel equating: [`kernel_equate`](#kernel_equate), [`KernelEquatingResult`](#kernelequatingresult), [`penalty_bandwidth`](#penalty_bandwidth)
- Exceptions and warnings: [`flexpyequate.errors`](#flexpyequateerrors)
- Version: [`__version__`](#__version__)

---

## Score distributions

### `ScoreDistribution`

```text
ScoreDistribution(scores, frequencies)
ScoreDistribution.from_frequencies(*, scores, frequencies) -> ScoreDistribution
ScoreDistribution.from_scores(values, *, scores=None, score_range=None, increment=1.0) -> ScoreDistribution
```

Frequencies of the possible scores of one test form. The percentile-rank and percentile functions
follow Kolen & Brennan (2014, ch. 2).

| Argument | Type | Description |
|---|---|---|
| `scores` | array of shape `(n_scores,)` | Possible scores: at least two, strictly increasing and equally spaced. Scores nobody obtained are included with frequency zero |
| `frequencies` | array of shape `(n_scores,)` | Non-negative frequency of each possible score. Non-integer values are allowed (presmoothed distributions) |

**`from_frequencies`** builds a distribution from a frequency table (`scores` may be any
iterable, for example `range(41)`).

**`from_scores`** tabulates one observed score per examinee.

| Argument | Type | Description |
|---|---|---|
| `values` | array of shape `(n_examinees,)` | Observed scores. Missing values are not allowed; drop them first |
| `scores` | array, optional | The possible scores. Give this or `score_range`, not both |
| `score_range` | `(low, high)`, optional | Lowest and highest possible score; the possible scores are `increment` apart. If neither `scores` nor `score_range` is given, the observed range is used |
| `increment` | float, default `1.0` | Distance between possible scores when `scores` is not given |

**Raises**: `ScoreDistributionError` if the scores are not equally spaced and increasing, a
frequency is negative or not finite, all frequencies are zero, the score range is not a multiple
of the increment, or (`from_scores`) an observed score is not one of the possible scores.

| Attribute | Type | Description |
|---|---|---|
| `scores` | array | Possible scores |
| `frequencies` | array | Frequency of each possible score |
| `n_scores` | int | Number of possible scores |
| `increment` | float | Distance $\delta$ between adjacent possible scores |
| `n` | float | Total frequency (sample size) |
| `probabilities` | array | Relative frequency of each possible score |
| `cumulative` | array | Cumulative proportion $F(x_j)$ at each possible score |
| `mean` | float | Mean |
| `skewness` | float | Skewness (population form) |
| `kurtosis` | float | Kurtosis (population form; 3 for a normal distribution) |

| Method | Returns | Description |
|---|---|---|
| `variance(*, ddof=0)` | float | Variance. `ddof=0`: population form (divisor $N$), as Kolen & Brennan; `ddof=1`: sample form (divisor $N - 1$), as R `equate`. Other values raise `ScoreDistributionError` |
| `sd(*, ddof=0)` | float | Standard deviation, the square root of `variance` |
| `percentile_rank(values)` | array | Percentile rank (0–100) of scores, also between possible scores |
| `percentile(ranks)` | array | Score at given percentile ranks (0–100), the inverse of `percentile_rank`. Raises `ScoreDistributionError` for ranks outside 0–100 |
| `to_frame()` | `pandas.DataFrame` | One row per possible score: `score`, `frequency`, `probability`, `cumulative`, `percentile_rank` |

A possible score $x_j$ is treated as uniform on $[x_j - \delta/2,\ x_j + \delta/2)$. With $x^*$
the possible score nearest to $x$,

$$
P(x) = 100\Bigl\{F(x^* - \delta) + \frac{x - (x^* - \delta/2)}{\delta}
       \bigl[F(x^*) - F(x^* - \delta)\bigr]\Bigr\},
$$

which is 0 below $x_1 - \delta/2$ and 100 from $x_J + \delta/2$ on. `percentile` returns the mean
of the upper and lower percentiles of Kolen & Brennan; the two differ only where zero frequencies
make $F$ flat. Its values lie between $x_1 - \delta/2$ and $x_J + \delta/2$.

**Checked against**: R `equate` (percentile ranks: `equate::px`).

### `BivariateScoreDistribution`

```text
BivariateScoreDistribution(x_scores, y_scores, frequencies)
BivariateScoreDistribution.from_frequencies(*, x_scores, y_scores, frequencies) -> BivariateScoreDistribution
BivariateScoreDistribution.from_scores(x_values, y_values, *, x_scores=None, y_scores=None,
    x_range=None, y_range=None, x_increment=1.0, y_increment=1.0) -> BivariateScoreDistribution
```

Joint frequencies of two scores obtained by the same examinees: forms X and Y in a single group,
or a form (first variable) and the anchor (second variable) in an anchor-test design.

| Argument | Type | Description |
|---|---|---|
| `x_scores` | array of shape `(n_x_scores,)` | Possible scores of the first variable, equally spaced and increasing |
| `y_scores` | array of shape `(n_y_scores,)` | Possible scores of the second variable |
| `frequencies` | array of shape `(n_x_scores, n_y_scores)` | Non-negative joint frequencies; rows are scores of the first variable, columns of the second |

**`from_frequencies`** builds a joint distribution from a two-way frequency table.

**`from_scores`** cross-tabulates paired observed scores (one pair per examinee).

| Argument | Type | Description |
|---|---|---|
| `x_values`, `y_values` | arrays of shape `(n_examinees,)` | Observed scores on the two variables, in the same examinee order |
| `x_scores`, `y_scores` | arrays, optional | The possible scores of each variable |
| `x_range`, `y_range` | `(low, high)`, optional | Lowest and highest possible score of each variable, used when the possible scores are not given. Without either, the observed range is used |
| `x_increment`, `y_increment` | float, default `1.0` | Distance between possible scores when they are not given explicitly |

**Raises**: `ScoreDistributionError` if the scores or frequencies are invalid, all frequencies are
zero, the two arrays of `from_scores` differ in length, or an observed score is not one of the
possible scores.

| Attribute | Type | Description |
|---|---|---|
| `x_scores`, `y_scores` | arrays | Possible scores of the two variables |
| `frequencies` | array | Joint frequencies, shape `(n_x_scores, n_y_scores)` |
| `n` | float | Total frequency (number of examinees) |
| `probabilities` | array | Joint relative frequencies |
| `x`, `y` | `ScoreDistribution` | Marginal distributions of the first and the second variable |
| `correlation` | float | Pearson correlation between the two scores |

| Method | Returns | Description |
|---|---|---|
| `covariance(*, ddof=0)` | float | Covariance of the two scores (`ddof=0`: population form, `ddof=1`: sample form) |
| `to_frame()` | `pandas.DataFrame` | Long form, one row per score pair: `x_score`, `y_score`, `frequency`, `probability` |

---

## Equating

### `equate`

```text
equate(x, y=None, *, method="equipercentile", ddof=0, synthetic_weight=None, anchor=None,
       standard_error=None, n_replications=1000, rng=None) -> EquatingResult
```

Equate form X to the scale of form Y from their score distributions (Kolen & Brennan, 2014). The
data collection design follows from the inputs:

- two `ScoreDistribution` objects: equivalent groups;
- one `BivariateScoreDistribution`: a single group, whose two margins are equated;
- two `BivariateScoreDistribution` objects: non-equivalent groups with an anchor test. The first
  holds form X and the anchor in the population that took X, the second form Y and the anchor in
  the population that took Y; in both, the anchor is the second variable.

| Argument | Type | Description |
|---|---|---|
| `x` | `ScoreDistribution` / `BivariateScoreDistribution` | Distribution of form X (equivalent groups); the joint distribution of forms X and Y (single group); or the joint distribution of form X and the anchor (non-equivalent groups) |
| `y` | `ScoreDistribution` / `BivariateScoreDistribution`, optional | Distribution of form Y from an independent, equivalent group, or the joint distribution of form Y and the anchor in the other population. Omit it for a single group |
| `method` | str, default `"equipercentile"` | `"identity"`, `"mean"`, `"linear"` or `"equipercentile"` for equivalent groups and a single group; `"tucker"`, `"levine_observed"`, `"levine_true"`, `"braun_holland"`, `"chained_linear"`, `"frequency_estimation"` or `"chained_equipercentile"` for non-equivalent groups |
| `ddof` | `0` / `1`, default `0` | Delta degrees of freedom of the variances and covariances in the linear methods: 0 (population form, as Kolen & Brennan) or 1 (sample form, as R `equate`). The Braun–Holland method always uses the moments of the synthetic distributions |
| `synthetic_weight` | float, optional | Weight $w_1$ of the population that took form X, between 0 and 1, for the Tucker, Levine observed-score, Braun–Holland and frequency-estimation methods. Default: proportional to the sample sizes, $w_1 = N_1 / (N_1 + N_2)$. Other methods ignore it |
| `anchor` | `"internal"` / `"external"`, optional | Required by the Levine methods: `"internal"` if the anchor items count towards the total scores, `"external"` if the anchor is scored separately. Other methods ignore it |
| `standard_error` | `"analytic"` / `"analytic_normal"` / `"bootstrap"`, optional | Compute standard errors of equating at the possible scores of form X. By default none are computed |
| `n_replications` | int, default `1000` | Number of bootstrap samples (at least 2) |
| `rng` | `numpy.random.Generator` / int, optional | Random number generator or non-negative integer seed. Required for the bootstrap; ignored otherwise |

**Methods for equivalent groups and a single group**, with $P$ the percentile-rank function of X
(as a proportion) and $Q^{-1}$ the percentile function of Y:

| `method` | Equating function |
|---|---|
| `"identity"` | $e_Y(x) = x$ |
| `"mean"` | $e_Y(x) = x - \mu_X + \mu_Y$ |
| `"linear"` | $e_Y(x) = \dfrac{\sigma_Y}{\sigma_X}(x - \mu_X) + \mu_Y$ |
| `"equipercentile"` | $e_Y(x) = Q^{-1}(P(x))$ |

**Methods for non-equivalent groups with an anchor test.** Population 1 takes X and the anchor V,
population 2 takes Y and V. `"tucker"`, `"levine_observed"` and `"braun_holland"` equate linearly
in the synthetic population with weights $w_1$ and $w_2 = 1 - w_1$,

$$
l_Y(x) = \frac{\sigma_s(Y)}{\sigma_s(X)}\,[x - \mu_s(X)] + \mu_s(Y) .
$$

For the Tucker and Levine observed-score methods the synthetic moments are

$$
\begin{aligned}
\mu_s(X) &= \mu_1(X) - w_2 \gamma_1 [\mu_1(V) - \mu_2(V)] \\
\mu_s(Y) &= \mu_2(Y) + w_1 \gamma_2 [\mu_1(V) - \mu_2(V)] \\
\sigma_s^2(X) &= \sigma_1^2(X) - w_2 \gamma_1^2 [\sigma_1^2(V) - \sigma_2^2(V)]
                 + w_1 w_2 \gamma_1^2 [\mu_1(V) - \mu_2(V)]^2 \\
\sigma_s^2(Y) &= \sigma_2^2(Y) + w_1 \gamma_2^2 [\sigma_1^2(V) - \sigma_2^2(V)]
                 + w_1 w_2 \gamma_2^2 [\mu_1(V) - \mu_2(V)]^2
\end{aligned}
$$

with $\gamma_1$ as follows ($\gamma_2$ likewise from Y and V in population 2):

| Method | $\gamma_1$ |
|---|---|
| Tucker | $\sigma_1(X, V) / \sigma_1^2(V)$ |
| Levine, internal anchor | $\sigma_1^2(X) / \sigma_1(X, V)$ |
| Levine, external anchor | $[\sigma_1^2(X) + \sigma_1(X, V)] / [\sigma_1^2(V) + \sigma_1(X, V)]$ |

The Braun–Holland method takes the synthetic means and standard deviations from the
frequency-estimation distributions $f_s(x) = w_1 f_1(x) + w_2 \sum_v f_1(x \mid v) h_2(v)$ and
$g_s(y) = w_1 \sum_v g_2(y \mid v) h_1(v) + w_2 g_2(y)$. The other methods:

| `method` | Equating function |
|---|---|
| `"levine_true"` | $l_Y(x) = \dfrac{\gamma_2}{\gamma_1}[x - \mu_1(X)] + \mu_2(Y) + \gamma_2 [\mu_1(V) - \mu_2(V)]$ |
| `"chained_linear"` | $l_Y(x) = \mu_2(Y) + \dfrac{\sigma_2(Y)}{\sigma_2(V)} \Bigl[\mu_1(V) + \dfrac{\sigma_1(V)}{\sigma_1(X)}(x - \mu_1(X)) - \mu_2(V)\Bigr]$ |
| `"frequency_estimation"` | $e_Y(x) = Q_s^{-1}(P_s(x))$, with the percentile-rank functions of $f_s$ and $g_s$ |
| `"chained_equipercentile"` | $e_Y(x) = Q_2^{-1}\bigl(H_2(H_1^{-1}(P_1(x)))\bigr)$: X to the anchor in population 1, the anchor to Y in population 2 |

Pass presmoothed joint distributions ([`presmooth`](#presmooth)) to smooth the equipercentile
methods.

**Standard errors** (`standard_error`):

- `"analytic"`: the delta method without a distributional assumption. The linear methods are
  functions of the means, variances and covariances of the samples, whose sampling covariance
  uses the third and fourth central moments of the observed distributions (Kolen, 1985;
  Zu & Yuan, 2012); for linear equating of equivalent groups this is the formula of Braun &
  Holland (1982). The Braun–Holland method is differentiated with respect to the cell
  probabilities of the two joint distributions. Equipercentile equating of equivalent groups uses
  the formula of Lord (1982).
- `"analytic_normal"`: the same with the sampling covariance of the moments under (bivariate)
  normality. It exists for the methods that depend on moments only.
- `"bootstrap"`: resamples $N$ examinees with replacement from each sample (the cells of a joint
  distribution, so the dependence between its two scores is kept), equates each of the
  `n_replications` samples and takes the standard deviation (divisor $B - 1$) of the equated
  scores.

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

The variances and covariances plugged into the analytic formulas follow `ddof`; third and fourth
moments always divide by $N$. All three options treat the frequencies as observed: for a
presmoothed distribution they ignore that a model was fitted (the bootstrap draws from the
smoothed distribution without refitting it) and take the total frequency as the sample size.

**Returns**: [`EquatingResult`](#equatingresult)

**Raises**: `SpecificationError` if the inputs do not match a supported design, the method does
not belong to the design, a required argument is missing, a variance or covariance the method
divides by is not positive, the requested analytic standard error does not exist for the method,
or the bootstrap is asked for without `rng`.

**Warns**: `SparseDataWarning`. Braun–Holland and frequency-estimation methods: an anchor score
was observed in one population only. Bootstrap: some bootstrap samples could not be equated and
were left out.

**Checked against**: R `equate::equate` with `type = "mean"`, `"linear"` and `"equipercentile"`;
with `method = "tucker"`, `"levine"`, `"braun/holland"`, `"chained"` and `"frequency estimation"`
for the anchor test; its analytic standard errors where `equate` has them (linear and
equipercentile equating of equivalent groups, Tucker, Levine observed score, chained linear), and
`equate::bootstrap` (a statistical comparison of two Monte Carlo estimates). Equipercentile
equating, the anchor-test methods and the analytic standard errors are also checked against
independent R implementations of the published formulas.

### `EquatingResult`

An equating function from form X to the scale of form Y, returned by [`equate`](#equate).

| Attribute | Type | Description |
|---|---|---|
| `method` | str | The equating method, as passed to `equate` |
| `design` | str | `"equivalent_groups"`, `"single_group"` or `"nonequivalent_groups"` |
| `x`, `y` | `ScoreDistribution` | The distributions of form X and form Y that were equated: the margins for a single group; for non-equivalent groups, form X in the population that took it and form Y in the population that took it. For frequency estimation they are the distributions of X and Y in the synthetic population (total frequency $N_1 + N_2$) |
| `scores` | array | The possible scores of form X |
| `equated` | array | Form-Y equivalents $e_Y(x_j)$ of the possible scores of form X |
| `slope`, `intercept` | float / `None` | Coefficients of $e_Y(x) = \mathrm{intercept} + \mathrm{slope}\,x$ for the linear methods (including identity and mean); `None` for the equipercentile methods |
| `ddof` | int | Delta degrees of freedom used for the variances and covariances of the linear methods |
| `synthetic_weight` | float / `None` | Weight $w_1$ of the population that took form X (Tucker, Levine observed-score, Braun–Holland and frequency-estimation methods) |
| `anchor` | str / `None` | `"internal"` or `"external"` for the Levine methods |
| `gamma` | `(float, float)` / `None` | $(\gamma_1, \gamma_2)$ of the Tucker and Levine methods |
| `synthetic_moments` | `pandas.DataFrame` / `None` | Mean and standard deviation of X and Y in the synthetic population (rows `x`, `y`; columns `mean`, `sd`) for the Tucker, Levine observed-score, Braun–Holland and frequency-estimation methods |
| `anchor_distributions` | pair of `ScoreDistribution` / `None` | Chained equipercentile equating: the anchor distributions in the population that took X and in the population that took Y |
| `see` | array / `None` | Standard error of equating at each possible score of form X, if `standard_error` was asked for |
| `standard_error` | str / `None` | How `see` was obtained: `"analytic"`, `"analytic_normal"` or `"bootstrap"` |
| `n_replications` | int / `None` | Bootstrap: the number of bootstrap samples that `see` is based on (samples that could not be equated are left out) |
| `bootstrap_mean` | array / `None` | Bootstrap: mean of the equated scores over the bootstrap samples. Its difference from `equated` estimates the bias of the equating function |

| Member | Returns | Description |
|---|---|---|
| `table` (property) | `pandas.DataFrame` | Conversion table: `score` (form X) and `equated` (form-Y equivalent), and `see` when standard errors were computed |
| `moments` (property) | `pandas.DataFrame` | Rows `x`, `y` and `equated`; columns `mean`, `sd`, `skewness`, `kurtosis` (population forms). The `equated` row describes $e_Y(X)$, which takes the value $e_Y(x_j)$ with the relative frequency of $x_j$ |
| `transform(values)` | array | Form-Y equivalents of arbitrary form-X scores (also between possible scores), same shape as `values` |

---

## Presmoothing

### `presmooth`

```text
presmooth(distribution, *, degree=None, cross_terms=((1, 1),), max_iterations=100,
          tolerance=1e-12) -> LoglinearResult
```

Presmooth a score distribution with a polynomial log-linear model (Holland & Thayer, 2000),
fitted by maximum likelihood (Newton's method). For one score with frequencies $n_j$,

$$
\log m_j = \beta_0 + \sum_{i=1}^{C} \beta_i\, x_j^{\,i},
$$

and for the joint distribution of two scores

$$
\log m_{jk} = \beta_0 + \sum_{i=1}^{C_X} \beta_{Xi}\, x_j^{\,i}
              + \sum_{i=1}^{C_Y} \beta_{Yi}\, y_k^{\,i}
              + \sum_{(a, b)} \beta_{ab}\, x_j^{\,a} y_k^{\,b} .
$$

The fitted distribution has the observed total and the same first $C$ moments as the observed
one; the bivariate model also preserves the cross moments $E[X^a Y^b]$ of the included cross
terms.

| Argument | Type | Description |
|---|---|---|
| `distribution` | `ScoreDistribution` / `BivariateScoreDistribution` | The observed distribution |
| `degree` | int / `(int, int)`, optional | Polynomial degree $C$ (default 6) for one score, or $(C_X, C_Y)$ (default `(6, 6)`) for a joint distribution. It is R `equate`'s `degrees` and the degree of the polynomial in a `glm` formula |
| `cross_terms` | sequence of `(int, int)`, default `((1, 1),)` | Joint distributions only: the powers $(a, b)$ of the cross terms $x^a y^b$. An empty sequence gives a model in which the two scores are independent |
| `max_iterations` | int, default `100` | Maximum number of Newton iterations |
| `tolerance` | float, default `1e-12` | Convergence tolerance on the score equations (differences between observed and fitted moments of the orthonormalized terms, as proportions) |

**Returns**: [`LoglinearResult`](#loglinearresult)

**Raises**: `SpecificationError` if a degree is not a positive integer or exceeds what the number
of possible scores supports (one score: at most `n_scores - 2`), the cross terms are invalid, or
the model has as many parameters as there are cells.

**Warns**: `ConvergenceWarning` if Newton's method does not converge within `max_iterations`.

**Checked against**: R `stats::glm(family = poisson)` and `equate::presmoothing(smoothmethod =
"loglinear")`.

### `LoglinearResult`

A fitted polynomial log-linear model, returned by [`presmooth`](#presmooth).

| Attribute | Type | Description |
|---|---|---|
| `distribution` | `ScoreDistribution` / `BivariateScoreDistribution` | The presmoothed distribution: the fitted frequencies on the same possible scores. Its total equals the observed total |
| `observed` | `ScoreDistribution` / `BivariateScoreDistribution` | The distribution that was smoothed |
| `terms` | tuple of str | Names of the polynomial terms, e.g. `("x^1", "x^2")` or `("x^1", "y^1", "x^1*y^1")` |
| `design_matrix` | array of shape `(n_cells, n_terms)` | The polynomial terms evaluated at every cell (no intercept column). Scores are rescaled to $[-1, 1]$ before taking powers; this changes neither the model nor the fit. For a joint distribution the cells are in row-major order (X varies slowest) |
| `log_likelihood` | float | Poisson log-likelihood at the fitted frequencies, $\sum_j [n_j \log m_j - m_j - \log n_j!]$ |
| `n_iterations` | int | Number of Newton iterations |
| `converged` | bool | Whether the score equations were solved to the requested tolerance |
| `n_parameters` | int | Number of free parameters: the polynomial terms plus the intercept |
| `degrees_of_freedom` | int | Residual degrees of freedom: number of cells minus number of parameters |

| Property | Returns | Description |
|---|---|---|
| `fit_statistics` | `pandas.Series` | `likelihood_ratio`, `pearson`, `freeman_tukey`, `degrees_of_freedom`, `n_parameters`, `log_likelihood` and `aic` |
| `c_matrix` | array of shape `(n_cells, n_terms)` | The C-matrix of the fitted probabilities (Holland & Thayer, 1987): $\operatorname{Cov}(\hat r) \approx C C^\top / N$. Kernel equating uses it for its standard errors. Any matrix with the same $C C^\top$ serves equally; the columns themselves are not unique |

With observed frequencies $n_j$, fitted frequencies $m_j$, Poisson log-likelihood $\ell$ and $p$
parameters, the fit statistics are

$$
\begin{aligned}
G^2 &= 2 \sum_j n_j \log(n_j / m_j) \\
\chi^2_{\mathrm{Pearson}} &= \sum_j (n_j - m_j)^2 / m_j \\
\chi^2_{\mathrm{FT}} &= \sum_j \bigl(\sqrt{n_j} + \sqrt{n_j + 1} - \sqrt{4 m_j + 1}\bigr)^2 \\
\mathrm{AIC} &= -2 \ell + 2 p .
\end{aligned}
$$

`aic` equals R `glm`'s AIC for the same Poisson model.

---

## Kernel equating

### `kernel_equate`

```text
kernel_equate(x, y=None, *, design=None, bandwidth_x=None, bandwidth_y=None,
              anchor_bandwidths=None, penalty_weight=1.0, linear=False, synthetic_weight=None,
              counterbalance_weights=(0.5, 0.5), kernel="gaussian",
              bandwidth_method="penalty") -> KernelEquatingResult
```

Kernel equating of form X to form Y (von Davier, Holland & Thayer, 2004; Lee & von Davier, 2011).
The discrete distributions with score probabilities $r_j$ (X) and $s_k$ (Y) are continuized,

$$
F_{h_X}(x) = \sum_j r_j\, K\!\left(\frac{x - a_X x_j - (1 - a_X)\mu_X}{a_X h_X}\right),
\qquad a_X^2 = \frac{\sigma_X^2}{\sigma_X^2 + \sigma_V^2 h_X^2},
$$

and likewise $G_{h_Y}$, with $K$ the distribution function of the kernel and $\sigma_V^2$ its
variance. The continuized variable keeps the mean and the variance of the discrete one. The
equating function is

$$
e_Y(x) = G_{h_Y}^{-1}\bigl(F_{h_X}(x)\bigr) .
$$

| Argument | Type | Description |
|---|---|---|
| `x` | `ScoreDistribution` / `BivariateScoreDistribution` / `LoglinearResult` | First input of the design (below). Pass the result of [`presmooth`](#presmooth) to equate presmoothed distributions; a plain distribution is used as observed |
| `y` | the same, optional | Second input of the design; omit it for a single group |
| `design` | str, optional | `"equivalent_groups"` and `"single_group"` follow from the inputs. With two joint distributions it is required: `"counterbalanced"`, `"chained"` or `"post_stratification"` |
| `bandwidth_x`, `bandwidth_y` | float, optional | Bandwidths $h_X$ and $h_Y$. By default each is chosen by `bandwidth_method` |
| `anchor_bandwidths` | `(float or None, float or None)`, optional | Chained equating: bandwidths of the anchor in the population that took X and in the population that took Y. `None` entries are chosen by `bandwidth_method` |
| `penalty_weight` | float, default `1.0` | Weight $K$ of the second penalty term in the bandwidth selection (see [`penalty_bandwidth`](#penalty_bandwidth)) |
| `linear` | bool, default `False` | Use bandwidths of 1000 standard deviations, which gives the linear equating function of the design (and its standard error). Not together with explicit bandwidths, and not with the uniform kernel |
| `synthetic_weight` | float, optional | Post-stratification: weight $w$ of the population that took X, between 0 and 1. Default $N_P / (N_P + N_Q)$ |
| `counterbalance_weights` | `(float, float)`, default `(0.5, 0.5)` | Counterbalanced design: $(w_X, w_Y)$, the weights of the sample that took X first in $r$ and in $s$ |
| `kernel` | `"gaussian"` / `"logistic"` / `"uniform"`, default `"gaussian"` | The kernel: standard normal ($\sigma_V^2 = 1$), standard logistic ($\pi^2/3$) or uniform on $(-1/2, 1/2)$ ($1/12$). With the uniform kernel the continuized density is zero outside its support and, for a bandwidth below the score increment, between the possible scores; where the density of Y is zero at an equated score, `see` is `nan` |
| `bandwidth_method` | `"penalty"` / `"rule_of_thumb"` / `"double_smoothing"` / `"cross_validation"`, default `"penalty"` | Rule for the bandwidths that are not given (below) |

**Designs.** The design gives $r$ and $s$ from the estimated (presmoothed or observed)
probabilities.

| `design` | Inputs | $r$ and $s$ |
|---|---|---|
| `"equivalent_groups"` | `x`, `y`: distributions of X and Y in two independent samples | Their probabilities |
| `"single_group"` | `x`: joint distribution of (X, Y) in one sample | Its two margins |
| `"counterbalanced"` | `x`, `y`: joint distributions of (X, Y) in the sample that took X first and in the sample that took Y first, with margins $r_1, s_1$ and $r_2, s_2$ | $r = w_X r_1 + (1 - w_X) r_2$, $s = w_Y s_1 + (1 - w_Y) s_2$ |
| `"post_stratification"` | `x`: joint distribution of (X, anchor) in population P; `y`: joint distribution of (Y, anchor) in population Q | The distributions of X and Y in the synthetic population $T = wP + (1 - w)Q$, assuming that the distribution of each form given the anchor score is the same in P and Q |
| `"chained"` | The same inputs | $e_Y(x) = G_Q^{-1}\bigl(H_Q(H_P^{-1}(F_P(x)))\bigr)$: X is equated to the anchor in P and the anchor to Y in Q, with four continuized distributions |

**Bandwidth rules** (`bandwidth_method`). The last three are defined for the Gaussian kernel.

| Value | Rule |
|---|---|
| `"penalty"` | [`penalty_bandwidth`](#penalty_bandwidth) with `penalty_weight`; any kernel |
| `"rule_of_thumb"` | $h = 9\sigma / \sqrt{100 N^{2/5} - 81}$ (Andersson & von Davier, 2014), with $\sigma$ the standard deviation of the distribution that is continuized and $N$ the size of the sample that took the form. Not for the counterbalanced design |
| `"double_smoothing"` | Minimizes the double-smoothing criterion of Häggström & Wiberg (2014), with a pilot bandwidth of 4 score increments (as in `kequate`). The minimum is searched below the pilot bandwidth |
| `"cross_validation"` | Minimizes the leave-one-out criterion of `kequate`: each score probability is predicted from the others by a kernel-weighted average. This is not the likelihood cross-validation of Liang & von Davier (2014) |

**Standard error of equating.** `see` is computed by the delta method (von Davier et al., 2004,
ch. 5) from the covariance of the estimated probabilities of each sample: the covariance implied
by the log-linear model for a presmoothed input, the multinomial covariance otherwise. The
selected bandwidths are treated as fixed, whatever the rule.

**Returns**: [`KernelEquatingResult`](#kernelequatingresult)

**Raises**: `SpecificationError` if the inputs do not fit the design, a distribution has no
variance, a weight or a bandwidth is out of range, the options do not fit each other (a kernel
other than Gaussian with a bandwidth rule other than the penalty, `linear=True` with explicit
bandwidths or the uniform kernel, the rule of thumb in the counterbalanced design), or
(post-stratification) an anchor score has probability zero in one population but not in the
other.

**Checked against**: R `kequate::kequate` in the designs `"EG"`, `"SG"`, `"CB"`, `"NEAT_PSE"` and
`"NEAT_CE"`, with `kernel = "logistic"` and `"uniform"`, and with its double-smoothing,
cross-validation and rule-of-thumb bandwidths; `SNSequate::ker.eq` (equivalent groups); an
independent R implementation with finite-difference standard errors.

### `KernelEquatingResult`

A kernel equating function from form X to the scale of form Y, returned by
[`kernel_equate`](#kernel_equate).

| Attribute | Type | Description |
|---|---|---|
| `design` | str | `"equivalent_groups"`, `"single_group"`, `"counterbalanced"`, `"chained"` or `"post_stratification"` |
| `x`, `y` | `ScoreDistribution` | The score distributions that were continuized: the score probabilities $r$ and $s$ given by the design (margins, weighted margins, or the synthetic population; for chained equating, X in the population that took it and Y in the population that took it) |
| `scores` | array | The possible scores of form X |
| `equated` | array | Form-Y equivalents $e_Y(x_j)$ |
| `see` | array | Standard error of equating at each possible score |
| `see_vectors` | array of shape `(n_scores, n_columns)` | The vectors whose Euclidean norms are `see`; `seed()` uses them |
| `bandwidth_x`, `bandwidth_y` | float | Bandwidths $h_X$ and $h_Y$ |
| `penalty_weight` | float | The weight $K$ used when a bandwidth was selected by the penalty |
| `kernel` | str | `"gaussian"`, `"logistic"` or `"uniform"` |
| `bandwidth_method` | str | The rule that selects the bandwidths that were not given |
| `x_presmoothed`, `y_presmoothed` | bool | Whether the first and the second input came from a log-linear model (which determines the covariance used for the standard errors). Equal for a single group |
| `anchor_distributions` | pair of `ScoreDistribution` / `None` | Chained equating: the anchor distributions in the populations that took X and Y |
| `anchor_bandwidths` | `(float, float)` / `None` | Chained equating: the bandwidths of the two anchor distributions |
| `synthetic_weight` | float / `None` | Post-stratification: weight of the population that took X in the synthetic population |
| `counterbalance_weights` | `(float, float)` / `None` | Counterbalanced design: the weights of the first sample in $r$ and in $s$ |

| Member | Returns | Description |
|---|---|---|
| `table` (property) | `pandas.DataFrame` | Conversion table: `score`, `equated` and `see` |
| `continuized` (property) | `pandas.DataFrame` | Continuized distributions at the possible scores of each form: `form`, `score`, `probability` (discrete), `cdf`, `density`. `form` is `"x"` or `"y"`, and for chained equating also `"anchor_x"` and `"anchor_y"` |
| `percent_relative_error` (property) | `pandas.Series` | Percent relative error in the first ten moments, indexed by the moment order 1..10. Raises `SpecificationError` for chained equating |
| `chain_percent_relative_error` (property) | `pandas.DataFrame` | Chained equating: percent relative error of the two links, columns `x_to_anchor` and `anchor_to_y`. Raises `SpecificationError` for other designs |
| `transform(values)` | array | Form-Y equivalents of arbitrary form-X scores, same shape as `values` |
| `seed(other)` | `pandas.DataFrame` | Standard error of the difference between two equating functions: columns `score`, `difference` (this function minus `other`) and `seed` |

The percent relative error compares the moments of the equated scores with those of form Y:

$$
\mathrm{PRE}(p) = 100\, \frac{\mu_p(e_Y(X)) - \mu_p(Y)}{\mu_p(Y)}, \qquad
\mu_p(e_Y(X)) = \sum_j r_j\, e_Y(x_j)^p, \quad \mu_p(Y) = \sum_k s_k\, y_k^p .
$$

**`seed(other)`**. For two equating functions $e_1$ and $e_2$ estimated from the same data,

$$
\mathrm{SEED}(x) = \sqrt{\operatorname{Var}\bigl(e_1(x) - e_2(x)\bigr)} .
$$

`other` must be computed **from the same inputs**: the same distributions or presmoothing results,
in the same design or in the other anchor-test design (chained against post-stratification). This
cannot be checked beyond the shapes; with different data the result is meaningless. Typical uses:
kernel against linear equating (`linear=True`), two sets of bandwidths, or chained against
post-stratification equating. It raises `SpecificationError` if the two results do not have the
same X scores and the same sources of sampling variation.

### `penalty_bandwidth`

```text
penalty_bandwidth(distribution, *, penalty_weight=1.0, kernel="gaussian") -> float
```

The bandwidth that minimizes the penalty of von Davier et al. (2004, ch. 4),

$$
\mathrm{PEN}(h) = \sum_j \bigl(r_j - f_h(x_j)\bigr)^2 + K \sum_j A_j (1 - B_j) .
$$

The first term makes the continuized density $f_h$ close to the score probabilities at the
possible scores. The second counts the scores around which the density is U-shaped: $A_j = 1$ if
$f_h'(x_j - w) < 0$ and $B_j = 0$ if $f_h'(x_j + w) > 0$, with $w$ a quarter of the score
increment. Scores are measured in units of their increment while the penalty is evaluated, and the
bandwidth is returned on the score scale. The minimum is searched between 0.05 and 10 increments.

| Argument | Type | Description |
|---|---|---|
| `distribution` | `ScoreDistribution` / `LoglinearResult` | The score distribution; for a presmoothing result, the smoothed distribution is used |
| `penalty_weight` | float, default `1.0` | The weight $K$ of the second term (`kequate`'s `KPEN`, `SNSequate`'s `Kp`). 0 drops it |
| `kernel` | `"gaussian"` / `"logistic"` / `"uniform"`, default `"gaussian"` | The kernel of the continuization. The density of the uniform kernel is piecewise constant, so its second penalty term is zero whatever `penalty_weight` |

**Returns**: float, the bandwidth $h$.

**Raises**: `SpecificationError` if `penalty_weight` is negative, the kernel is unknown, or the
distribution is not a univariate one or has no variance.

**Checked against**: R `kequate` (with `KPEN = 0`), `SNSequate::bandwidth` and an independent R
implementation.

---

## `flexpyequate.errors`

Exception and warning classes. All errors raised intentionally by the library derive from
`FlexpyequateError`, and all warnings from `FlexpyequateWarning`, so they can be caught as a
family.

```text
from flexpyequate import errors
```

### `FlexpyequateError`

Base class for all errors raised by flexpyequate (an `Exception`).

### `ScoreDistributionError`

Scores or frequencies do not form a valid score distribution. Examples: possible scores that are
not equally spaced, negative frequencies, an observed score that is not one of the possible
scores, or a distribution without any observation. Derives from `FlexpyequateError` and
`ValueError`.

### `SpecificationError`

The arguments of a call are inconsistent with each other or with the data. Examples: a
single-group method given two separate distributions, an unknown method name, or a polynomial
degree that the number of possible scores cannot support. Derives from `FlexpyequateError` and
`ValueError`.

### `FlexpyequateWarning`

Base class for all warnings issued by flexpyequate (a `UserWarning`).

### `ConvergenceWarning`

An iterative procedure stopped before reaching its convergence criterion (log-linear
presmoothing). Derives from `FlexpyequateWarning`.

### `SparseDataWarning`

The data are too sparse for part of a computation, which was done on what is available. Example:
an anchor score observed in only one of two populations, so that a conditional distribution given
that score cannot be estimated. Derives from `FlexpyequateWarning`.

---

## `__version__`

The installed version of flexpyequate, as a string (`flexpyequate.__version__`).

---

## References

- Andersson, B., & von Davier, A. A. (2014). Improving the bandwidth selection in kernel
  equating. *Journal of Educational Measurement, 51*, 223–238.
- Braun, H. I., & Holland, P. W. (1982). Observed-score test equating: A mathematical analysis
  of some ETS equating procedures. In P. W. Holland & D. B. Rubin (Eds.), *Test equating*
  (pp. 9–49). Academic Press.
- Häggström, J., & Wiberg, M. (2014). Optimal bandwidth selection in observed-score kernel
  equating. *Journal of Educational Measurement, 51*, 201–211.
- Holland, P. W., & Thayer, D. T. (1987). *Notes on the use of log-linear models for fitting
  discrete probability distributions* (ETS RR-87-31).
- Holland, P. W., & Thayer, D. T. (2000). Univariate and bivariate loglinear models for discrete
  test score distributions. *Journal of Educational and Behavioral Statistics, 25*, 133–183.
- Kolen, M. J. (1985). Standard errors of Tucker equating. *Applied Psychological Measurement,
  9*, 209–223.
- Kolen, M. J., & Brennan, R. L. (2014). *Test equating, scaling, and linking* (3rd ed.). Springer.
- Lee, Y.-H., & von Davier, A. A. (2011). Equating through alternative kernels. In A. A. von
  Davier (Ed.), *Statistical models for test equating, scaling, and linking* (pp. 159–173).
  Springer.
- Liang, T., & von Davier, A. A. (2014). Cross-validation: An alternative bandwidth selection
  method in kernel equating. *Applied Psychological Measurement, 38*, 281–295.
- Lord, F. M. (1982). The standard error of equipercentile equating. *Journal of Educational
  Statistics, 7*, 165–174.
- von Davier, A. A., Holland, P. W., & Thayer, D. T. (2004). *The kernel method of test equating*.
  Springer.
- Zu, J., & Yuan, K.-H. (2012). Standard error of linear observed-score equating for the NEAT
  design with nonnormally distributed data. *Journal of Educational Measurement, 49*, 190–213.
