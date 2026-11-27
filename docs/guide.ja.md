# ユーザーガイド

[English](guide.md) | 日本語

flexpyequate で得点分布を作り、等化し、結果を読む手順をまとめる。このページのコード例は上から順に 1 つの
スクリプトとして実行できる。関数ごとの引数は [API リファレンス](reference.ja.md) を参照。

1. [準備とデータ](#1-準備とデータ)
2. [得点分布](#2-得点分布)
3. [等価群](#3-等価群)
4. [結果を読む](#4-結果を読む)
5. [単一群](#5-単一群)
6. [アンカーテストつき非等価群](#6-アンカーテストつき非等価群)
7. [等化の標準誤差](#7-等化の標準誤差)
8. [対数線形モデルによる事前平滑化](#8-対数線形モデルによる事前平滑化)
9. [カーネル等化](#9-カーネル等化)
10. [エラーと警告](#10-エラーと警告)
11. [R パッケージとの違い](#11-r-パッケージとの違い)

## 1. 準備とデータ

flexpyequate に設定は要らない。乱数を使う関数は `rng`（`numpy.random.Generator` または整数のシード）を
受け取るので、結果を再現できる。

例にはシミュレーションで作った正答数得点を使う。データの集め方（デザイン）は 3 通りあり、それぞれに
データを用意する。

- **等価群**: 同じ母集団から無作為に分けた 2 群の一方が X 版、他方が Y 版を受ける。
- **単一群**: 同じ受検者が両方の版を受ける。
- **アンカーテストつき非等価群**: 能力が異なるかもしれない 2 群が、それぞれ 1 つの版と共通のアンカーテストを
  受ける。

```python
import warnings

import numpy as np

import flexpyequate as fe
from flexpyequate import errors

rng = np.random.default_rng(20261127)


def simulate_scores(ability, n_items, difficulty):
    """難しさが同じ n_items 項目の正答数得点。"""
    p = 1.0 / (1.0 + np.exp(-(ability - difficulty)))
    return rng.binomial(n_items, p)


# 等価群: 各版 2000 人、40 項目。Y 版のほうがやさしい。
x_scores = simulate_scores(rng.normal(0.0, 1.0, 2000), 40, 0.0)
y_scores = simulate_scores(rng.normal(0.0, 1.0, 2000), 40, -0.3)

# 単一群: 1500 人が両方の版を受ける。
ability = rng.normal(0.0, 1.0, 1500)
both_x = simulate_scores(ability, 40, 0.0)
both_y = simulate_scores(ability, 40, -0.3)

# アンカーテスト: 母集団 P が X 版、母集団 Q（能力が高い）が Y 版を受ける。
# 各版に固有の項目が 30、両群に共通のアンカー項目が 10。
ability_p = rng.normal(0.0, 1.0, 2000)
ability_q = rng.normal(0.3, 1.0, 1600)
x_unique = simulate_scores(ability_p, 30, 0.0)
x_anchor = simulate_scores(ability_p, 10, 0.0)
y_unique = simulate_scores(ability_q, 30, -0.2)
y_anchor = simulate_scores(ability_q, 10, 0.0)
```

## 2. 得点分布

等化の関数はどれも、生データではなく得点分布を受け取る。得点分布は、等間隔で増加する**とりうる得点**と、
それぞれの度数の組である。誰も取らなかった得点も、度数 0 として分布に含める。

### 1 つの得点: `ScoreDistribution`

`from_scores` は受検者ごとの得点を集計する。とりうる得点は `score_range`（最低点と最高点。間隔は
`increment` で、既定は 1）か `scores` で指定する。どちらも指定しないと観測された範囲を使うので、観測された
最低点より下と最高点より上のとりうる得点は分布に入らない。

```python
x = fe.ScoreDistribution.from_scores(x_scores, score_range=(0, 40))
y = fe.ScoreDistribution.from_scores(y_scores, score_range=(0, 40))
print(x)
# ScoreDistribution(scores=0..40 by 1, n=2000, mean=19.8150, sd=8.8167)
```

`from_frequencies` は度数表から作る。等間隔であれば、得点は整数でなくてよい。

```python
half_points = fe.ScoreDistribution.from_frequencies(
    scores=[0.0, 0.5, 1.0, 1.5, 2.0], frequencies=[3, 8, 12, 9, 4]
)
half_points.increment  # 0.5
```

欠測値は扱えない。分布を作る前に除いておく。

分布からはモーメント、パーセンタイル順位、パーセンタイルが得られる。

```python
x.n_scores, x.n  # とりうる得点の数、標本サイズ
x.mean, x.sd(), x.variance()  # 母集団形（N で割る）
x.sd(ddof=1)  # 標本形（N - 1 で割る）
x.skewness, x.kurtosis  # 尖度は正規分布で 3
x.probabilities, x.cumulative  # 相対度数と累積相対度数

x.percentile_rank([20, 20.5])  # 0〜100。とりうる得点の間の値でもよい
x.percentile([25, 50, 75])  # 逆関数: パーセンタイル順位に対応する得点
x.to_frame().head()  # score, frequency, probability, cumulative, percentile_rank
```

パーセンタイル順位は Kolen & Brennan (2014) の定義に従う。とりうる得点 $x_j$ は区間
$[x_j - \delta/2,\ x_j + \delta/2)$ を代表し（$\delta$ は得点の刻み幅）、受検者はその区間に一様に分布すると
みなす。したがって、とりうる得点でのパーセンタイル順位は、その得点より下の割合に、その得点の割合の半分を
足したものになる。`percentile` はその逆関数である。度数 0 のために累積分布が平らな区間では、その区間の
中点（Kolen & Brennan の上側・下側パーセンタイルの平均）を返す。

### 2 つの得点: `BivariateScoreDistribution`

同じ受検者に 2 つの得点があるとき、その同時分布を `BivariateScoreDistribution` で表す。単一群（X 版と
Y 版）とアンカーテスト（1 つの版とアンカー）で使う。

```python
xy = fe.BivariateScoreDistribution.from_scores(both_x, both_y, x_range=(0, 40), y_range=(0, 40))
print(xy)
# BivariateScoreDistribution(x=0..40, y=0..40, n=1500, correlation=0.8832)

xy.x, xy.y  # 2 つの周辺分布（ScoreDistribution）
xy.correlation, xy.covariance()
xy.frequencies.shape  # (41, 41): 行が X の得点、列が Y の得点
xy.to_frame().head()  # 縦持ち: x_score, y_score, frequency, probability
```

アンカーテストでは、版を第 1 変数、**アンカーを第 2 変数**にする。

```python
# 外部アンカー: アンカー項目は版の得点に含めない。
xa = fe.BivariateScoreDistribution.from_scores(x_unique, x_anchor, x_range=(0, 30), y_range=(0, 10))
ya = fe.BivariateScoreDistribution.from_scores(y_unique, y_anchor, x_range=(0, 30), y_range=(0, 10))

# 内部アンカー: アンカー項目も合計得点に含める。
xa_internal = fe.BivariateScoreDistribution.from_scores(
    x_unique + x_anchor, x_anchor, x_range=(0, 40), y_range=(0, 10)
)
ya_internal = fe.BivariateScoreDistribution.from_scores(
    y_unique + y_anchor, y_anchor, x_range=(0, 40), y_range=(0, 10)
)
```

2 元の度数表から作るときは
`BivariateScoreDistribution.from_frequencies(x_scores=..., y_scores=..., frequencies=...)` を使う。

## 3. 等価群

`equate(x, y, method=...)` は X 版を Y 版の尺度に等化する。デザインは渡したものから決まり、
`ScoreDistribution` を 2 つ渡すと等価群になる。

| `method` | 等化関数 |
|---|---|
| `"identity"` | $e_Y(x) = x$ |
| `"mean"` | $e_Y(x) = x - \mu_X + \mu_Y$ |
| `"linear"` | $e_Y(x) = \dfrac{\sigma_Y}{\sigma_X}(x - \mu_X) + \mu_Y$ |
| `"equipercentile"`（既定） | $e_Y(x) = Q^{-1}(P(x))$ |

$\mu$ と $\sigma$ は平均と標準偏差、$P$ は X 版のパーセンタイル順位関数、$Q^{-1}$ は Y 版の
パーセンタイル関数である（2 節）。

```python
mean = fe.equate(x, y, method="mean")
linear = fe.equate(x, y, method="linear")
equipercentile = fe.equate(x, y, method="equipercentile")

print(linear)
# EquatingResult(method='linear', design='equivalent_groups', slope=0.985374, intercept=2.888805, n_scores=41)
mean.slope, mean.intercept  # 傾きは 1、切片は平均の差
```

線形等化の標準偏差は、既定では Kolen & Brennan と同じ母集団形（$N$ で割る）である。`ddof=1` にすると
R `equate` と同じ標本形（$N - 1$ で割る）になる。

```python
linear_sample = fe.equate(x, y, method="linear", ddof=1)
```

## 4. 結果を読む

`equate()` は `EquatingResult` を返す。

```python
equipercentile.table.head()  # 換算表: score（X 版）と equated（Y 版での対応値）
equipercentile.scores, equipercentile.equated  # 同じ 2 列を配列で

# X 版の任意の得点を等化する。とりうる得点の間の値でもよい。
equipercentile.transform([19.5, 20.0])

# X、Y、等化後の X 得点の平均・標準偏差・歪度・尖度
print(equipercentile.moments)
#               mean        sd  skewness  kurtosis
# x        19.815000  8.816676 -0.031222  2.182716
# y        22.414000  8.687727 -0.165331  2.257228
# equated  22.413024  8.682557 -0.164098  2.253566
```

等化がうまくいっていれば、`moments` の `equated` の行は `y` の行に近い。等化後の X 版の得点が Y 版の
得点と同じように分布するということである。平均等化は平均だけ、線形等化は平均と標準偏差を合わせる。
等パーセンタイル等化は、得点が離散であることが許す範囲で分布全体を合わせる。

そのほかの属性は、結果がどう求められたかを示す。

| 属性 | 内容 |
|---|---|
| `method`、`design` | 手法と、`"equivalent_groups"`・`"single_group"`・`"nonequivalent_groups"` のいずれか |
| `x`、`y` | 等化した `ScoreDistribution` |
| `slope`、`intercept` | 線形の手法の係数。等パーセンタイルの手法では `None` |
| `ddof` | 使った `ddof` |
| `see`、`standard_error`、`n_replications`、`bootstrap_mean` | 標準誤差（7 節）。求めなかったときは `None` |
| `synthetic_weight`、`anchor`、`gamma`、`synthetic_moments`、`anchor_distributions` | アンカーテストを使う手法（6 節）。それ以外では `None` |

等パーセンタイル等化の `transform` は、X 版の最低のとりうる得点より刻み幅の半分を超えて低い得点に
パーセンタイル順位 0 に対応する Y 版の値を、最高のとりうる得点より刻み幅の半分以上高い得点に
パーセンタイル順位 100 に対応する値を返す。

## 5. 単一群

`BivariateScoreDistribution` を 1 つだけ渡し、`y` は渡さない。2 つの周辺分布を、等価群と同じ 4 つの手法で
等化する。

```python
single = fe.equate(xy, method="equipercentile")
single.design  # 'single_group'
single_linear = fe.equate(xy, method="linear")
single_linear.slope, single_linear.intercept
```

等化関数は、等価群の場合とまったく同じように周辺分布から計算する。同時分布が効くのは標準誤差（7 節）で
ある。2 つの得点が同じ受検者のものだからである。

## 6. アンカーテストつき非等価群

`BivariateScoreDistribution` を 2 つ渡す。1 つめは X 版を受けた母集団での X 版とアンカー、2 つめは Y 版を
受けた母集団での Y 版とアンカーである。アンカーのとりうる得点は両方で同じでなければならない。

| `method` | 種類 | `synthetic_weight` を使う | `anchor` が必要 |
|---|---|---|---|
| `"tucker"` | 線形 | はい | いいえ |
| `"levine_observed"` | 線形 | はい | はい |
| `"levine_true"` | 線形 | いいえ | はい |
| `"braun_holland"` | 線形 | はい | いいえ |
| `"chained_linear"` | 線形 | いいえ | いいえ |
| `"frequency_estimation"` | 等パーセンタイル | はい | いいえ |
| `"chained_equipercentile"` | 等パーセンタイル | いいえ | いいえ |

### 線形の手法

Tucker 法、Levine の観測得点法、Braun–Holland 法は、2 つの母集団を重み $w_1$（X 版を受けた母集団）と
$w_2 = 1 - w_1$ で混ぜた**合成母集団**で線形等化を行う。重みの既定は標本サイズに比例する値で、
`synthetic_weight` で $w_1$ を指定できる。

```python
tucker = fe.equate(xa, ya, method="tucker")
tucker.slope, tucker.intercept
tucker.synthetic_weight  # 2000 / (2000 + 1600)
tucker.gamma  # (gamma_1, gamma_2): 版の得点のアンカー得点への回帰係数
print(tucker.synthetic_moments)  # 合成母集団での X・Y の平均と標準偏差
#         mean        sd
# x  15.719047  6.693560
# y  17.697187  6.407046

# X 版を受けた母集団を合成母集団にする:
tucker_p = fe.equate(xa, ya, method="tucker", synthetic_weight=1.0)
```

Levine の方法では、アンカーが得点に含まれるかどうかを指定する。アンカー項目が合計得点に含まれるとき
（第 1 変数がアンカーを含むとき）は `anchor="internal"`、アンカーを別に採点するときは
`anchor="external"` とする。

```python
levine = fe.equate(xa, ya, method="levine_observed", anchor="external")
levine_internal = fe.equate(xa_internal, ya_internal, method="levine_observed", anchor="internal")
levine_true = fe.equate(xa, ya, method="levine_true", anchor="external")
```

Braun–Holland 法は、頻度推定法（後述）の合成分布から X と Y の平均と標準偏差を求めて線形等化を行う。
連鎖線形等化は、第 1 の母集団で X をアンカーに、第 2 の母集団でアンカーを Y に等化する。合成母集団は
使わない。

```python
braun_holland = fe.equate(xa, ya, method="braun_holland")
chained_linear = fe.equate(xa, ya, method="chained_linear")
```

### 等パーセンタイルの手法

頻度推定法（事後層化）は、アンカー得点を与えたときの各版の得点分布が 2 つの母集団で同じであると仮定して、
合成母集団での X と Y の分布を推定し、それらを等パーセンタイル法で等化する。連鎖等パーセンタイル等化は、
第 1 の母集団で X をアンカーに、第 2 の母集団でアンカーを Y に等化する。

```python
frequency_estimation = fe.equate(xa, ya, method="frequency_estimation")
frequency_estimation.x  # 合成母集団での X の分布
frequency_estimation.synthetic_moments

chained = fe.equate(xa, ya, method="chained_equipercentile")
chained.anchor_distributions  # 2 つの母集団でのアンカーの分布
```

頻度推定法では、結果の `x` と `y` は合成分布である（総度数は $N_1 + N_2$）。アンカーテストを使う
そのほかの手法では、X 版を受けた母集団での X 版と、Y 版を受けた母集団での Y 版である。

頻度推定法と Braun–Holland 法では、どのアンカー得点も両方の母集団で観測されている必要がある。一方の
母集団でしか観測されなかったアンカー得点があると、他方の母集団のその部分を除いて計算し、
`SparseDataWarning` を出す。同時分布を事前平滑化すれば（8 節）これは起こらない。等パーセンタイルの手法では
もともと事前平滑化するのが普通である。

## 7. 等化の標準誤差

`standard_error=` を指定すると、X 版のとりうる得点ごとに等化の標準誤差を求める。`table` の列 `see` と
属性 `see` に入る。

```python
linear_se = fe.equate(x, y, method="linear", standard_error="analytic")
linear_se.table.head()  # score, equated, see
linear_se.see  # 同じものを配列で
```

選択肢は 3 つある。

- `"analytic"`: 分布を仮定しないデルタ法。線形の手法では観測された分布の 3 次・4 次のモーメントを使う。
  等価群の等パーセンタイル等化では Lord (1982) の式である。
- `"analytic_normal"`: 得点が（2 変量）正規分布に従うと仮定したデルタ法。平均・分散・共分散だけで決まる
  手法で使える。
- `"bootstrap"`: 各標本の受検者を復元抽出し、ブートストラップ標本ごとに等化して、等化後得点の標準偏差を
  とる。すべての手法で使え、`rng` が必要である。

| 手法（デザイン） | `"analytic"` | `"analytic_normal"` | `"bootstrap"` |
|---|---|---|---|
| identity | 0 | 0 | 0 |
| mean、linear（等価群） | あり | あり | あり |
| mean、linear（単一群） | あり | あり | あり |
| equipercentile（等価群） | あり（Lord） | なし | あり |
| equipercentile（単一群） | なし | なし | あり |
| tucker、levine_observed、levine_true | あり | あり | あり |
| chained_linear | あり | あり | あり |
| braun_holland | あり | なし | あり |
| frequency_estimation | なし | なし | あり |
| chained_equipercentile | なし | なし | あり |

「なし」の組み合わせを指定すると `SpecificationError` になる。

```python
normal_se = fe.equate(x, y, method="linear", standard_error="analytic_normal")
lord_se = fe.equate(x, y, method="equipercentile", standard_error="analytic")
tucker_se = fe.equate(xa, ya, method="tucker", standard_error="analytic")
single_se = fe.equate(xy, method="linear", standard_error="analytic")
```

ブートストラップには `n_replications`（既定 1000）と `rng` を渡す。例では実行を速くするために回数を
減らしている。

```python
boot = fe.equate(
    x, y, method="equipercentile", standard_error="bootstrap", n_replications=200, rng=1
)
boot.see  # ブートストラップ標準誤差
boot.n_replications  # 標準誤差のもとになったブートストラップ標本の数
boot.bootstrap_mean - boot.equated  # 等化関数の偏りの推定値

chained_boot = fe.equate(
    xa,
    ya,
    method="chained_equipercentile",
    standard_error="bootstrap",
    n_replications=200,
    rng=np.random.default_rng(2),
)
```

同時分布では受検者（得点の組）を再抽出するので、2 つの得点の従属性は保たれる。等化できなかった
ブートストラップ標本（たとえば得点に分散がない標本）は除かれ、`SparseDataWarning` が出る。結果の
`n_replications` は実際に使った標本の数である。

3 つの選択肢はどれも、度数を観測値として扱う。事前平滑化した分布を `equate()` に渡した場合、標準誤差は
モデルを当てはめたことを考慮せず、総度数を標本サイズとして扱う。カーネル等化（9 節）の標準誤差は
事前平滑化を考慮する。

## 8. 対数線形モデルによる事前平滑化

`presmooth()` は分布に多項式対数線形モデル（Holland & Thayer, 2000）を当てはめ、当てはめた滑らかな分布を
返す。度数 $n_j$ の 1 つの得点に対し、当てはめた度数を $m_j$ とすると、モデルは次のとおり。

$$
\log m_j = \beta_0 + \sum_{i=1}^{C} \beta_i\, x_j^{\,i} .
$$

当てはめた分布は、観測された分布と総度数および 1 次から $C$ 次までのモーメントが等しい。`degree` が
$C$ である（既定 6）。

```python
smooth_x = fe.presmooth(x, degree=6)
smooth_y = fe.presmooth(y, degree=6)

smooth_x.distribution  # 平滑化後の ScoreDistribution
smooth_x.observed  # 平滑化した元の分布
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

`fit_statistics` には尤度比・Pearson・Freeman–Tukey のカイ二乗とその自由度、AIC が入る。次数を選ぶ
ときは、いくつかのモデルの AIC を比べることが多い。

```python
aic = {degree: fe.presmooth(x, degree=degree).fit_statistics["aic"] for degree in range(2, 8)}
best_degree = min(aic, key=aic.get)  # このデータでは 6
```

平滑化後の分布は `ScoreDistribution` なので、`equate()` に渡せる。

```python
smoothed_equipercentile = fe.equate(
    smooth_x.distribution, smooth_y.distribution, method="equipercentile"
)
```

### 同時分布

`BivariateScoreDistribution` では、`degree` は組 $(C_X, C_Y)$（既定 `(6, 6)`）で、`cross_terms` に
交差項 $x^a y^b$ のべき $(a, b)$ を並べる（既定 `[(1, 1)]`）。

$$
\log m_{jk} = \beta_0 + \sum_{i=1}^{C_X} \beta_{Xi}\, x_j^{\,i}
              + \sum_{i=1}^{C_Y} \beta_{Yi}\, y_k^{\,i}
              + \sum_{(a, b)} \beta_{ab}\, x_j^{\,a} y_k^{\,b} .
$$

このモデルは、2 つの周辺分布の $C_X$ 次・$C_Y$ 次までのモーメントと、交差項に対応する交差モーメント
$E[X^a Y^b]$ を保つ。項 $(1, 1)$ があれば相関が保たれる。`cross_terms` を空にすると、2 つの得点が独立な
モデルになる。

```python
xa_fit = fe.presmooth(xa, degree=(4, 3), cross_terms=[(1, 1)])
ya_fit = fe.presmooth(ya, degree=(4, 3), cross_terms=[(1, 1)])
xa_fit.terms  # ('x^1', 'x^2', 'x^3', 'x^4', 'y^1', 'y^2', 'y^3', 'x^1*y^1')
xy_fit = fe.presmooth(xy, degree=(4, 4))

# 事前平滑化した同時分布で頻度推定法と連鎖等化を行う:
smoothed_fe = fe.equate(xa_fit.distribution, ya_fit.distribution, method="frequency_estimation")
smoothed_chained = fe.equate(
    xa_fit.distribution, ya_fit.distribution, method="chained_equipercentile"
)
```

とりうる得点の数に対して高すぎる次数を指定すると `SpecificationError` になる。`max_iterations`（既定
100）回で収束しなかったときは `ConvergenceWarning` が出て、`converged` が `False` になる。

## 9. カーネル等化

`kernel_equate()` は von Davier, Holland & Thayer (2004) のカーネル法である。離散分布をバンド幅 $h$ の
カーネルで、平均と分散を保ったまま連続化し、2 つの連続な分布関数を通じて X 版を Y 版に等化する。

$$
e_Y(x) = G_{h_Y}^{-1}\bigl(F_{h_X}(x)\bigr) .
$$

`presmooth()` の結果（`.distribution` ではなく `LoglinearResult` そのもの）を渡すと、標準誤差が当てはめた
モデルを考慮したものになる。分布をそのまま渡すこともでき、その場合は観測された分布として扱う。

```python
kernel = fe.kernel_equate(smooth_x, smooth_y)
print(kernel)
# KernelEquatingResult(design='equivalent_groups', kernel='gaussian', bandwidth_x=0.6253, bandwidth_y=0.6174, n_scores=41)

kernel.table.head()  # score, equated, see（等化の標準誤差）
kernel.bandwidth_x, kernel.bandwidth_y
kernel.transform([19.5, 20.0])
kernel.x_presmoothed, kernel.y_presmoothed  # True, True

unsmoothed = fe.kernel_equate(x, y)  # 観測された分布
```

`equate()` と違い、`kernel_equate()` は常に標準誤差（`see`）を返す。

### バンド幅

既定では、各バンド幅は von Davier et al. (2004) のペナルティを最小にする値である。ペナルティには 2 つの
項がある。第 1 項は、とりうる得点での連続化した密度を得点の確率に近づける。第 2 項（重みは
`penalty_weight`、既定 1）は、密度がそのまわりで U 字形になる得点を数える。`penalty_weight=0` で第 2 項を
外せる。`penalty_bandwidth()` は 1 つの分布のバンド幅だけを求める。

```python
fe.penalty_bandwidth(smooth_x)  # kernel.bandwidth_x と同じ値
first_term_only = fe.kernel_equate(smooth_x, smooth_y, penalty_weight=0.0)

# バンド幅を自分で指定する:
fixed = fe.kernel_equate(smooth_x, smooth_y, bandwidth_x=1.0, bandwidth_y=1.0)
```

`bandwidth_method` で、指定しなかったバンド幅の選び方を変えられる。

| `bandwidth_method` | 選び方 | カーネル |
|---|---|---|
| `"penalty"`（既定） | 上のペナルティを最小にする | すべて |
| `"rule_of_thumb"` | $h = 9\sigma / \sqrt{100 N^{2/5} - 81}$（Andersson & von Davier, 2014） | ガウス |
| `"double_smoothing"` | Häggström & Wiberg (2014) の二重平滑化の基準を最小にする | ガウス |
| `"cross_validation"` | R `kequate` の 1 個抜き基準を最小にする | ガウス |

```python
rule = fe.kernel_equate(smooth_x, smooth_y, bandwidth_method="rule_of_thumb")
double = fe.kernel_equate(smooth_x, smooth_y, bandwidth_method="double_smoothing")
cross = fe.kernel_equate(smooth_x, smooth_y, bandwidth_method="cross_validation")
rule.bandwidth_x, double.bandwidth_x, cross.bandwidth_x
```

`"rule_of_thumb"` はカウンターバランスデザインでは使えない。標準誤差は、どの選び方でも、選ばれた
バンド幅を固定値として扱う。

### カーネル

`kernel` は `"gaussian"`（既定）、`"logistic"`（標準ロジスティック分布）、`"uniform"`（$(-1/2, 1/2)$ 上の
一様分布）のいずれかである（Lee & von Davier, 2011）。

```python
logistic = fe.kernel_equate(smooth_x, smooth_y, kernel="logistic")
uniform = fe.kernel_equate(smooth_x, smooth_y, kernel="uniform")
```

一様カーネルでは、連続化した密度が台の外で 0 になり、バンド幅が得点の刻み幅より小さいときはとりうる得点の
間でも 0 になる。等化後の得点で Y 版の密度が 0 になるところでは、`see` は `nan` になる。

### 線形等化と 2 つの等化関数の差

`linear=True` はとても大きいバンド幅（標準偏差の 1000 倍）を使う。これでそのデザインの線形等化関数と
その標準誤差が得られる。バンド幅の指定や一様カーネルとは併用できない。

`seed()` は、**同じ入力から**計算した 2 つの等化関数を比べ、その差と、差の標準誤差（SEED）を返す。差が
標準誤差に比べて小さければ、単純なほうの関数で足りるということである。

```python
kernel_linear = fe.kernel_equate(smooth_x, smooth_y, linear=True)
kernel.seed(kernel_linear).head()  # score, difference（カーネル − 線形）, seed
```

### 診断

`percent_relative_error` は、等化後得点の 1 次から 10 次のモーメントを Y 版のモーメントと比べた相対誤差
（パーセント）である。`continuized` は、各版のとりうる得点での連続化した分布関数と密度を返す。

```python
kernel.percent_relative_error  # 添字はモーメントの次数 1..10
kernel.continuized.head()  # form, score, probability, cdf, density
```

### 他のデザイン

`kernel_equate()` は 5 つのデザインを扱う。1 変量の入力が 2 つなら等価群、同時分布が 1 つなら単一群で
ある。同時分布が 2 つのときは、デザインを指定しなければならない。

| `design` | 入力 |
|---|---|
| `"equivalent_groups"` | `x`: X 版、`y`: Y 版。独立な 2 つの標本 |
| `"single_group"` | `x`: 1 つの標本での (X, Y) の同時分布 |
| `"counterbalanced"` | `x`: X を先に受けた標本での (X, Y) の同時分布、`y`: Y を先に受けた標本での同じもの |
| `"chained"` | `x`: (X, アンカー) の同時分布、`y`: (Y, アンカー) の同時分布 |
| `"post_stratification"` | `"chained"` と同じ入力 |

```python
single_kernel = fe.kernel_equate(xy_fit)  # 単一群

chained_kernel = fe.kernel_equate(xa_fit, ya_fit, design="chained")
post_kernel = fe.kernel_equate(xa_fit, ya_fit, design="post_stratification")
post_kernel.synthetic_weight  # X を受けた母集団の重み。synthetic_weight= で指定できる

chained_kernel.anchor_distributions  # 2 つの母集団でのアンカーの分布
chained_kernel.anchor_bandwidths  # そのバンド幅。anchor_bandwidths= で指定できる
chained_kernel.chain_percent_relative_error.head()  # 列は x_to_anchor, anchor_to_y

# 連鎖と事後層化、カーネルと線形を比べる:
chained_kernel.seed(post_kernel).head()
post_linear = fe.kernel_equate(xa_fit, ya_fit, design="post_stratification", linear=True)
post_kernel.seed(post_linear).head()
```

連鎖等化にはリンクが 2 つ（X からアンカー、アンカーから Y）あるので、相対誤差は
`chain_percent_relative_error` で見る。連鎖等化で `percent_relative_error` を使うと `SpecificationError` に
なる。事後層化では、観測されたアンカー得点がすべて両方の母集団にある必要がある。事前平滑化した同時分布なら
この条件を満たす。満たさないときは `SpecificationError` になる。

カウンターバランスデザインでは、どちらの標本も両方の版を、逆の順序で受ける。X と Y の得点の確率は
2 つの標本の重みつき平均で、`counterbalance_weights=(w_X, w_Y)` は X を先に受けた標本の重みである
（既定 `(0.5, 0.5)`）。

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
# 各版を、その版を先に受けた標本だけから求める:
first_only = fe.kernel_equate(
    x_first_fit, y_first_fit, design="counterbalanced", counterbalance_weights=(1.0, 0.0)
)
```

## 10. エラーと警告

例外と警告のクラスは `flexpyequate.errors` にある。

| クラス | 発生する場面 |
|---|---|
| `ScoreDistributionError` | 得点や度数が正しい分布にならない。得点が等間隔でない、度数が負、観測された得点がとりうる得点でない、観測が 1 つもない |
| `SpecificationError` | 引数どうし、または引数とデータが合わない。デザインに合わない手法、未知の選択肢、`anchor` や `rng` の指定漏れ、高すぎる次数、存在しない解析的な標準誤差 |
| `SparseDataWarning` | 計算の一部を、使えるデータだけで行った。一方の母集団でしか観測されなかったアンカー得点、等化できなかったブートストラップ標本 |
| `ConvergenceWarning` | 事前平滑化が収束する前に止まった |

エラーはすべて `FlexpyequateError` を、警告はすべて `FlexpyequateWarning` を継承する。2 つのエラー
クラスは `ValueError` でもある。

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

データが疎なときの警告の小さな例を示す。第 2 の母集団にはアンカーで 0 点を取った人がいない。

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

## 11. R パッケージとの違い

flexpyequate は R `equate`・`kequate`・`SNSequate` と照合しているが、これらのパッケージが公刊された式と
異なるところでは、公刊された式に従う。R の結果を再現するには次のようにする。

- **分散。** R `equate` は分散を $N - 1$ で割る。flexpyequate の既定は Kolen & Brennan の母集団形である。
  `ddof=1` を指定すると `equate` の線形等化と一致する。
- **平均等化。** R `equate` の `type = "mean"` は得点に 2 つの得点範囲の比を掛ける。flexpyequate の
  平均等化は常に傾き 1 である。得点範囲が同じ版どうしでは両者は一致する。
- **パーセンタイル順位 0 と 100。** X 版の得点のパーセンタイル順位がちょうど 0 または 100 のとき、
  flexpyequate は Kolen & Brennan の定義どおり Y 版の上側・下側パーセンタイルの平均を返す。`equate` は
  Y 版の得点範囲の端を返す。両者が異なるのは、Y 版の最低点（または最高点）付近を取った受検者がいない
  ときだけである。
- **合成母集団の重み。** Braun–Holland 法と頻度推定法で、R `equate` は 2 つの群を度数のまま混ぜる。
  そのため標本サイズが異なると、第 1 群の重みが $w$ でなく $wN_1 / (wN_1 + (1 - w)N_2)$ になる。
  flexpyequate は $w$ そのものを使う。`equate` を再現するには、その実質的な重みを `synthetic_weight` に
  渡す。
- **カーネル等化の分散。** R `kequate` は連続化に使う分散に $N / (N - 1)$ を掛ける。flexpyequate は
  von Davier, Holland & Thayer (2004) および `SNSequate` と同じく、得点分布そのものの分散を使う。
  等化後得点の差は標本が大きいほど小さくなる。
- **カウンターバランスデザイン。** R `kequate` の重みは 1 つで、その標準誤差が等化関数と対応するのは
  重みが 1/2 のときだけである。flexpyequate は重みを 2 つ持ち（`counterbalance_weights`）、標準誤差は
  どの重みでも成り立つ。
- **ペナルティ。** `kernel_equate()` はペナルティの 2 つの項を両方使ってバンド幅を選ぶ
  （`penalty_weight=1`）。`kequate` の既定は第 1 項のみである（`penalty_weight=0` で再現できる）。

## 参考文献

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
