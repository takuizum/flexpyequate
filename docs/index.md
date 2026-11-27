# flexpyequate

English | [日本語](index.ja.md)

Equating of test score distributions in Python. Given the score distributions of two test forms,
flexpyequate finds the function that puts scores of form X on the scale of form Y: mean, linear
and equipercentile equating, the methods for an anchor test, log-linear presmoothing and kernel
equating.

- **Checked against R**: every method is compared numerically with R `equate`, `kequate` and
  `SNSequate`, and with independent implementations of the published formulas.
- **Light**: it depends on NumPy, SciPy and pandas only.
- **Scope**: observed-score equating of score distributions. Equating that needs item parameters
  (IRT true-score and observed-score equating, scale linking) is in
  [flexpyirt](https://github.com/takuizum/flexpyirt).

> Under development (0.x). The public API may change before 1.0.0.

## Installation

Python 3.12 or later.

```bash
pip install flexpyequate  # or: uv add flexpyequate
```

## A first equating

Two forms were taken by equivalent groups. Build a score distribution for each form and equate
form X to form Y.

```python
import flexpyequate as fe

# Frequencies of the scores 0..4 on two forms taken by equivalent groups.
x = fe.ScoreDistribution.from_frequencies(scores=range(5), frequencies=[4, 6, 6, 3, 1])
y = fe.ScoreDistribution.from_frequencies(scores=range(5), frequencies=[2, 4, 6, 4, 4])

result = fe.equate(x, y, method="equipercentile")
print(result.table)
#    score   equated
# 0    0.0  0.500000
# 1    1.0  1.666667
# 2    2.0  2.750000
# 3    3.0  3.875000
# 4    4.0  4.375000

result.transform([1.5, 2.5])  # equate scores between the possible scores
result.moments  # mean, sd, skewness, kurtosis of X, Y and the equated scores

linear = fe.equate(x, y, method="linear")
linear.slope, linear.intercept
```

## What is in the package

| Task | Function |
|---|---|
| Describe the scores of a form, or of two scores taken by the same examinees | `ScoreDistribution`, `BivariateScoreDistribution` |
| Mean, linear and equipercentile equating; the anchor-test methods (Tucker, Levine, Braun–Holland, chained, frequency estimation); standard errors | `equate()` |
| Smooth a distribution with a polynomial log-linear model | `presmooth()` |
| Kernel equating in five designs, with standard errors | `kernel_equate()` |

## Where to go next

- [User guide](guide.md): score distributions, each equating method and design, standard errors,
  presmoothing, kernel equating, and how to read the results.
- [API reference](reference.md): every public class and function.
- Source code, issues and releases: [GitHub](https://github.com/takuizum/flexpyequate).
