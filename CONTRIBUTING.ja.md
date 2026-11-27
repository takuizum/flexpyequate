# コントリビューションガイド

[English](CONTRIBUTING.md) | 日本語

flexpyequate は関連する 3 つのパッケージの 1 つで、それぞれが自分のリポジトリとバージョンを持つ。

| パッケージ | リポジトリ | 内容 |
|---|---|---|
| `flexpyirt` | [takuizum/flexpyirt](https://github.com/takuizum/flexpyirt) | IRT モデルの推定と、推定済みのモデルを使うものすべて。JAX と flexpyctt に依存 |
| `flexpyctt` | [takuizum/flexpyctt](https://github.com/takuizum/flexpyctt) | 推定済みのモデルを使わない項目・テスト分析。NumPy・SciPy・pandas のみ |
| `flexpyequate` | [takuizum/flexpyequate](https://github.com/takuizum/flexpyequate) | 得点分布の等化。NumPy・SciPy・pandas のみ。他の 2 つとは独立 |

- **flexpyequate は JAX も flexpyirt も flexpyctt も import しない。**CI で、どれもインストールされていない
  ことを確認する。
- 項目パラメータが要る等化（IRT の真値等化・観測得点等化、尺度の連結）は flexpyirt に置く。
- 設計は [docs/DESIGN.ja.md](docs/DESIGN.ja.md) にある。先にそこで決めてから、コードを書く。

## ブランチ

| ブランチ | 役割 | 作成元 / マージ先 |
|---|---|---|
| `main` | リリース済みの状態だけ。直接 push しない | `develop` からのリリース PR だけを受け付ける |
| `develop` | 統合ブランチ。次のリリースに入るものを集める | `feature/*` と `fix/*` からの PR を受け付ける |
| `feature/<slug>` | 機能、ドキュメント、リファクタリングなど | `develop` から作り、`develop` へ PR |
| `fix/<issue番号>-<slug>` | バグ修正。**必ず issue に紐づける** | `develop` から作り、`develop` へ PR |

- `<slug>` に使えるのは小文字、数字、`.`、`_`、`-` だけ。
- fix ブランチの PR の説明には `Closes #<issue番号>` を書き、その issue は open でなければならない
  （`develop` はデフォルトブランチではないので、issue はマージ時ではなく**リリース時**にワークフローが閉じる）。
- これらは `PR rules` チェック（`scripts/check_pr.py`）がすべての PR で確認する。

## PR とレビュー

- すべての変更は PR で入れる。`main` と `develop` はルールセットで保護されていて、CI（`test (3.12/3.13)`）と
  `pr-rules` が通るまでマージできない。
- PR はリポジトリのオーナーがレビューしてからマージする（自動マージはしない）。
- 数値計算のコードを変えるときは、R（equate, kequate, SNSequate）との照合テストが通ること。参照値は
  `tests/reference/` にコミットしてあり、CI では R を実行しない。

## リリース

バージョンは **git タグ**（`vX.Y.Z`、hatch-vcs）から決まる。`pyproject.toml` にはバージョンを書かない。
リリースとはタグを付けることである。タグのない開発中のコミットは `0.1.1.dev3+g1a2b3c4` のようなバージョンになる。

1. `develop` から `main` へ PR を開く。**タイトルでバージョンの上げ方が決まる**:
   - `release(major): ...` / `release(minor): ...` / `release(patch): ...`
   - **マージコミット**でマージする（`main` のルールセットはマージコミットだけを許可している）。
2. マージすると `.github/workflows/release.yml` が動く:
   1. `plan` ジョブ: PR のタイトルと最新の `vX.Y.Z` タグから次のバージョンを計算する。
   2. `publish` ジョブ: **承認を待たずに動く**（`release` 環境。`main` からしかデプロイしない）。`main` に
      タグ `vX.Y.Z` を打ってビルドし（`uv build`）、GitHub Release を作成する（wheel / sdist 添付、
      リリースノート自動生成）。このリリースに含まれる fix PR が `Closes` していた issue を閉じる。
   3. `pypi` ジョブ: **`pypi` 環境の承認待ちになる**。オーナーが Actions 画面で承認すると、同じ wheel / sdist を
      PyPI に公開する（Trusted Publishing。API トークンは使わない）。
3. **最初のリリース**（`v*` タグがまだないとき）は、タイトルの指定にかかわらず **v0.1.0** になる。
4. 手動実行（`workflow_dispatch`）はドライランだけで、次のバージョンの計算とビルドをする。

バージョンは [Semantic Versioning](https://semver.org/) に従う。1.0.0 より前は、マイナーリリース（`0.X.0`）で
公開 API を変えてよく、パッチリリース（`0.x.Y`）では変えてはならない。

## セキュリティ（誰がリリースできるか）

- **`main` を更新できるのはリポジトリの管理者だけ**（ルールセット `main-release-gate`）。PR と CI の要件
  （ルールセット `main`）は管理者にも適用される。
- **`publish` ジョブは `release` 環境で動き**、この環境は `main` からしかデプロイしない。必須レビュアーは
  付けていない。リリース PR のマージが、タグを打つ判断である。
- **PyPI へのアップロードは Trusted Publishing**（OIDC）。PyPI のプロジェクト `flexpyequate` は、
  「リポジトリ `takuizum/flexpyequate`、ワークフロー `release.yml`、環境 `pypi`」という発行者だけを信頼するので、
  リポジトリに API トークンは置かない。`pypi` 環境はオーナーの承認を必要とする。PyPI に一度アップロードした
  バージョン番号は、削除しても再利用できない。
- ワークフローの `GITHUB_TOKEN` は既定で読み取り専用で、書き込むのは `publish` ジョブだけである。

## ローカル開発

Python 環境は `uv` だけで管理する（pip は使わない）。

```bash
uv sync --dev
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```

参照値を書き出す R スクリプトは `validation/r/equate_*.R` である（リポジトリのルートから実行する。例:
`Rscript validation/r/equate_e1_reference.R`）。出力先は `tests/reference/` である。

## 命名

名前は PEP 8 に従い、R ではなく Python として読めるものにする。`ruff` が `N` ルールを確認する。

- 公開名は略さず、同じ概念には API 全体で同じ名前を使う（`n_factors`、`n_categories`）。R の引数名を
  持ち込まず、R での名前は docstring に書く。
- `Literal` の選択肢は小文字の `snake_case`。定着した頭字語は大文字のままにする。
- 公開関数・クラスには型ヒントと NumPy スタイルの docstring を付ける。数式を実装した関数は、docstring に
  その式と出典を書く。

## ドキュメント

どの文書にも英語版（`*.md`）と日本語版（`*.ja.md`）があり、内容は同じである。片方を変えたら両方を直す。

| 文書 | 読者 | 表示される場所 |
|---|---|---|
| `README.md` | ユーザー | GitHub と PyPI のプロジェクトページ |
| `docs/index.md`、`docs/guide.md`、`docs/reference.md` | ユーザー | ドキュメントサイト <https://takuizum.github.io/flexpyequate/ja/> |
| `docs/DESIGN.md` | 開発者 | GitHub のみ（`mkdocs.yml` でサイトから除外している） |
| `CONTRIBUTING.md` | 開発者 | GitHub のみ |

- **サイト**は、`docs/` の Markdown（`DESIGN*.md` を除く）から MkDocs（Material テーマ、
  `mkdocs-static-i18n`）で作る。`.github/workflows/docs.yml` がすべての PR でビルドし、`main` から
  GitHub Pages に公開する。サイトはリリース済みの状態を示す。
- **プレビュー**: `uv run --group docs mkdocs serve`。**CI と同じ検査**:
  `uv run --group docs mkdocs build --strict`（リンクやアンカーが切れているとビルドが失敗する）。
- **サイトのページはユーザー向けである。** パッケージで何ができ、どう使うかを書く。マイルストーン、
  `DESIGN.md` の節番号、検証ケースの ID、開発の手順は書かない。内容はすべてコード、docstring、
  `README.md`、`DESIGN.md` にもとづいて書く。
- **リンク。** `docs/` のページどうしは相対リンクにする（`guide.ja.md`、`reference.ja.md#equate`）。
  日本語のページからは日本語のページにリンクする。サイトのページから `DESIGN.md` へ相対リンクを
  張らない（サイトに含まれないため）。必要なら GitHub の URL を使う。`README.md` / `README.ja.md` は
  PyPI のプロジェクトページにも表示されるので、リンクは絶対 URL にし（日本語版 README はサイトの `/ja/`
  以下にリンクする）、開発に関する情報は書かない。
- **コード例。** `docs/index.md` と `docs/guide.md` の Python ブロックはすべて、固定したシードの
  シミュレーションデータで、ページの上から順にそのまま実行できる。`tests/test_docs.py` が両方の言語で
  実行し、2 つの言語のコードが同じであること（コメントは違ってよい）、公開名がすべて
  `docs/reference.md` に載っていること、どの文書にも他方の言語の版があることを確かめる。
