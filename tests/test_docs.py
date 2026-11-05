"""The docs: every tracked Markdown file (`README.md`, `docs/*.md`, the
credits of the README images in `.github/assets/`).

Every relative link leads to a file of the repository and every `#anchor`
to a heading of its file (with the slugs GitHub gives headings); there is
no HTML outside code; the README shows every README image with a text;
every doc that the code cites in a message exists, with its anchor; the
samples that the docs present as valid pass the checks.
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
from tests.test_cyrillic import README_IMAGE
from tools import _locale

DOCS = sorted((ROOT / "docs").glob("*.md"))
#: The README images and their credits.
ASSETS = ".github/assets/"
CREDITS = ASSETS + "README.md"

#: The opening line of a fenced code block: up to three spaces, then three or
#: more backticks or tildes (a backtick fence has no backtick after them).
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}(?=[^`]*$)|~{3,})")
_CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
#: A code span, also one that goes on to the next lines of its paragraph.
_MULTILINE_CODE_SPAN_RE = re.compile(r"`(?:[^`\n]|\n(?![ \t]*\n))*`")
_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
#: A Markdown image: its text (group 1) and its target (group 2).
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
#: An HTML tag or comment; an autolink such as `<https://…>` is not one.
_HTML_RE = re.compile(r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?/?>|<!--")
#: A backslash escape of an ASCII punctuation character: `\<p>` is the text `<p>`.
_ESCAPE_RE = re.compile(r"\\[!-/:-@\[-`{-~]")
#: The target of an HTML link or image (`<a href>`, `<img src>`), in double
#: or single quotes (group 2).
_HTML_LINK_RE = re.compile(r"""<(?:a|img)\b[^>]*?\s(?:href|src)=(["'])(.*?)\1""")
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$", re.M)
_JSON_BLOCK_RE = re.compile(r"^```json[ \t]*\n(.*?)^```", re.M | re.S)
#: A doc cited by the code: `docs/<name>.md`, maybe with an anchor.
_CITATION_RE = re.compile(r"docs/([a-z0-9-]+\.md)(?:#([A-Za-z0-9_-]+))?")


def blank(text: str) -> str:
    """The text with every character but the line breaks made a space."""
    return re.sub(r"[^\n]", " ", text)


def without_code(text: str) -> str:
    """The text with its fenced blocks blanked out (same length, same
    lines): their lines are neither headings nor links.

    A fence is indented by up to three spaces (so it may sit in a list item)
    and made of backticks or tildes; it is closed only by a line of the same
    character, at least as long, with nothing after it, or by the end of the
    file. Code blocks indented by four spaces are not recognised: the docs
    use fences only."""
    lines = text.splitlines(keepends=True)
    fence = ""
    for number, line in enumerate(lines):
        if fence:
            lines[number] = blank(line)
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + r"{%d,}[ \t]*\r?\n?" % len(fence), line):
                fence = ""
        elif found := _FENCE_OPEN_RE.match(line):
            fence = found.group(1)
            lines[number] = blank(line)
    return "".join(lines)


def without_inline_code(text: str) -> str:
    """The text without its fenced blocks, code spans (also those that go on
    to the next lines of their paragraph) and backslash escapes, blanked out:
    what is left is rendered as Markdown or HTML."""
    text = _MULTILINE_CODE_SPAN_RE.sub(lambda match: blank(match.group(0)), without_code(text))
    return _ESCAPE_RE.sub(lambda match: blank(match.group(0)), text)


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
    """The link and image targets of a Markdown file, outside code, in
    Markdown and in HTML."""
    text = _CODE_SPAN_RE.sub("", without_code(path.read_text(encoding="utf-8")))
    return _LINK_RE.findall(text) + [match.group(2) for match in _HTML_LINK_RE.finditer(text)]


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


def markdown_files() -> list[Path]:
    """Every tracked Markdown file, or, outside a git work tree of its own,
    the README, the docs and the Markdown files in `.github/`."""
    tracked = tracked_files()
    if tracked is None:
        return [ROOT / "README.md", *sorted((ROOT / ".github").rglob("*.md")), *DOCS]
    return [ROOT / name for name in sorted(tracked) if name.lower().endswith(".md")]


