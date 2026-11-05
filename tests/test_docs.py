"""The docs: `README.md` and `docs/*.md`.

Every relative link leads to a file of the repository and every `#anchor`
to a heading of its file (with the slugs GitHub gives headings); every doc
that the code cites in a message exists, with its anchor; the samples that
the docs present as valid pass the checks.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.support import ROOT
from tools import _locale

DOCS = sorted((ROOT / "docs").glob("*.md"))
MARKDOWN = [ROOT / "README.md", *DOCS]

_FENCE_RE = re.compile(r"^```.*?^```[ \t]*$", re.M | re.S)
_CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$", re.M)
_JSON_BLOCK_RE = re.compile(r"^```json[ \t]*\n(.*?)^```", re.M | re.S)
#: A doc cited by the code: `docs/<name>.md`, maybe with an anchor.
_CITATION_RE = re.compile(r"docs/([a-z0-9-]+\.md)(?:#([A-Za-z0-9_-]+))?")


def without_code(text: str) -> str:
    """The text with its fenced blocks blanked out (same length, same
    lines): their lines are neither headings nor links."""
    return _FENCE_RE.sub(lambda match: re.sub(r"[^\n]", " ", match.group(0)), text)


def github_slug(heading: str) -> str:
    """The anchor GitHub gives a heading: the text in lower case, every
    character but letters, digits, spaces, `-` and `_` removed, spaces
    turned into `-` (hyphens are not collapsed)."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    text = text.replace("`", "").strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    """The anchors of the headings of a Markdown file; a repeated slug gets
    `-1`, `-2`, … as on GitHub."""
    seen: dict[str, int] = {}
    found = set()
    for match in _HEADING_RE.finditer(without_code(path.read_text(encoding="utf-8"))):
        slug = github_slug(match.group(2))
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        found.add(slug if count == 0 else f"{slug}-{count}")
    return found


def links(path: Path) -> list[str]:
    """The link targets of a Markdown file, outside code."""
    text = _CODE_SPAN_RE.sub("", without_code(path.read_text(encoding="utf-8")))
    return _LINK_RE.findall(text)


def tracked_files() -> set[str] | None:
    """The tracked files of the repository, or None outside a git work tree
    of its own."""
    try:
        top = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
            capture_output=True, check=False, text=True,
        )
        if top.returncode != 0 or Path(top.stdout.strip()).resolve() != ROOT.resolve():
            return None
        listed = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=False
        )
    except OSError:
        return None
    if listed.returncode != 0:
        return None
    return {name for name in listed.stdout.decode("utf-8").split("\0") if name}


def section(path: Path, heading: str) -> str:
    """The text of a section of a Markdown file, from its heading to the
    next heading of the same or a higher level."""
    text = path.read_text(encoding="utf-8")
    plain = without_code(text)
    for match in _HEADING_RE.finditer(plain):
        if match.group(2) == heading:
            level = len(match.group(1))
            rest = _HEADING_RE.finditer(plain, match.end())
            end = next(
                (found.start() for found in rest if len(found.group(1)) <= level), len(text)
            )
            return text[match.end():end]
    raise AssertionError(f"{path.name}: no heading {heading!r}")


def json_blocks(text: str) -> list[str]:
    return _JSON_BLOCK_RE.findall(text)


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.tracked = tracked_files()

    def assert_file(self, target: Path, where: str):
        relative = target.resolve().relative_to(ROOT.resolve()).as_posix()
        if self.tracked is None:
            self.assertTrue(target.is_file(), f"{where}: no file {relative}")
        else:
            self.assertIn(relative, self.tracked, f"{where}: {relative} is not tracked")

    def test_the_docs_exist(self):
        self.assertTrue(DOCS)

    def test_relative_links_lead_to_files_and_headings(self):
        for path in MARKDOWN:
            for target in links(path):
                if re.match(r"[a-z][a-z0-9+.-]*:", target):
                    continue  # an external address
                where = f"{path.relative_to(ROOT)} -> {target}"
                with self.subTest(link=where):
                    name, _, anchor = target.partition("#")
                    file = (path.parent / name).resolve() if name else path
                    self.assert_file(file, where)
                    if anchor:
                        self.assertEqual(file.suffix, ".md", f"{where}: an anchor into a non-Markdown file")
                        self.assertIn(anchor, anchors(file), f"{where}: no such heading")

    def test_the_readme_lists_every_doc(self):
        listed = {target.partition("#")[0] for target in links(ROOT / "README.md")}
        for path in DOCS:
            with self.subTest(doc=path.name):
                self.assertIn(f"docs/{path.name}", listed)

    def test_slugs_follow_the_rules_of_github(self):
        self.assertEqual(github_slug("`--allow-path`: links to other pages"), "--allow-path-links-to-other-pages")
        self.assertEqual(github_slug("`robots.txt` and link preview bots"), "robotstxt-and-link-preview-bots")
        self.assertEqual(github_slug('The "not found" page'), "the-not-found-page")
        self.assertEqual(github_slug("Tokens: pairs and derived values"), "tokens-pairs-and-derived-values")


class CitationTests(unittest.TestCase):
    def test_the_docs_cited_by_the_code_exist(self):
        sources = [ROOT / "build.py", *sorted((ROOT / "tools").glob("*.py"))]
        for source in sources:
            for name, anchor in _CITATION_RE.findall(source.read_text(encoding="utf-8")):
                with self.subTest(source=source.name, doc=name, anchor=anchor):
                    doc = ROOT / "docs" / name
                    self.assertTrue(doc.is_file(), f"no docs/{name}")
                    if anchor:
                        self.assertIn(anchor, anchors(doc))


class LanguageSampleTests(unittest.TestCase):
    LANGUAGES = ROOT / "docs" / "languages.md"

    def sample(self, heading: str) -> dict:
        blocks = json_blocks(section(self.LANGUAGES, heading))
        self.assertEqual(len(blocks), 1, heading)
        # a fragment of site.json: its members, without the braces
        return json.loads("{" + blocks[0] + "}")

    def test_the_serbian_sample_is_complete(self):
        site = self.sample("A complete Serbian Latin example")
        self.assertEqual(site["lang"], "sr-Latn")
        self.assertIsNone(_locale.pack_name(site["lang"]))
        self.assertEqual(_locale.check_site(site), [])
        self.assertEqual(_locale.check_pack(site["strings"]), [])
        text = json.dumps(site["strings"], ensure_ascii=False)
        for letter in "čćšžđ":
            self.assertIn(letter, text)
        self.assertNotRegex(text, f"[{chr(0x400)}-{chr(0x4FF)}]")

    def test_the_us_sample_overrides_the_english_strings(self):
        site = self.sample("A US date format")
        self.assertEqual(_locale.check_site(site), [])
        self.assertEqual(_locale.check_pack(_locale.site_strings(site)), [])


class DataSampleTests(unittest.TestCase):
    def test_the_minimal_data_set_passes_validate(self):
        blocks = json_blocks(section(ROOT / "docs" / "data-format.md", "A minimal data set"))
        self.assertEqual(len(blocks), 2)
        site, invitations = (json.loads(block) for block in blocks)
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            (data / "site.json").write_text(json.dumps(site), encoding="utf-8")
            (data / "invitations.json").write_text(json.dumps(invitations), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "build.py"), "validate",
                 "--data", str(data), "--media", str(data / "media")],
                capture_output=True, text=True, check=False,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
            )  # fmt: skip
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn("validate: OK - 2 invitation(s), 1 event(s), 2 section(s)", result.stdout)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
