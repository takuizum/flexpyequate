# Contributing

English | [日本語](CONTRIBUTING.ja.md)

flexpyequate is one of three related packages, each in its own repository with its own version:

| Package | Repository | Contents |
|---|---|---|
| `flexpyirt` | [takuizum/flexpyirt](https://github.com/takuizum/flexpyirt) | Estimation of IRT models and everything that uses a fitted model. Depends on JAX and on flexpyctt |
| `flexpyctt` | [takuizum/flexpyctt](https://github.com/takuizum/flexpyctt) | Item and test analysis that needs no fitted model. NumPy, SciPy and pandas only |
| `flexpyequate` | [takuizum/flexpyequate](https://github.com/takuizum/flexpyequate) | Equating of score distributions. NumPy, SciPy and pandas only; independent of the other two |

- **flexpyequate never imports JAX, flexpyirt or flexpyctt.** CI checks that none of them is
  installed.
- Equating that needs item parameters (IRT true-score and observed-score equating, scale
  linking) belongs in flexpyirt.
- The design is in [docs/DESIGN.md](docs/DESIGN.md). Decide there first, then write the code.

## Branches

| Branch | Role | Created from / merged into |
|---|---|---|
| `main` | Released states only. No direct pushes | Accepts release PRs from `develop` only |
| `develop` | Integration branch; collects what goes into the next release | Accepts PRs from `feature/*` and `fix/*` |
| `feature/<slug>` | Features, documentation, refactoring and so on | From `develop`, PR into `develop` |
| `fix/<issue number>-<slug>` | Bug fixes. **Always tied to an issue** | From `develop`, PR into `develop` |

- `<slug>` uses lowercase letters, digits, `.`, `_` and `-` only.
- A fix branch's PR description contains `Closes #<issue number>`, and the issue must be open.
  (`develop` is not the default branch, so the workflow closes the issue **at release time**, not at
  merge time.)
- The `PR rules` check (`scripts/check_pr.py`) enforces these on every PR.

## PRs and reviews

- Every change goes in through a PR. `main` and `develop` are protected by rulesets and cannot be
  merged into until CI (`test (3.12/3.13)`) and `pr-rules` pass.
- The repository owner reviews PRs before merging them (no automatic merging).
- Changes to numerical code must pass the agreement tests against R (equate, kequate, SNSequate). The
  reference values are committed in `tests/reference/`; CI does not run R.

## Releases

The version comes from **git tags** (`vX.Y.Z`, via hatch-vcs). `pyproject.toml` holds no version;
releasing means tagging. Untagged development commits get versions like `0.1.1.dev3+g1a2b3c4`.

1. Open a PR from `develop` into `main`. **Its title decides the version bump**:
   - `release(major): ...` / `release(minor): ...` / `release(patch): ...`
   - Merge it with a **merge commit** (the `main` ruleset allows merge commits only).
2. The merge runs `.github/workflows/release.yml`:
   1. `plan` job: computes the next version from the PR title and the latest `vX.Y.Z` tag.
   2. `publish` job: runs **without waiting for approval** (`release` environment, which deploys
      from `main` only). It tags `main` with `vX.Y.Z`, builds (`uv build`) and creates a GitHub
      Release (wheel and sdist attached, release notes generated). It then closes the issues
      that fix PRs in this release `Closes`d.
   3. `pypi` job: **waits for approval in the `pypi` environment**. Once the owner approves it on
      the Actions page, it publishes the same wheel and sdist to PyPI (Trusted Publishing; no
      API token).
3. **The first release** (no `v*` tag yet) is **v0.1.0**, whatever bump the title asks for.
4. Manual runs (`workflow_dispatch`) are dry runs only: they compute the next version and build.

Versions follow [Semantic Versioning](https://semver.org/). Before 1.0.0, a minor release
(`0.X.0`) may change the public API and a patch release (`0.x.Y`) must not.

## Security (who can release)

- **Only repository admins can update `main`** (ruleset `main-release-gate`). The PR and CI
  requirements (ruleset `main`) apply to admins too.
- **The `publish` job runs in the `release` environment**, which deploys from `main` only and
  has no required reviewer: merging the release PR is the decision to tag.
- **PyPI uploads use Trusted Publishing** (OIDC). The PyPI project `flexpyequate` trusts only the
  publisher "repository `takuizum/flexpyequate`, workflow `release.yml`, environment `pypi`", so no API
  token lives in the repository. The `pypi` environment needs the owner's approval. A version
  number uploaded to PyPI can never be reused, even after deleting it.
- Workflow `GITHUB_TOKEN`s are read-only by default; only the `publish` job writes.

## Local development

Manage Python environments with `uv` only (no pip).

```bash
uv sync --dev
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```

The R scripts that write the reference values are `validation/r/equate_*.R` (run them from the
repository root, e.g. `Rscript validation/r/equate_e1_reference.R`); they write to
`tests/reference/`.

## Naming

Names follow PEP 8 and read as Python, not as R. `ruff` checks the `N` rules.

- Spell public names out, and use one name for one concept across the API (`n_factors`,
  `n_categories`). Do not copy R argument names; mention the R name in the docstring.
- `Literal` string options are lowercase `snake_case`. Established acronyms stay upper case.
- Public functions and classes have type hints and NumPy-style docstrings; a function that
  implements a formula gives the formula and its source in the docstring.

## Documentation

Every document exists in English (`*.md`) and Japanese (`*.ja.md`) with the same content. Update
both when you change one. `README.md` / `README.ja.md` are also shown on the PyPI project page, so
their links are absolute and they hold no development information.
