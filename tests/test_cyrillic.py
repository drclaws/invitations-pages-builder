"""Cyrillic only where it belongs.

The code, the docs and the main examples are English.  Cyrillic is allowed
in the Russian language pack, in the Russian example set and its tests, and
in a few robustness tests that need non-ASCII input of exactly this kind.
The tracked files of the repository are read from git; a copy without a git
work tree (e.g. `git archive`) skips the test.  The README images (real
PNG, JPEG or GIF files directly in `.github/assets/`) are not text and are
skipped.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.support import ROOT

CYRILLIC = re.compile(f"[{chr(0x400)}-{chr(0x4FF)}]")

#: Path -> None (the whole file is Russian on purpose) or the exact number of
#: lines with Cyrillic in it.
ALLOWED: dict[str, int | None] = {
    # the Russian language pack, the Russian example set and its tests
    "tools/locales/ru.json": None,
    "examples/data-ru/site.json": None,
    "examples/data-ru/invitations.json": None,
    "tests/fixtures_ru.py": None,
    "tests/test_dates_ru.py": None,
    "tests/test_example_pages_ru.py": None,
    "tests/test_link_preview_ru.py": None,
    "tests/test_locale_ru.py": None,
    "tests/test_page_tree_ru.py": None,
    # non-ASCII input on purpose: a media file name with a space and Cyrillic
    # letters, and a greeting with comment markers
    "tests/test_full_build.py": 5,
    # a token of Cyrillic letters
    "tests/test_cli.py": 1,
    # the address of a map service built from Cyrillic text
    "tests/test_maps.py": 5,
    # paths with Cyrillic letters, as written and percent-encoded
    "tests/test_output_checks.py": 2,
    # a fragment name with a Cyrillic letter that looks like a Latin one
    "tests/test_fragments.py": 1,
}


#: The README images: PNG, JPEG or GIF files directly in `.github/assets/`.
#: Their bytes are not text, so they are not read for Cyrillic.
README_IMAGE = re.compile(r"^\.github/assets/[^/]+\.(png|jpe?g|gif)$", re.I)
#: The first bytes of a real PNG, GIF or JPEG file.
SIGNATURES = (b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a", b"\xff\xd8\xff")


def git(*args: str) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=False)
    except OSError:
        return None


def tracked_files() -> list[str] | None:
    """The tracked files of the repository, or None without a git work tree
    of its own (a copy inside the work tree of another repository counts as
    none)."""
    top = git("rev-parse", "--show-toplevel")
    if top is None or top.returncode != 0:
        return None
    if Path(top.stdout.decode("utf-8").strip()).resolve() != ROOT.resolve():
        return None
    result = git("ls-files", "-z")
    if result is None or result.returncode != 0:
        return None
    return [name for name in result.stdout.decode("utf-8").split("\0") if name]


def cyrillic_lines(path: str, root: Path = ROOT) -> list[int]:
    """The numbers of the lines of a file that have Cyrillic in them."""
    text = (root / path).read_bytes().decode("utf-8", errors="replace")
    return [number for number, line in enumerate(text.splitlines(), start=1) if CYRILLIC.search(line)]


def is_readme_image(path: str, root: Path = ROOT) -> bool:
    """Whether a file is a README image: named as one and starting with the
    signature of a real image."""
    if not README_IMAGE.search(path):
        return False
    with (root / path).open("rb") as handle:
        return handle.read(8).startswith(SIGNATURES)


class CyrillicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        files = tracked_files()
        if files is None:
            raise unittest.SkipTest("not a git work tree: the tracked files are unknown")
        cls.files = [path for path in files if not is_readme_image(path)]

    def test_only_real_readme_images_are_skipped(self):
        cyrillic = b"\xd0\x9f\xd1\x80\xd0\xb8\n"  # three Cyrillic letters in UTF-8
        # path -> (contents, skipped)
        cases = {
            # a real image in the README directory: skipped
            ".github/assets/demo.gif": (b"GIF89a" + cyrillic, True),
            ".github/assets/screen.PNG": (b"\x89PNG\r\n\x1a\n" + cyrillic, True),
            ".github/assets/still.jpg": (b"\xff\xd8\xff\xe0" + cyrillic, True),
            # a text file named as an image: read
            ".github/assets/fake.png": (cyrillic, False),
            # a real image elsewhere, or deeper: read
            "docs/screen.png": (b"\x89PNG\r\n\x1a\n" + cyrillic, False),
            ".github/assets/more/demo.gif": (b"GIF89a" + cyrillic, False),
            # not an image name
            ".github/assets/notes.txt": (b"GIF89a" + cyrillic, False),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path, (content, skipped) in cases.items():
                with self.subTest(path=path):
                    (root / path).parent.mkdir(parents=True, exist_ok=True)
                    (root / path).write_bytes(content)
                    self.assertEqual(is_readme_image(path, root), skipped)
                    # read or not, the file has Cyrillic in it
                    self.assertTrue(cyrillic_lines(path, root))
        self.assertFalse(is_readme_image("README.md"))

    def test_no_cyrillic_outside_the_allowed_files(self):
        found = [
            f"{path}:{number}"
            for path in self.files
            if path not in ALLOWED
            for number in cyrillic_lines(path)
        ]
        # the place only, never the text
        self.assertEqual(found, [], "Cyrillic outside the allowed files")

    def test_the_counted_files_keep_their_lines(self):
        for path, count in ALLOWED.items():
            if count is None or path not in self.files:
                continue
            with self.subTest(path=path):
                lines = cyrillic_lines(path)
                self.assertEqual(len(lines), count, f"lines with Cyrillic: {lines}")

    def test_every_allowed_file_exists_and_has_cyrillic(self):
        for path in ALLOWED:
            with self.subTest(path=path):
                self.assertIn(path, self.files, "a stale entry: the file is not tracked")
                self.assertTrue(cyrillic_lines(path), "a stale entry: the file has no Cyrillic")

    def test_this_file_has_none(self):
        self.assertEqual(cyrillic_lines("tests/test_cyrillic.py"), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
