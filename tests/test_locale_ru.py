"""The pages in Russian, end to end: the main example set (`"lang": "ru"`)
built with the real template, fragments and assets; the words, dates and
labels come from the built-in `ru` pack."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from tests import support
from tests.support import build
from tests.test_locale import CHROME, LEFT_SECONDS, plural_category, shipped_strings
from tools import _locale

ROOT = support.ROOT
DATA = ROOT / "examples" / "data"
#: The main set links to a directory of its fictional site that is not built.
ALLOW_PATHS = ("/photos",)
#: The first invitation of the main set: it sees every event.
TOKEN = "0R-pnCqGFgrPOR5e-NluZw"


class RussianExampleTests(unittest.TestCase):
    page: str
    out: Path

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="invite-locale-ru-"))
        site = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
        names = sorted(
            {item[key] for item in site["media"].values()
             for key in ("file", "poster", "thumb") if key in item}
        )  # fmt: skip
        media = support.write_media(cls.tmp / "media", names)
        cls.out = cls.tmp / "dist"
        cls.log: list[str] = []
        build.build_site(
            DATA, media, cls.out, code_dir=ROOT, log=cls.log.append,
            preview=build.PreviewOptions(enabled=False), allow_paths=ALLOW_PATHS,
        )  # fmt: skip
        cls.site = site
        cls.page = (cls.out / TOKEN / "index.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_example_is_in_russian(self):
        self.assertEqual(self.site["lang"], "ru")
        self.assertEqual(list(self.site)[:2], ["schemaVersion", "lang"])
        self.assertIn("build: language: ru", self.log)

    def test_the_head(self):
        for text in ('<html lang="ru" class="invitation">',
                     "<title>Приглашение · Алиса и Боб</title>",
                     '<meta property="og:title" content="Приглашение · Алиса и Боб">',
                     '<meta property="og:image:alt" content="Приглашение · Алиса и Боб">',
                     '<meta property="og:locale" content="ru_RU">'):  # fmt: skip
            with self.subTest(text=text):
                self.assertIn(text, self.page)

    def test_the_dates(self):
        for text in (
            'cover__date"><time datetime="2030-06-15T16:00:00+03:00">15 июня 2030</time>',
            'date__text"><time datetime="2030-06-15T16:00:00+03:00">15 июня 2030, 16:00</time>',
            ">Суббота, 15 июня 2030, 11:00</time>",
            ">Суббота, 15 июня 2030, 16:00–23:30</time>",
            ">Воскресенье, 16 июня 2030, 12:00</time>",
            ">15 июня, 11:00</time>",
            ">16 июня, 12:00</time>",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.page)

    def test_the_labels(self):
        for text in ('aria-label="Осталось до начала"', ">дней</span>", ">часов</span>",
                     ">минут</span>", ">секунд</span>", ">Добавить в календарь</a>",
                     ">Программа</h4>", ">Схема проезда", 'aria-label="Открыть на карте"',
                     ">Google Карты</a>", ">Яндекс Карты</a>", ">Apple Карты</a>",
                     ">прошло</span>", ">событие прошло</span>", ">идёт сейчас</span>"):  # fmt: skip
            with self.subTest(text=text):
                self.assertIn(text, self.page)
        # the label of a video tile: the word of the pack, the description, the duration
        self.assertRegex(self.page, r'aria-label="Видео: Видео предложения, 0:\d\d"')

    def test_the_script_gets_the_russian_strings(self):
        strings = shipped_strings(self.out)
        self.assertEqual(strings, _locale.script_strings(_locale.pack("ru")))
        for unit, forms in (("days", ("день", "дня", "дней")), ("hours", ("час", "часа", "часов")),
                            ("minutes", ("минута", "минуты", "минут")),
                            ("seconds", ("секунда", "секунды", "секунд"))):  # fmt: skip
            with self.subTest(unit=unit):
                self.assertEqual(
                    strings["countdown"][unit],
                    {"one": forms[0], "few": forms[1], "many": forms[2], "other": forms[1]},
                )
        self.assertEqual(strings["lightbox"]["position"], "{item} {n} из {total}")
        self.assertEqual(strings["lightbox"]["nextItem"], "Вперёд")

    @unittest.skipUnless(CHROME, "Chrome or Chromium is not installed")
    def test_the_countdown_in_a_real_browser(self):
        start = self.site["events"][self.site["mainEvent"]]["start"]
        found = support.countdown_in_browser(self.out, f"{TOKEN}/", CHROME, start, LEFT_SECONDS)
        self.assertEqual(found["lang"], "ru")
        self.assertTrue(found["shown"])
        # 1 day, 2 hours, 5 minutes and about 21 seconds
        self.assertEqual([cell[1] for cell in found["cells"]][:3], ["1", "02", "05"])
        self.assertEqual([cell[2] for cell in found["cells"]][:3], ["день", "часа", "минут"])
        forms = _locale.pack("ru")["countdown"]
        for unit, value, label in found["cells"]:
            with self.subTest(unit=unit, value=value):
                self.assertEqual(label, forms[unit][plural_category("ru", int(value))])

    def test_the_pack_holds_the_russian_words(self):
        russian = _locale.pack("ru")
        self.assertEqual(russian["months"][5], "июня")
        self.assertEqual(russian["weekdays"][5], "суббота")
        self.assertEqual(russian["rangeOtherDay"], "{when} — {endDay}, {endTime}")
        self.assertEqual(
            russian["countdown"]["days"],
            {"one": "день", "few": "дня", "many": "дней", "other": "дня"},
        )
        self.assertEqual(russian["lightbox"]["position"], "{item} {n} из {total}")
        # nothing Russian is left in the code of the dates and the pages
        for path in (ROOT / "tools" / "_dates.py", ROOT / "tools" / "_page.py"):
            self.assertNotRegex(path.read_text(encoding="utf-8"), r"[а-яё]")


class RussianPendingTests(unittest.TestCase):
    def test_the_place_not_announced_yet(self):
        tmp = Path(tempfile.mkdtemp(prefix="invite-locale-ru-pending-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        out = tmp / "dist"
        build.build_site(
            ROOT / "examples" / "data-venue-pending", ROOT / "examples" / "media-none", out,
            code_dir=ROOT, log=lambda _line: None, preview=build.PreviewOptions(enabled=False),
        )  # fmt: skip
        page = (out / "quokka" / "index.html").read_text(encoding="utf-8")
        self.assertIn("<p>Подробности появятся на этой странице позже.</p>", page)
        self.assertIn('<html lang="ru" class="invitation">', page)
        self.assertRegex(page, re.escape("10 августа 2030"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
