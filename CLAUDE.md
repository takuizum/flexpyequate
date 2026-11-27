# CLAUDE.md — flexpyequate

**flexpyequate** は、得点分布の等化（平均等化、線形等化、等パーセンタイル等化、アンカーテストを使う方法、対数線形モデルに
よる事前平滑化、カーネル等化）のライブラリです。NumPy・SciPy・pandas だけに依存します（JAX は使わない）。2026-11-27 に
[takuizum/flexpyirt](https://github.com/takuizum/flexpyirt) の `packages/flexpyequate/` から独立したリポジトリになりました。

作業の前に `docs/DESIGN.md`（設計・数式・検証計画）を読んでください。各文書は英語版 `*.md` と日本語版 `*.ja.md` があり、
内容は同じ。更新するときは両方を直す。

## 関連リポジトリ

| パッケージ | リポジトリ | 関係 |
|---|---|---|
| `flexpyirt` | takuizum/flexpyirt | 独立。項目パラメータが要る等化（IRT の真値等化・観測得点等化、尺度の連結）はこちら |
| `flexpyctt` | takuizum/flexpyctt | 独立 |

## 最優先の原則

1. **正しさ > 速さ > 機能の多さ。** 各機能は R（equate・kequate・SNSequate）と数値照合するテストが通るまで「完成」と
   しない。R の焼き直しではなく数式から実装し、R は検証の参照値としてのみ使う。
2. **機能を水増ししない。** 未検証の機能を README に載せない。
3. **JAX も flexpyirt も flexpyctt も import しない。** 乱数は `rng`（`numpy.random.Generator` または整数のシード）で
   受け取る。
4. **迷ったら先に DESIGN.md で決める。** 決めた内容を `docs/DESIGN.md` に追記してからコードを書く。
5. **小さくコミット。**

## 開発環境

- Python >= 3.12、パッケージ管理は `uv` のみ（pip は使わない）。
- 依存: `numpy`, `scipy`, `pandas`。開発依存: `pytest`, `hypothesis`, `ruff`, `mypy`。
- 検査: `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`
- R 参照値の生成: `validation/r/equate_*.R`（リポジトリのルートから実行）。生成した参照値は `tests/reference/*.json` に
  コミットし、CI では R を走らせない。

## コーディング規約

- 公開関数・クラスは型ヒント必須、docstring は NumPy スタイル。公開 API は keyword-only 引数を基本にする。
- 数式を実装した関数には、docstring に対応する式（LaTeX）と出典（著者・年）を書く。
- 例外は `flexpyequate.errors` に定義した具体的なクラスで投げる。
- 命名は PEP 8 に従い、R の引数名を持ち込まない（CONTRIBUTING.md「命名」）。

## 開発フロー（CONTRIBUTING.md）

- `feature/<slug>` と `fix/<issue番号>-<slug>` を `develop` から切り、`develop` へ PR。fix は issue 必須（`Closes #N`）。
- リリースは `develop` → `main` の PR。タイトル `release(major|minor|patch): ...` で上げ方を決め、マージ後にオーナーが
  `release` 環境を承認するとタグ `vX.Y.Z` と GitHub Release ができ、`pypi` ジョブが PyPI に公開する
  （Trusted Publishing）。バージョンは git タグから（hatch-vcs、`pyproject.toml` に書かない）。最初のリリースは v0.1.0。
- `README*.md` は PyPI にも表示されるのでリンクは絶対 URL。開発関連の情報は書かない。
- **PR はオーナーがレビューしてマージする。Claude は PR を作るまでで、マージしない。**
