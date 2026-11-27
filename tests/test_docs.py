"""Keep the documentation honest, in both languages.

- Every ```python block in docs/index and docs/guide (English and Japanese) runs, top to bottom,
  in one namespace per file (later blocks may use names from earlier ones), without a flexpyequate
  warning that the block does not catch itself.
- English and Japanese versions have the same code (comments aside).
- Every document has its counterpart (``X.md`` <-> ``X.ja.md``).
- Every name in ``flexpyequate.__all__`` and ``flexpyequate.errors.__all__`` has an entry in
  docs/reference.md and docs/reference.ja.md.
- Japanese documents link to Japanese documents (except the language switcher), including
  absolute links to GitHub files and to the documentation site (README links are absolute so they
  work on PyPI).
- Pages of the site do not link to the design document with a relative link (it is not part of
  the site).
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import pytest

import flexpyequate
from flexpyequate import errors

ROOT = Path(__file__).resolve().parents[1]
BLOCK_RE = re.compile(r"^```python\n(.*?)^```", re.M | re.S)
RUNNABLE = ["docs/index.md", "docs/index.ja.md", "docs/guide.md", "docs/guide.ja.md"]
GITHUB_BLOB = "https://github.com/takuizum/flexpyequate/blob/main/"
DOCS_SITE = "https://takuizum.github.io/flexpyequate/"
# Developer documents under docs/ that mkdocs.yml excludes from the site.
NOT_ON_SITE = {"DESIGN"}
DOC_STEMS = sorted(
    {
        "README",
        "CONTRIBUTING",
        *(f"docs/{p.name.split('.')[0]}" for p in (ROOT / "docs").glob("*.md")),
    }
)
SITE_PAGES = sorted(
    str(p.relative_to(ROOT))
    for p in (ROOT / "docs").glob("*.md")
    if p.name.split(".")[0] not in NOT_ON_SITE
)
JAPANESE_DOCS = sorted(
    str(p.relative_to(ROOT))
    for p in ROOT.rglob("*.ja.md")
    # Skip hidden directories (.venv, ...) and the built site: not the repository's documents.
    if not any(part.startswith(".") or part == "site" for part in p.relative_to(ROOT).parts)
)


def _blocks(path: Path) -> list[str]:
    return BLOCK_RE.findall(path.read_text(encoding="utf-8"))


def _code_only(block: str) -> list[str]:
    """Return the block's lines without comments, docstring lines and blank lines."""
    out = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith('"""'):
            continue
        out.append(re.sub(r"\s+#.*$", "", line).rstrip())
    return out


@pytest.mark.parametrize("doc", RUNNABLE)
def test_code_blocks_run(doc: str, capsys: pytest.CaptureFixture[str]) -> None:
    blocks = _blocks(ROOT / doc)
    assert blocks, f"{doc} has no python blocks"
    namespace: dict[str, object] = {"__name__": f"docs:{doc}"}
    with warnings.catch_warnings():
        warnings.simplefilter("error", errors.FlexpyequateWarning)
        for i, code in enumerate(blocks):
            try:
                # dont_inherit: run the blocks as a plain script, without this module's
                # ``from __future__ import annotations``.
                exec(compile(code, f"{doc}[block {i}]", "exec", dont_inherit=True), namespace)
            except Exception as e:  # pragma: no cover - message for the failing block
                raise AssertionError(f"{doc} block {i} failed:\n{code}") from e
    capsys.readouterr()


@pytest.mark.parametrize("stem", DOC_STEMS)
def test_documents_come_in_pairs(stem: str) -> None:
    en, ja = ROOT / f"{stem}.md", ROOT / f"{stem}.ja.md"
    assert en.exists(), f"{en.name} is missing (counterpart of {ja.name})"
    assert ja.exists(), f"{ja.name} is missing (counterpart of {en.name})"


@pytest.mark.parametrize("stem", DOC_STEMS)
def test_translations_have_the_same_code(stem: str) -> None:
    en_blocks = [_code_only(b) for b in _blocks(ROOT / f"{stem}.md")]
    ja_blocks = [_code_only(b) for b in _blocks(ROOT / f"{stem}.ja.md")]
    assert len(en_blocks) == len(ja_blocks), f"{stem}: different number of python blocks"
    for i, (a, b) in enumerate(zip(en_blocks, ja_blocks, strict=True)):
        assert a == b, f"{stem} block {i} differs between English and Japanese"


@pytest.mark.parametrize("doc", ["docs/reference.md", "docs/reference.ja.md"])
def test_reference_covers_public_api(doc: str) -> None:
    text = (ROOT / doc).read_text(encoding="utf-8")
    names = [*flexpyequate.__all__, *errors.__all__]
    # A heading whose code span is the name itself or its dotted path (`flexpyequate.errors`).
    missing = [
        n for n in names if not re.search(rf"^#+ .*`(?:[\w.]+\.)?{re.escape(n)}`", text, re.M)
    ]
    assert not missing, f"Not documented in {doc}: {missing}"


@pytest.mark.parametrize("doc", JAPANESE_DOCS)
def test_japanese_docs_link_to_japanese_docs(doc: str) -> None:
    lines = (ROOT / doc).read_text(encoding="utf-8").splitlines()
    text = "\n".join(line for line in lines if not line.startswith("[English]("))
    links = re.findall(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)", text)
    english = [link for link in links if not link.endswith(".ja.md")]
    # Pages of the documentation site: the Japanese site lives under /ja/.
    site_links = re.findall(rf"\]\(({re.escape(DOCS_SITE)}[^)\s]*)\)", text)
    english += [s for s in site_links if not s.startswith(DOCS_SITE + "ja/")]
    assert not english, f"{doc} links to English documents: {english}"


@pytest.mark.parametrize("doc", SITE_PAGES)
def test_site_pages_do_not_link_to_documents_outside_the_site(doc: str) -> None:
    text = (ROOT / doc).read_text(encoding="utf-8")
    links = re.findall(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)", text)
    excluded = [
        link
        for link in links
        if not link.startswith("https://") and Path(link).name.split(".")[0] in NOT_ON_SITE
    ]
    assert not excluded, f"{doc} links to documents that are not on the site: {excluded}"