MARKDOWN = markdown_files()


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

    def test_the_readme_shows_every_readme_image(self):
        """`.github/assets/` holds the README images and their credits; the
        README shows every image once, as a Markdown image with a text, and
        links to the credits."""
        if self.tracked is None:
            present = {path.relative_to(ROOT).as_posix()
                       for path in (ROOT / ".github" / "assets").glob("*") if path.is_file()}  # fmt: skip
        else:
            present = {name for name in self.tracked if name.startswith(ASSETS)}
        images = present - {CREDITS}
        self.assertTrue(images)
        for name in images:
            self.assertRegex(name, README_IMAGE)
        text = _CODE_SPAN_RE.sub("", without_code((ROOT / "README.md").read_text(encoding="utf-8")))
        shown = [(alt, target) for alt, target in _IMAGE_RE.findall(text) if target.startswith(ASSETS)]
        self.assertEqual(sorted(target for _alt, target in shown), sorted(images))
        for alt, target in shown:
            with self.subTest(image=target):
                self.assertTrue(alt.strip(), "an image without a text")
        if CREDITS in present:
            self.assertIn(CREDITS, links(ROOT / "README.md"))

    def test_every_markdown_file_is_checked(self):
        checked = {path.relative_to(ROOT).as_posix() for path in MARKDOWN}
        self.assertIn("README.md", checked)
        for path in DOCS:
            self.assertIn(f"docs/{path.name}", checked)
        if (ROOT / CREDITS).is_file():
            self.assertIn(CREDITS, checked)

    def test_no_html_outside_code(self):
        for path in MARKDOWN:
            text = without_inline_code(path.read_text(encoding="utf-8"))
            found = [f"{text.count(chr(10), 0, match.start()) + 1}: {match.group(0)}"
                     for match in _HTML_RE.finditer(text)]  # fmt: skip
            with self.subTest(file=path.relative_to(ROOT).as_posix()):
                self.assertEqual(found, [])

    def test_html_and_images_are_found(self):
        text = ("A <sub>small</sub> `<b>code</b>` text <!-- a note --> and <https://example.org>\n"
                "```\n<p>code</p>\n```\n"
                "with `a span that goes\non <i>`. ![A demo](.github/assets/a.gif)\n"
                "An escaped \\<p> is text, an escaped backslash \\\\<em>x</em> is not.\n")  # fmt: skip
        plain = without_inline_code(text)
        self.assertEqual(_HTML_RE.findall(plain), ["<sub>", "</sub>", "<!--", "<em>", "</em>"])
        self.assertEqual(len(plain), len(text))
        self.assertEqual(_IMAGE_RE.findall(text), [("A demo", ".github/assets/a.gif")])

    def test_fences_are_found(self):
        cases = {
            # tildes, and backticks inside them that close nothing
            "~~~\n<p>\n```\n<b>\n~~~\n<i>\n": ["<i>"],
            # an indented fence in a list item, with a blank line inside
            "1. Run:\n\n  ```bash\n  <p>\n\n  <b>\n  ```\n2. <i>\n": ["<i>"],
            # closed only by the same character, at least as long
            "````\n<p>\n```\n~~~~\n<b>\n````\n<i>\n": ["<i>"],
            # a closing line has nothing after the fence
            "```\n<p>\n``` x\n<b>\n```\n<i>\n": ["<i>"],
            # not a fence: four spaces, two backticks, a backtick after a backtick fence
            "    ```\n<p>\n": ["<p>"],
            "``\n<p>\n": ["<p>"],
            "``` a`b\n<p>\n": ["<p>"],
            # an unclosed fence runs to the end of the file
            "<i>\n```\n<p>\n": ["<i>"],
        }
        for text, found in cases.items():
            with self.subTest(text=text):
                plain = without_code(text)
                self.assertEqual(len(plain), len(text))
                self.assertEqual(_HTML_RE.findall(plain), found)

    def test_html_targets_are_found(self):
        text = ('<p><a href="docs/cli.md"><img src=".github/assets/a.gif" alt="A" width="300"></a>'
                "<img alt='B' src='.github/assets/b.png'></p>")
        self.assertEqual([match.group(2) for match in _HTML_LINK_RE.finditer(text)],
                         ["docs/cli.md", ".github/assets/a.gif", ".github/assets/b.png"])

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
