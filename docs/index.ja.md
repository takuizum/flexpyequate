# flexpyequate

[English](index.md) | 日本語

テスト得点分布の等化を行う Python ライブラリである。2 つのテスト版の得点分布から、X 版の得点を Y 版の
尺度に対応づける関数を求める。平均等化、線形等化、等パーセンタイル等化、アンカーテストを使う方法、
対数線形モデルによる事前平滑化、カーネル等化を扱う。

- **R と数値照合済み**: すべての手法を R `equate`・`kequate`・`SNSequate`、および公刊された式の独立実装と
  数値で比較している。
- **軽量**: 依存は NumPy・SciPy・pandas のみである。
- **範囲**: 得点分布にもとづく観測得点等化。項目パラメータを使う等化（IRT 真値等化・観測得点等化、
  尺度のリンキング）は [flexpyirt](https://github.com/takuizum/flexpyirt) にある。

> 開発中（0.x）。1.0.0 までは公開 API が変わることがある。

## インストール

Python 3.12 以降。

```bash
pip install flexpyequate  # または: uv add flexpyequate
```

## 最初の等化

等価な 2 群がそれぞれ 1 つの版を受けたとする。版ごとに得点分布を作り、X 版を Y 版に等化する。

```python
import flexpyequate as fe

# 等価な 2 群が受けた 2 つの版の、得点 0..4 の度数
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

result.transform([1.5, 2.5])  # とりうる得点の間の値も等化できる
result.moments  # X・Y・等化後得点の平均、標準偏差、歪度、尖度

linear = fe.equate(x, y, method="linear")
linear.slope, linear.intercept
```

## パッケージの内容

| やりたいこと | 関数 |
|---|---|
| 1 つの版の得点、または同じ受検者の 2 つの得点を表す | `ScoreDistribution`、`BivariateScoreDistribution` |
| 平均等化・線形等化・等パーセンタイル等化、アンカーテストを使う方法（Tucker、Levine、Braun–Holland、連鎖、頻度推定）、標準誤差 | `equate()` |
| 多項式対数線形モデルで分布を平滑化する | `presmooth()` |
| 5 つのデザインでのカーネル等化と標準誤差 | `kernel_equate()` |

## 次に読むもの

- [ユーザーガイド](guide.ja.md): 得点分布、各等化手法とデザイン、標準誤差、事前平滑化、カーネル等化、
  結果の読み方。
- [API リファレンス](reference.ja.md): 公開しているすべてのクラスと関数。
- ソースコード、issue、リリース: [GitHub](https://github.com/takuizum/flexpyequate)。
