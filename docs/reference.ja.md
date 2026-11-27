# API リファレンス

[English](reference.md) | 日本語

flexpyequate の公開 API（`from flexpyequate import ...` で使えるもの）の一覧。使い方の流れは
[ユーザーガイド](guide.ja.md) を参照。各関数の docstring にも同じ内容と、対応する式・出典がある
（`help(flexpyequate.equate)` など）。

公開関数の引数は、最初の 1〜2 個を除いてキーワード専用（`*` の後ろ）。ライブラリが返す配列は `float64` の
`numpy.ndarray` で、分布や結果が保持している配列は書き込み不可である。

- 得点分布: [`ScoreDistribution`](#scoredistribution), [`BivariateScoreDistribution`](#bivariatescoredistribution)
- 等化: [`equate`](#equate), [`EquatingResult`](#equatingresult)
- 事前平滑化: [`presmooth`](#presmooth), [`LoglinearResult`](#loglinearresult)
- カーネル等化: [`kernel_equate`](#kernel_equate), [`KernelEquatingResult`](#kernelequatingresult), [`penalty_bandwidth`](#penalty_bandwidth)
- 例外と警告: [`flexpyequate.errors`](#flexpyequateerrors)
- バージョン: [`__version__`](#__version__)

---

## 得点分布

### `ScoreDistribution`

```text
ScoreDistribution(scores, frequencies)
ScoreDistribution.from_frequencies(*, scores, frequencies) -> ScoreDistribution
ScoreDistribution.from_scores(values, *, scores=None, score_range=None, increment=1.0) -> ScoreDistribution
```

1 つのテスト版の、とりうる得点ごとの度数。パーセンタイル順位とパーセンタイルの関数は Kolen & Brennan
(2014, 2 章) に従う。

| 引数 | 型 | 説明 |
|---|---|---|
| `scores` | 形 `(n_scores,)` の配列 | とりうる得点。2 つ以上で、狭義に増加し、等間隔であること。誰も取らなかった得点も度数 0 で含める |
| `frequencies` | 形 `(n_scores,)` の配列 | とりうる得点ごとの非負の度数。整数でなくてよい（事前平滑化した分布） |

**`from_frequencies`** は度数表から分布を作る（`scores` は `range(41)` などの反復可能オブジェクトでよい）。

**`from_scores`** は受検者ごとの観測得点を集計する。

| 引数 | 型 | 説明 |
|---|---|---|
| `values` | 形 `(n_examinees,)` の配列 | 観測得点。欠測値は扱えないので、先に除いておく |
| `scores` | 配列、省略可 | とりうる得点。これか `score_range` の一方だけを指定する |
| `score_range` | `(low, high)`、省略可 | 最低点と最高点。とりうる得点は `increment` 間隔になる。`scores` も `score_range` も指定しないと、観測された範囲を使う |
| `increment` | float、既定 `1.0` | `scores` を指定しないときの、とりうる得点の間隔 |

**例外**: `ScoreDistributionError`。得点が等間隔でない・増加していない、度数が負または有限でない、度数が
すべて 0、得点範囲が刻み幅の倍数でない、（`from_scores`）観測得点がとりうる得点でない場合。

| 属性 | 型 | 説明 |
|---|---|---|
| `scores` | 配列 | とりうる得点 |
| `frequencies` | 配列 | とりうる得点ごとの度数 |
| `n_scores` | int | とりうる得点の数 |
| `increment` | float | 隣り合うとりうる得点の間隔 $\delta$ |
| `n` | float | 総度数（標本サイズ） |
| `probabilities` | 配列 | とりうる得点ごとの相対度数 |
| `cumulative` | 配列 | とりうる得点ごとの累積割合 $F(x_j)$ |
| `mean` | float | 平均 |
| `skewness` | float | 歪度（母集団形） |
| `kurtosis` | float | 尖度（母集団形。正規分布で 3） |

| メソッド | 戻り値 | 説明 |
|---|---|---|
| `variance(*, ddof=0)` | float | 分散。`ddof=0` は Kolen & Brennan と同じ母集団形（$N$ で割る）、`ddof=1` は R `equate` と同じ標本形（$N - 1$ で割る）。それ以外の値は `ScoreDistributionError` |
| `sd(*, ddof=0)` | float | 標準偏差（`variance` の平方根） |
| `percentile_rank(values)` | 配列 | 得点のパーセンタイル順位（0〜100）。とりうる得点の間の値でもよい |
| `percentile(ranks)` | 配列 | パーセンタイル順位（0〜100）に対応する得点。`percentile_rank` の逆関数。0〜100 の外の順位は `ScoreDistributionError` |
| `to_frame()` | `pandas.DataFrame` | とりうる得点ごとに 1 行: `score`, `frequency`, `probability`, `cumulative`, `percentile_rank` |

とりうる得点 $x_j$ は $[x_j - \delta/2,\ x_j + \delta/2)$ 上で一様とみなす。$x$ に最も近いとりうる得点を
$x^*$ とすると、

$$
P(x) = 100\Bigl\{F(x^* - \delta) + \frac{x - (x^* - \delta/2)}{\delta}
       \bigl[F(x^*) - F(x^* - \delta)\bigr]\Bigr\}
$$

であり、$x_1 - \delta/2$ より下では 0、$x_J + \delta/2$ 以上では 100 になる。`percentile` は Kolen &
Brennan の上側・下側パーセンタイルの平均を返す。両者が異なるのは、度数 0 のために $F$ が平らなところ
だけである。値は $x_1 - \delta/2$ から $x_J + \delta/2$ の間になる。

**照合先**: R `equate`（パーセンタイル順位は `equate::px`）。

### `BivariateScoreDistribution`

```text
BivariateScoreDistribution(x_scores, y_scores, frequencies)
BivariateScoreDistribution.from_frequencies(*, x_scores, y_scores, frequencies) -> BivariateScoreDistribution
BivariateScoreDistribution.from_scores(x_values, y_values, *, x_scores=None, y_scores=None,
    x_range=None, y_range=None, x_increment=1.0, y_increment=1.0) -> BivariateScoreDistribution
```

同じ受検者の 2 つの得点の同時度数。単一群での X 版と Y 版、またはアンカーテストを使うデザインでの
1 つの版（第 1 変数）とアンカー（第 2 変数）を表す。

| 引数 | 型 | 説明 |
|---|---|---|
| `x_scores` | 形 `(n_x_scores,)` の配列 | 第 1 変数のとりうる得点。等間隔で増加すること |
| `y_scores` | 形 `(n_y_scores,)` の配列 | 第 2 変数のとりうる得点 |
| `frequencies` | 形 `(n_x_scores, n_y_scores)` の配列 | 非負の同時度数。行が第 1 変数、列が第 2 変数の得点 |

**`from_frequencies`** は 2 元の度数表から同時分布を作る。

**`from_scores`** は対になった観測得点（受検者ごとに 1 組）をクロス集計する。

| 引数 | 型 | 説明 |
|---|---|---|
| `x_values`、`y_values` | 形 `(n_examinees,)` の配列 | 2 つの変数の観測得点。受検者の順序をそろえる |
| `x_scores`、`y_scores` | 配列、省略可 | 各変数のとりうる得点 |
| `x_range`、`y_range` | `(low, high)`、省略可 | 各変数の最低点と最高点。とりうる得点を指定しないときに使う。どちらも指定しないと、観測された範囲を使う |
| `x_increment`、`y_increment` | float、既定 `1.0` | とりうる得点を明示しないときの間隔 |

**例外**: `ScoreDistributionError`。得点や度数が正しくない、度数がすべて 0、`from_scores` の 2 つの配列の
長さが違う、観測得点がとりうる得点でない場合。

| 属性 | 型 | 説明 |
|---|---|---|
| `x_scores`、`y_scores` | 配列 | 2 つの変数のとりうる得点 |
| `frequencies` | 配列 | 同時度数。形は `(n_x_scores, n_y_scores)` |
| `n` | float | 総度数（受検者数） |
| `probabilities` | 配列 | 同時相対度数 |
| `x`、`y` | `ScoreDistribution` | 第 1 変数・第 2 変数の周辺分布 |
| `correlation` | float | 2 つの得点の Pearson の相関係数 |

| メソッド | 戻り値 | 説明 |
|---|---|---|
| `covariance(*, ddof=0)` | float | 2 つの得点の共分散（`ddof=0` は母集団形、`ddof=1` は標本形） |
| `to_frame()` | `pandas.DataFrame` | 縦持ち。得点の組ごとに 1 行: `x_score`, `y_score`, `frequency`, `probability` |

---

## 等化

### `equate`

```text
equate(x, y=None, *, method="equipercentile", ddof=0, synthetic_weight=None, anchor=None,
       standard_error=None, n_replications=1000, rng=None) -> EquatingResult
```

得点分布から、X 版を Y 版の尺度に等化する（Kolen & Brennan, 2014）。データ収集デザインは入力から
決まる。

- `ScoreDistribution` が 2 つ: 等価群。
- `BivariateScoreDistribution` が 1 つ: 単一群。その 2 つの周辺分布を等化する。
- `BivariateScoreDistribution` が 2 つ: アンカーテストつき非等価群。1 つめは X 版を受けた母集団での
  X 版とアンカー、2 つめは Y 版を受けた母集団での Y 版とアンカー。どちらもアンカーが第 2 変数である。

| 引数 | 型 | 説明 |
|---|---|---|
| `x` | `ScoreDistribution` / `BivariateScoreDistribution` | X 版の分布（等価群）、X 版と Y 版の同時分布（単一群）、または X 版とアンカーの同時分布（非等価群） |
| `y` | `ScoreDistribution` / `BivariateScoreDistribution`、省略可 | 独立で等価な群による Y 版の分布、またはもう一方の母集団での Y 版とアンカーの同時分布。単一群では省略する |
| `method` | str、既定 `"equipercentile"` | 等価群と単一群では `"identity"`、`"mean"`、`"linear"`、`"equipercentile"`。非等価群では `"tucker"`、`"levine_observed"`、`"levine_true"`、`"braun_holland"`、`"chained_linear"`、`"frequency_estimation"`、`"chained_equipercentile"` |
| `ddof` | `0` / `1`、既定 `0` | 線形の手法で使う分散・共分散の自由度の補正。0 は Kolen & Brennan と同じ母集団形、1 は R `equate` と同じ標本形。Braun–Holland 法は常に合成分布のモーメントを使う |
| `synthetic_weight` | float、省略可 | X 版を受けた母集団の重み $w_1$（0 以上 1 以下）。Tucker 法、Levine の観測得点法、Braun–Holland 法、頻度推定法で使う。既定は標本サイズに比例する $w_1 = N_1 / (N_1 + N_2)$。ほかの手法では無視される |
| `anchor` | `"internal"` / `"external"`、省略可 | Levine の方法で必須。アンカー項目が合計得点に含まれるなら `"internal"`、アンカーを別に採点するなら `"external"`。ほかの手法では無視される |
| `standard_error` | `"analytic"` / `"analytic_normal"` / `"bootstrap"`、省略可 | X 版のとりうる得点での等化の標準誤差を求める。既定では求めない |
| `n_replications` | int、既定 `1000` | ブートストラップ標本の数（2 以上） |
| `rng` | `numpy.random.Generator` / int、省略可 | 乱数生成器、または非負の整数のシード。ブートストラップで必須。それ以外では無視される |

**等価群と単一群の手法。** $P$ は X のパーセンタイル順位関数（割合）、$Q^{-1}$ は Y のパーセンタイル
関数。

| `method` | 等化関数 |
|---|---|
| `"identity"` | $e_Y(x) = x$ |
| `"mean"` | $e_Y(x) = x - \mu_X + \mu_Y$ |
| `"linear"` | $e_Y(x) = \dfrac{\sigma_Y}{\sigma_X}(x - \mu_X) + \mu_Y$ |
| `"equipercentile"` | $e_Y(x) = Q^{-1}(P(x))$ |

**アンカーテストつき非等価群の手法。** 母集団 1 が X とアンカー V を、母集団 2 が Y と V を受ける。
`"tucker"`、`"levine_observed"`、`"braun_holland"` は、重み $w_1$ と $w_2 = 1 - w_1$ の合成母集団で
線形等化を行う。

$$
l_Y(x) = \frac{\sigma_s(Y)}{\sigma_s(X)}\,[x - \mu_s(X)] + \mu_s(Y) .
$$

Tucker 法と Levine の観測得点法では、合成母集団のモーメントは次のとおり。

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

$\gamma_1$ は次の表のとおり（$\gamma_2$ は母集団 2 の Y と V から同じように求める）。

| 手法 | $\gamma_1$ |
|---|---|
| Tucker | $\sigma_1(X, V) / \sigma_1^2(V)$ |
| Levine、内部アンカー | $\sigma_1^2(X) / \sigma_1(X, V)$ |
| Levine、外部アンカー | $[\sigma_1^2(X) + \sigma_1(X, V)] / [\sigma_1^2(V) + \sigma_1(X, V)]$ |

Braun–Holland 法は、頻度推定法の分布 $f_s(x) = w_1 f_1(x) + w_2 \sum_v f_1(x \mid v) h_2(v)$ と
$g_s(y) = w_1 \sum_v g_2(y \mid v) h_1(v) + w_2 g_2(y)$ から合成母集団の平均と標準偏差を求める。
そのほかの手法は次のとおり。

| `method` | 等化関数 |
|---|---|
| `"levine_true"` | $l_Y(x) = \dfrac{\gamma_2}{\gamma_1}[x - \mu_1(X)] + \mu_2(Y) + \gamma_2 [\mu_1(V) - \mu_2(V)]$ |
| `"chained_linear"` | $l_Y(x) = \mu_2(Y) + \dfrac{\sigma_2(Y)}{\sigma_2(V)} \Bigl[\mu_1(V) + \dfrac{\sigma_1(V)}{\sigma_1(X)}(x - \mu_1(X)) - \mu_2(V)\Bigr]$ |
| `"frequency_estimation"` | $e_Y(x) = Q_s^{-1}(P_s(x))$。$f_s$ と $g_s$ のパーセンタイル順位関数を使う |
| `"chained_equipercentile"` | $e_Y(x) = Q_2^{-1}\bigl(H_2(H_1^{-1}(P_1(x)))\bigr)$。母集団 1 で X をアンカーに、母集団 2 でアンカーを Y に等化する |

等パーセンタイルの手法を平滑化するには、事前平滑化した同時分布（[`presmooth`](#presmooth)）を渡す。

**標準誤差**（`standard_error`）:

- `"analytic"`: 分布を仮定しないデルタ法。線形の手法は標本の平均・分散・共分散の関数であり、それらの
  標本共分散には観測された分布の 3 次・4 次の中心モーメントを使う（Kolen, 1985; Zu & Yuan, 2012）。
  等価群の線形等化では Braun & Holland (1982) の式になる。Braun–Holland 法は 2 つの同時分布のセル確率で
  微分する。等価群の等パーセンタイル等化は Lord (1982) の式を使う。
- `"analytic_normal"`: 同じ方法で、モーメントの標本共分散を（2 変量）正規分布のもとでの値にする。
  モーメントだけで決まる手法で使える。
- `"bootstrap"`: 各標本から $N$ 人を復元抽出し（同時分布ではセルを再抽出するので、2 つの得点の従属性は
  保たれる）、`n_replications` 個の標本をそれぞれ等化して、等化後得点の標準偏差（$B - 1$ で割る）をとる。

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

解析的な式に入れる分散・共分散は `ddof` に従い、3 次・4 次のモーメントは常に $N$ で割る。3 つの選択肢は
どれも度数を観測値として扱う。事前平滑化した分布では、モデルを当てはめたことを考慮せず（ブートストラップは
平滑化後の分布から抽出し、当てはめ直さない）、総度数を標本サイズとして扱う。

**戻り値**: [`EquatingResult`](#equatingresult)

**例外**: `SpecificationError`。入力が対応するデザインに合わない、手法がデザインに属さない、必要な引数が
ない、手法が割り算に使う分散や共分散が正でない、指定した解析的な標準誤差がその手法にない、`rng` なしで
ブートストラップを指定した場合。

**警告**: `SparseDataWarning`。Braun–Holland 法と頻度推定法で、一方の母集団でしか観測されなかった
アンカー得点があるとき。ブートストラップで、等化できずに除かれた標本があるとき。

**照合先**: R `equate::equate` の `type = "mean"`、`"linear"`、`"equipercentile"`。アンカーテストでは
`method = "tucker"`、`"levine"`、`"braun/holland"`、`"chained"`、`"frequency estimation"`。`equate` に
解析的な標準誤差があるもの（等価群の線形等化と等パーセンタイル等化、Tucker、Levine の観測得点法、
連鎖線形）はその値。ブートストラップは `equate::bootstrap`（2 つのモンテカルロ推定値の統計的な比較）。
等パーセンタイル等化、アンカーテストを使う手法、解析的な標準誤差は、公刊された式の独立した R 実装とも
照合している。

### `EquatingResult`

X 版から Y 版の尺度への等化関数。[`equate`](#equate) が返す。

| 属性 | 型 | 説明 |
|---|---|---|
| `method` | str | `equate` に渡した等化手法 |
| `design` | str | `"equivalent_groups"`、`"single_group"`、`"nonequivalent_groups"` のいずれか |
| `x`、`y` | `ScoreDistribution` | 等化した X 版と Y 版の分布。単一群では周辺分布。非等価群では、X 版を受けた母集団での X 版と、Y 版を受けた母集団での Y 版。頻度推定法では合成母集団での X と Y の分布（総度数は $N_1 + N_2$） |
| `scores` | 配列 | X 版のとりうる得点 |
| `equated` | 配列 | X 版のとりうる得点に対応する Y 版の値 $e_Y(x_j)$ |
| `slope`、`intercept` | float / `None` | 線形の手法（identity と mean を含む）での $e_Y(x) = \mathrm{intercept} + \mathrm{slope}\,x$ の係数。等パーセンタイルの手法では `None` |
| `ddof` | int | 線形の手法の分散・共分散に使った自由度の補正 |
| `synthetic_weight` | float / `None` | X 版を受けた母集団の重み $w_1$（Tucker 法、Levine の観測得点法、Braun–Holland 法、頻度推定法） |
| `anchor` | str / `None` | Levine の方法での `"internal"` または `"external"` |
| `gamma` | `(float, float)` / `None` | Tucker 法と Levine の方法の $(\gamma_1, \gamma_2)$ |
| `synthetic_moments` | `pandas.DataFrame` / `None` | 合成母集団での X と Y の平均と標準偏差（行 `x`・`y`、列 `mean`・`sd`）。Tucker 法、Levine の観測得点法、Braun–Holland 法、頻度推定法 |
| `anchor_distributions` | `ScoreDistribution` の組 / `None` | 連鎖等パーセンタイル等化: X を受けた母集団と Y を受けた母集団でのアンカーの分布 |
| `see` | 配列 / `None` | `standard_error` を指定したときの、X 版のとりうる得点ごとの等化の標準誤差 |
| `standard_error` | str / `None` | `see` の求め方: `"analytic"`、`"analytic_normal"`、`"bootstrap"` |
| `n_replications` | int / `None` | ブートストラップ: `see` のもとになった標本の数（等化できなかった標本は除く） |
| `bootstrap_mean` | 配列 / `None` | ブートストラップ: 標本にわたる等化後得点の平均。`equated` との差が等化関数の偏りの推定値になる |

| メンバー | 戻り値 | 説明 |
|---|---|---|
| `table`（プロパティ） | `pandas.DataFrame` | 換算表: `score`（X 版）と `equated`（Y 版での対応値）。標準誤差を求めたときは `see` も |
| `moments`（プロパティ） | `pandas.DataFrame` | 行 `x`・`y`・`equated`、列 `mean`・`sd`・`skewness`・`kurtosis`（母集団形）。`equated` の行は $e_Y(X)$ のモーメントで、$e_Y(X)$ は $x_j$ の相対度数で値 $e_Y(x_j)$ をとる |
| `transform(values)` | 配列 | X 版の任意の得点（とりうる得点の間の値でもよい）に対応する Y 版の値。形は `values` と同じ |

---

## 事前平滑化

### `presmooth`

```text
presmooth(distribution, *, degree=None, cross_terms=((1, 1),), max_iterations=100,
          tolerance=1e-12) -> LoglinearResult
```

多項式対数線形モデル（Holland & Thayer, 2000）で得点分布を事前平滑化する。最尤法（ニュートン法）で
当てはめる。度数 $n_j$ の 1 つの得点では

$$
\log m_j = \beta_0 + \sum_{i=1}^{C} \beta_i\, x_j^{\,i},
$$

2 つの得点の同時分布では

$$
\log m_{jk} = \beta_0 + \sum_{i=1}^{C_X} \beta_{Xi}\, x_j^{\,i}
              + \sum_{i=1}^{C_Y} \beta_{Yi}\, y_k^{\,i}
              + \sum_{(a, b)} \beta_{ab}\, x_j^{\,a} y_k^{\,b} .
$$

当てはめた分布は、観測された分布と総度数および 1 次から $C$ 次までのモーメントが等しい。2 変量のモデルは、
入れた交差項に対応する交差モーメント $E[X^a Y^b]$ も保つ。

| 引数 | 型 | 説明 |
|---|---|---|
| `distribution` | `ScoreDistribution` / `BivariateScoreDistribution` | 観測された分布 |
| `degree` | int / `(int, int)`、省略可 | 1 つの得点では多項式の次数 $C$（既定 6）、同時分布では $(C_X, C_Y)$（既定 `(6, 6)`）。R `equate` の `degrees`、`glm` の式の多項式の次数にあたる |
| `cross_terms` | `(int, int)` の列、既定 `((1, 1),)` | 同時分布のみ: 交差項 $x^a y^b$ のべき $(a, b)$。空の列にすると 2 つの得点が独立なモデルになる |
| `max_iterations` | int、既定 `100` | ニュートン法の最大反復回数 |
| `tolerance` | float、既定 `1e-12` | スコア方程式の収束判定の許容誤差（直交化した項の、観測モーメントと当てはめたモーメントの差。割合で測る） |

**戻り値**: [`LoglinearResult`](#loglinearresult)

**例外**: `SpecificationError`。次数が正の整数でない、とりうる得点の数に対して高すぎる（1 つの得点では
`n_scores - 2` まで）、交差項が正しくない、モデルのパラメータ数がセルの数に達する場合。

**警告**: `ConvergenceWarning`。ニュートン法が `max_iterations` 回で収束しないとき。

**照合先**: R `stats::glm(family = poisson)`、`equate::presmoothing(smoothmethod = "loglinear")`。

### `LoglinearResult`

当てはめた多項式対数線形モデル。[`presmooth`](#presmooth) が返す。

| 属性 | 型 | 説明 |
|---|---|---|
| `distribution` | `ScoreDistribution` / `BivariateScoreDistribution` | 事前平滑化した分布。同じとりうる得点の上の、当てはめた度数。総度数は観測された総度数に等しい |
| `observed` | `ScoreDistribution` / `BivariateScoreDistribution` | 平滑化した元の分布 |
| `terms` | str のタプル | 多項式の項の名前。例: `("x^1", "x^2")`、`("x^1", "y^1", "x^1*y^1")` |
| `design_matrix` | 形 `(n_cells, n_terms)` の配列 | 各セルでの多項式の項の値（切片の列はない）。べきをとる前に得点を $[-1, 1]$ に変換している。これはモデルも当てはめの結果も変えない。同時分布ではセルは行優先の順（X が遅く変わる） |
| `log_likelihood` | float | 当てはめた度数でのポアソン対数尤度 $\sum_j [n_j \log m_j - m_j - \log n_j!]$ |
| `n_iterations` | int | ニュートン法の反復回数 |
| `converged` | bool | スコア方程式が指定した許容誤差まで解けたか |
| `n_parameters` | int | 自由パラメータの数（多項式の項と切片） |
| `degrees_of_freedom` | int | 残差の自由度（セルの数からパラメータ数を引いたもの） |

| プロパティ | 戻り値 | 説明 |
|---|---|---|
| `fit_statistics` | `pandas.Series` | `likelihood_ratio`, `pearson`, `freeman_tukey`, `degrees_of_freedom`, `n_parameters`, `log_likelihood`, `aic` |
| `c_matrix` | 形 `(n_cells, n_terms)` の配列 | 当てはめた確率の C 行列（Holland & Thayer, 1987）。$\operatorname{Cov}(\hat r) \approx C C^\top / N$。カーネル等化が標準誤差に使う。$C C^\top$ が同じ行列ならどれでも同じ役割を果たし、列そのものは一意でない |

観測度数を $n_j$、当てはめた度数を $m_j$、ポアソン対数尤度を $\ell$、パラメータ数を $p$ とすると、
適合度の統計量は次のとおり。

$$
\begin{aligned}
G^2 &= 2 \sum_j n_j \log(n_j / m_j) \\
\chi^2_{\mathrm{Pearson}} &= \sum_j (n_j - m_j)^2 / m_j \\
\chi^2_{\mathrm{FT}} &= \sum_j \bigl(\sqrt{n_j} + \sqrt{n_j + 1} - \sqrt{4 m_j + 1}\bigr)^2 \\
\mathrm{AIC} &= -2 \ell + 2 p .
\end{aligned}
$$

`aic` は、同じポアソンモデルに対する R `glm` の AIC に等しい。

---

## カーネル等化

### `kernel_equate`

```text
kernel_equate(x, y=None, *, design=None, bandwidth_x=None, bandwidth_y=None,
              anchor_bandwidths=None, penalty_weight=1.0, linear=False, synthetic_weight=None,
              counterbalance_weights=(0.5, 0.5), kernel="gaussian",
              bandwidth_method="penalty") -> KernelEquatingResult
```

X 版を Y 版にカーネル等化する（von Davier, Holland & Thayer, 2004; Lee & von Davier, 2011）。得点の確率が
$r_j$（X）と $s_k$（Y）の離散分布を連続化する。

$$
F_{h_X}(x) = \sum_j r_j\, K\!\left(\frac{x - a_X x_j - (1 - a_X)\mu_X}{a_X h_X}\right),
\qquad a_X^2 = \frac{\sigma_X^2}{\sigma_X^2 + \sigma_V^2 h_X^2},
$$

$G_{h_Y}$ も同様である。$K$ はカーネルの分布関数、$\sigma_V^2$ はその分散。連続化した変数は、離散分布の
平均と分散を保つ。等化関数は

$$
e_Y(x) = G_{h_Y}^{-1}\bigl(F_{h_X}(x)\bigr) .
$$

| 引数 | 型 | 説明 |
|---|---|---|
| `x` | `ScoreDistribution` / `BivariateScoreDistribution` / `LoglinearResult` | デザインの 1 つめの入力（後述）。事前平滑化した分布を等化するには [`presmooth`](#presmooth) の結果を渡す。分布をそのまま渡すと、観測された分布として扱う |
| `y` | 同上、省略可 | デザインの 2 つめの入力。単一群では省略する |
| `design` | str、省略可 | `"equivalent_groups"` と `"single_group"` は入力から決まる。同時分布が 2 つのときは必須: `"counterbalanced"`、`"chained"`、`"post_stratification"` |
| `bandwidth_x`、`bandwidth_y` | float、省略可 | バンド幅 $h_X$ と $h_Y$。既定ではそれぞれ `bandwidth_method` で選ぶ |
| `anchor_bandwidths` | `(float または None, float または None)`、省略可 | 連鎖等化: X を受けた母集団と Y を受けた母集団でのアンカーのバンド幅。`None` の要素は `bandwidth_method` で選ぶ |
| `penalty_weight` | float、既定 `1.0` | バンド幅選択のペナルティ第 2 項の重み $K$（[`penalty_bandwidth`](#penalty_bandwidth) を参照） |
| `linear` | bool、既定 `False` | 標準偏差の 1000 倍のバンド幅を使う。そのデザインの線形等化関数（とその標準誤差）が得られる。バンド幅の指定や一様カーネルとは併用できない |
| `synthetic_weight` | float、省略可 | 事後層化: X を受けた母集団の重み $w$（0 以上 1 以下）。既定は $N_P / (N_P + N_Q)$ |
| `counterbalance_weights` | `(float, float)`、既定 `(0.5, 0.5)` | カウンターバランスデザイン: $(w_X, w_Y)$。X を先に受けた標本の、$r$ と $s$ での重み |
| `kernel` | `"gaussian"` / `"logistic"` / `"uniform"`、既定 `"gaussian"` | カーネル。標準正規分布（$\sigma_V^2 = 1$）、標準ロジスティック分布（$\pi^2/3$）、$(-1/2, 1/2)$ 上の一様分布（$1/12$）。一様カーネルでは、連続化した密度が台の外で 0 になり、バンド幅が得点の刻み幅より小さいときはとりうる得点の間でも 0 になる。等化後の得点で Y の密度が 0 のところでは `see` は `nan` |
| `bandwidth_method` | `"penalty"` / `"rule_of_thumb"` / `"double_smoothing"` / `"cross_validation"`、既定 `"penalty"` | 指定しなかったバンド幅の選び方（後述） |

**デザイン。** デザインに応じて、推定した（事前平滑化した、または観測された）確率から $r$ と $s$ が
決まる。

| `design` | 入力 | $r$ と $s$ |
|---|---|---|
| `"equivalent_groups"` | `x`、`y`: 独立な 2 つの標本での X と Y の分布 | それぞれの確率 |
| `"single_group"` | `x`: 1 つの標本での (X, Y) の同時分布 | その 2 つの周辺分布 |
| `"counterbalanced"` | `x`、`y`: X を先に受けた標本と Y を先に受けた標本での (X, Y) の同時分布。周辺分布を $r_1, s_1$ と $r_2, s_2$ とする | $r = w_X r_1 + (1 - w_X) r_2$、$s = w_Y s_1 + (1 - w_Y) s_2$ |
| `"post_stratification"` | `x`: 母集団 P での (X, アンカー) の同時分布、`y`: 母集団 Q での (Y, アンカー) の同時分布 | 合成母集団 $T = wP + (1 - w)Q$ での X と Y の分布。アンカー得点を与えたときの各版の得点分布が P と Q で同じと仮定する |
| `"chained"` | 同じ入力 | $e_Y(x) = G_Q^{-1}\bigl(H_Q(H_P^{-1}(F_P(x)))\bigr)$。P で X をアンカーに、Q でアンカーを Y に等化する。4 つの分布を連続化する |

**バンド幅の選び方**（`bandwidth_method`）。後の 3 つはガウスカーネルで定義されている。

| 値 | 選び方 |
|---|---|
| `"penalty"` | `penalty_weight` を使った [`penalty_bandwidth`](#penalty_bandwidth)。どのカーネルでも使える |
| `"rule_of_thumb"` | $h = 9\sigma / \sqrt{100 N^{2/5} - 81}$（Andersson & von Davier, 2014）。$\sigma$ は連続化する分布の標準偏差、$N$ はその版を受けた標本の大きさ。カウンターバランスデザインでは使えない |
| `"double_smoothing"` | Häggström & Wiberg (2014) の二重平滑化の基準を最小にする。パイロットバンド幅は得点の刻み幅の 4 倍（`kequate` と同じ）で、最小値はそれより小さい範囲で探す |
| `"cross_validation"` | `kequate` の 1 個抜き基準を最小にする。各得点の確率を、ほかの得点の確率のカーネル重みつき平均で予測する。Liang & von Davier (2014) の尤度交差検証ではない |

**等化の標準誤差。** `see` は、各標本の推定確率の共分散からデルタ法（von Davier et al., 2004, 5 章）で
求める。共分散は、事前平滑化した入力では対数線形モデルから導かれるもの、そうでなければ多項分布のもので
ある。選ばれたバンド幅は、どの選び方でも固定値として扱う。

**戻り値**: [`KernelEquatingResult`](#kernelequatingresult)

**例外**: `SpecificationError`。入力がデザインに合わない、分布に分散がない、重みやバンド幅が範囲外、
選択肢どうしが合わない（ガウス以外のカーネルとペナルティ以外のバンド幅の選び方、`linear=True` と
バンド幅の指定または一様カーネル、カウンターバランスデザインでの `"rule_of_thumb"`）、（事後層化で）
アンカー得点の確率が一方の母集団でだけ 0 の場合。

**照合先**: R `kequate::kequate` のデザイン `"EG"`、`"SG"`、`"CB"`、`"NEAT_PSE"`、`"NEAT_CE"`。
`kernel = "logistic"` と `"uniform"`、二重平滑化・交差検証・経験則のバンド幅も照合している。
`SNSequate::ker.eq`（等価群）。有限差分による標準誤差を持つ独立した R 実装。

### `KernelEquatingResult`

X 版から Y 版の尺度へのカーネル等化関数。[`kernel_equate`](#kernel_equate) が返す。

| 属性 | 型 | 説明 |
|---|---|---|
| `design` | str | `"equivalent_groups"`、`"single_group"`、`"counterbalanced"`、`"chained"`、`"post_stratification"` のいずれか |
| `x`、`y` | `ScoreDistribution` | 連続化した得点分布。デザインで決まる得点の確率 $r$ と $s$（周辺分布、重みつきの周辺分布、または合成母集団。連鎖等化では、X を受けた母集団での X と、Y を受けた母集団での Y） |
| `scores` | 配列 | X 版のとりうる得点 |
| `equated` | 配列 | Y 版での対応値 $e_Y(x_j)$ |
| `see` | 配列 | とりうる得点ごとの等化の標準誤差 |
| `see_vectors` | 形 `(n_scores, n_columns)` の配列 | ユークリッドノルムが `see` になるベクトル。`seed()` が使う |
| `bandwidth_x`、`bandwidth_y` | float | バンド幅 $h_X$ と $h_Y$ |
| `penalty_weight` | float | ペナルティでバンド幅を選んだときに使った重み $K$ |
| `kernel` | str | `"gaussian"`、`"logistic"`、`"uniform"` のいずれか |
| `bandwidth_method` | str | 指定しなかったバンド幅の選び方 |
| `x_presmoothed`、`y_presmoothed` | bool | 1 つめと 2 つめの入力が対数線形モデルから来たか（標準誤差に使う共分散が決まる）。単一群では等しい |
| `anchor_distributions` | `ScoreDistribution` の組 / `None` | 連鎖等化: X を受けた母集団と Y を受けた母集団でのアンカーの分布 |
| `anchor_bandwidths` | `(float, float)` / `None` | 連鎖等化: 2 つのアンカー分布のバンド幅 |
| `synthetic_weight` | float / `None` | 事後層化: 合成母集団での、X を受けた母集団の重み |
| `counterbalance_weights` | `(float, float)` / `None` | カウンターバランスデザイン: 1 つめの標本の、$r$ と $s$ での重み |

| メンバー | 戻り値 | 説明 |
|---|---|---|
| `table`（プロパティ） | `pandas.DataFrame` | 換算表: `score`, `equated`, `see` |
| `continuized`（プロパティ） | `pandas.DataFrame` | 各版のとりうる得点での連続化した分布: `form`, `score`, `probability`（離散）, `cdf`, `density`。`form` は `"x"` か `"y"`。連鎖等化では `"anchor_x"` と `"anchor_y"` もある |
| `percent_relative_error`（プロパティ） | `pandas.Series` | 1 次から 10 次のモーメントの相対誤差（パーセント）。添字はモーメントの次数 1..10。連鎖等化では `SpecificationError` |
| `chain_percent_relative_error`（プロパティ） | `pandas.DataFrame` | 連鎖等化: 2 つのリンクの相対誤差。列は `x_to_anchor` と `anchor_to_y`。ほかのデザインでは `SpecificationError` |
| `transform(values)` | 配列 | X 版の任意の得点に対応する Y 版の値。形は `values` と同じ |
| `seed(other)` | `pandas.DataFrame` | 2 つの等化関数の差の標準誤差。列は `score`、`difference`（この関数 − `other`）、`seed` |

相対誤差は、等化後得点のモーメントを Y 版のモーメントと比べる。

$$
\mathrm{PRE}(p) = 100\, \frac{\mu_p(e_Y(X)) - \mu_p(Y)}{\mu_p(Y)}, \qquad
\mu_p(e_Y(X)) = \sum_j r_j\, e_Y(x_j)^p, \quad \mu_p(Y) = \sum_k s_k\, y_k^p .
$$

**`seed(other)`**。同じデータから推定した 2 つの等化関数 $e_1$ と $e_2$ について、

$$
\mathrm{SEED}(x) = \sqrt{\operatorname{Var}\bigl(e_1(x) - e_2(x)\bigr)} .
$$

`other` は**同じ入力から**計算したものでなければならない。同じ分布または事前平滑化の結果を使い、同じ
デザインか、アンカーテストを使うもう一方のデザイン（連鎖と事後層化）であること。これは配列の形以上には
確認できず、データが違えば結果に意味はない。主な使い方は、カーネル等化と線形等化（`linear=True`）、
2 組のバンド幅、連鎖等化と事後層化等化の比較である。2 つの結果で X の得点や標本変動の源が同じでないと
`SpecificationError` になる。

### `penalty_bandwidth`

```text
penalty_bandwidth(distribution, *, penalty_weight=1.0, kernel="gaussian") -> float
```

von Davier et al. (2004, 4 章) のペナルティを最小にするバンド幅。

$$
\mathrm{PEN}(h) = \sum_j \bigl(r_j - f_h(x_j)\bigr)^2 + K \sum_j A_j (1 - B_j) .
$$

第 1 項は、とりうる得点での連続化した密度 $f_h$ を得点の確率に近づける。第 2 項は、密度がそのまわりで
U 字形になる得点を数える。$f_h'(x_j - w) < 0$ なら $A_j = 1$、$f_h'(x_j + w) > 0$ なら $B_j = 0$ で、
$w$ は得点の刻み幅の 4 分の 1 である。ペナルティは得点を刻み幅の単位で測って評価し、バンド幅は得点の
尺度で返す。最小値は刻み幅の 0.05 倍から 10 倍の範囲で探す。

| 引数 | 型 | 説明 |
|---|---|---|
| `distribution` | `ScoreDistribution` / `LoglinearResult` | 得点分布。事前平滑化の結果を渡すと、平滑化後の分布を使う |
| `penalty_weight` | float、既定 `1.0` | 第 2 項の重み $K$（`kequate` の `KPEN`、`SNSequate` の `Kp`）。0 で第 2 項を外す |
| `kernel` | `"gaussian"` / `"logistic"` / `"uniform"`、既定 `"gaussian"` | 連続化のカーネル。一様カーネルの密度は区分的に一定なので、`penalty_weight` によらず第 2 項は 0 になる |

**戻り値**: float。バンド幅 $h$。

**例外**: `SpecificationError`。`penalty_weight` が負、カーネルが未知、分布が 1 変量でない、または分散が
ない場合。

**照合先**: R `kequate`（`KPEN = 0`）、`SNSequate::bandwidth`、独立した R 実装。

---

## `flexpyequate.errors`

例外と警告のクラス。ライブラリが意図して送出するエラーはすべて `FlexpyequateError` を、警告はすべて
`FlexpyequateWarning` を継承するので、まとめて捕捉できる。

```text
from flexpyequate import errors
```

### `FlexpyequateError`

flexpyequate が送出するすべてのエラーの基底クラス（`Exception`）。

### `ScoreDistributionError`

得点や度数が正しい得点分布にならない。例: とりうる得点が等間隔でない、度数が負、観測得点がとりうる得点で
ない、観測が 1 つもない。`FlexpyequateError` と `ValueError` を継承する。

### `SpecificationError`

呼び出しの引数どうし、または引数とデータが合わない。例: 単一群の手法に別々の分布を 2 つ渡した、手法名が
未知、とりうる得点の数に対して多項式の次数が高すぎる。`FlexpyequateError` と `ValueError` を継承する。

### `FlexpyequateWarning`

flexpyequate が出すすべての警告の基底クラス（`UserWarning`）。

### `ConvergenceWarning`

反復計算が収束基準に達する前に止まった（対数線形モデルによる事前平滑化）。`FlexpyequateWarning` を
継承する。

### `SparseDataWarning`

データが疎で計算の一部ができず、使えるデータだけで計算した。例: 2 つの母集団の一方でしか観測されなかった
アンカー得点があり、その得点を与えたときの条件つき分布を推定できない。`FlexpyequateWarning` を継承する。

---

## `__version__`

インストールされている flexpyequate のバージョン（文字列。`flexpyequate.__version__`）。

---

## 参考文献

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
