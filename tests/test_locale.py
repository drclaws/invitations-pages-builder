"""The language of the pages (`tools/_locale.py`): the built-in packs,
`site.json` `lang` and `strings`, their checks, the merge, the page tree and
the build in a language with a pack and in one without."""

from __future__ import annotations

import copy
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from tests import fixtures_v2 as F
from tests import support
from tests.support import CliTestCase, build
from tools import _locale, _page, _preview, _schema

REAL_TEMPLATE = (support.ROOT / build.TEMPLATE_FILE).read_text(encoding="utf-8")
#: Any letter of the Cyrillic block (U+0400 to U+04FF).
CYRILLIC = re.compile(f"[{chr(0x400)}-{chr(0x4FF)}]")

#: A complete set of strings for a language without a pack: fictional
#: Serbian in the Latin script.
SERBIAN = {
    "ogLocale": "sr_RS",
    "invitationTitle": "Pozivnica",
    "addToCalendar": "Dodaj u kalendar",
    "programme": "Raspored",
    "directions": "Plan dolaska",
    "placePending": "Detalji će se pojaviti na ovoj stranici kasnije.",
    "openOnMap": "Prikaži na mapi",
    "mapGoogle": "Google mape",
    "mapYandex": "Jandeks mape",
    "mapApple": "Apple mape",
    "past": "prošlo",
    "eventPast": "događaj je završen",
    "now": "u toku",
    "countdownLabel": "Preostalo do početka",
    "countdownDays": "dana",
    "countdownHours": "sati",
    "countdownMinutes": "minuta",
    "countdownSeconds": "sekundi",
    "photo": "Fotografija",
    "video": "Snimak",
    "months": ["januara", "februara", "marta", "aprila", "maja", "juna", "jula", "avgusta",
               "septembra", "oktobra", "novembra", "decembra"],
    "weekdays": ["ponedeljak", "utorak", "sreda", "četvrtak", "petak", "subota", "nedelja"],
    "date": "{d}. {month} {yyyy}.",
    "dayMonth": "{d}. {month}",
    "time": "{H}:{mm}",
    "ampm": ["pre podne", "po podne"],
    "dateTime": "{date} u {time}",
    "when": "{Weekday}, {date}, {time}",
    "rangeSameDay": "{when}–{endTime}",
    "rangeOtherDay": "{when} – {endDay}, {endTime}",
    "tab": "{dayMonth}, {time}",
    "countdown": {
        "days": {"one": "dan", "few": "dana", "other": "dana"},
        "hours": {"one": "sat", "few": "sata", "other": "sati"},
        "minutes": {"one": "minut", "few": "minuta", "other": "minuta"},
        "seconds": {"one": "sekunda", "few": "sekunde", "other": "sekundi"},
    },
    "lightbox": {
        "photos": "Pregled fotografija",
        "mixed": "Pregled fotografija i snimaka",
        "image": "Pregled slike",
        "video": "Pregled snimka",
        "close": "Zatvori",
        "prev": "Prethodna fotografija",
        "next": "Sledeća fotografija",
        "prevItem": "Nazad",
        "nextItem": "Napred",
        "itemImage": "Fotografija",
        "itemVideo": "Snimak",
        "loading": "Učitavanje…",
        "error": "Slika nije mogla da se učita.",
        "videoError": "Snimak nije mogao da se učita.",
        "position": "{item} {n} od {total}",
    },
}  # fmt: skip


def site_errors(**changes) -> list[str]:
    """The errors of the fixture `site.json` with `changes` at its top level
    (a value of None removes the field)."""
    site = F.site()
    for key, value in changes.items():
        if value is None:
            site.pop(key, None)
        else:
            site[key] = copy.deepcopy(value)
    report = F.Collector()
    _schema.check_site(site, report)
    return report.errors


def without(strings: dict, *keys: str) -> dict:
    """A copy of `strings` without the dotted keys."""
    result = copy.deepcopy(strings)
    for key in keys:
        group, _dot, name = key.partition(".")
        if name:
            del result[group][name]
        else:
            del result[key]
    return result


class PackTests(unittest.TestCase):
    def test_the_packs(self):
        self.assertEqual(_locale.packs(), frozenset({"en", "ru"}))
        self.assertEqual(_locale.DEFAULT_LANG, "en")

    def test_the_packs_have_the_same_keys_of_the_same_kinds(self):
        def keys(strings):
            return sorted(
                f"{key}.{name}" if isinstance(value, dict) and key in _locale.GROUPS else key
                for key, value in strings.items()
                for name in (value if key in _locale.GROUPS else [None])
            )

        english, russian = _locale.pack("en"), _locale.pack("ru")
        self.assertEqual(keys(english), sorted(_locale.KEY_PATHS))
        self.assertEqual(keys(russian), keys(english))
        for name in ("en", "ru"):
            with self.subTest(pack=name):
                self.assertEqual(_locale.check_pack(_locale.pack(name)), [])
        # the packs read alike: the keys in the same order
        self.assertEqual(list(russian), list(english))
        self.assertEqual(list(russian["lightbox"]), list(english["lightbox"]))
        # a pack without a key is incomplete
        self.assertEqual(
            _locale.check_pack(without(english, "tab", "countdown.days")),
            [_locale.Problem((), "misses the keys countdown.days, tab")],
        )

    def test_the_kinds_of_the_keys(self):
        english = _locale.pack("en")
        for key in (*_locale.LABELS, *_locale.TEXTS):
            self.assertIsInstance(english[key], str)
        self.assertEqual(len(english["months"]), 12)
        self.assertEqual(english["weekdays"][0], "Monday")
        self.assertEqual(english["ampm"], ["am", "pm"])
        for unit in _locale.COUNTDOWN_UNITS:
            self.assertIn("other", english["countdown"][unit])
        self.assertEqual(english["lightbox"]["position"], "{item} {n} of {total}")
        # the labels of the page tree
        self.assertEqual(set(_locale.ui_labels(english)), set(_locale.LABELS))
        self.assertEqual(set(_locale.script_strings(english)), {"countdown", "lightbox"})

    def test_a_pack_is_a_copy(self):
        _locale.pack("en")["months"][0] = "changed"
        self.assertEqual(_locale.pack("en")["months"][0], "January")


class ResolutionTests(unittest.TestCase):
    def test_the_primary_subtag_picks_the_pack(self):
        for tag, name in (("en", "en"), ("en-US", "en"), ("EN-gb", "en"), ("ru", "ru"),
                          ("ru-RU", "ru"), ("sr-Latn", None), ("de", None)):  # fmt: skip
            with self.subTest(tag=tag):
                self.assertEqual(_locale.pack_name(tag), name)
        self.assertEqual(_locale.site_strings({"lang": "ru-RU"}), _locale.pack("ru"))
        self.assertEqual(_locale.site_strings({"lang": "en-US"}), _locale.pack("en"))
        self.assertEqual(_locale.site_strings({}), _locale.pack("en"))

    def test_the_groups_merge_key_by_key(self):
        strings = _locale.site_strings({"strings": {"lightbox": {"close": "Shut"}}})
        expected = dict(_locale.pack("en")["lightbox"], close="Shut")
        self.assertEqual(strings["lightbox"], expected)

    def test_lists_and_plural_forms_replace_the_value_of_the_pack(self):
        strings = _locale.site_strings({
            "strings": {"ampm": ["AM", "PM"], "countdown": {"days": {"other": "d"}}}
        })  # fmt: skip
        self.assertEqual(strings["ampm"], ["AM", "PM"])
        self.assertEqual(strings["countdown"]["days"], {"other": "d"})
        # the other units stay those of the pack
        self.assertEqual(strings["countdown"]["hours"], {"one": "hour", "other": "hours"})

    def test_a_partial_override_of_a_pack(self):
        site = {"lang": "en", "strings": {"addToCalendar": "Save the date"}}
        strings = _locale.site_strings(site)
        self.assertEqual(strings["addToCalendar"], "Save the date")
        self.assertEqual(strings["programme"], "Programme")
        self.assertEqual(site_errors(lang="en", strings={"addToCalendar": "Save the date"}), [])
        # the Russian pack, too (the fixture is in Russian)
        self.assertEqual(site_errors(strings={"invitationTitle": "Invite"}), [])

    def test_a_language_without_a_pack_takes_the_strings_as_they_are(self):
        self.assertEqual(_locale.site_strings({"lang": "sr-Latn", "strings": SERBIAN}), SERBIAN)

    def test_the_script_strings_on_one_line(self):
        separators = (chr(0x2028), chr(0x2029))  # line and paragraph separators
        close = f"a{separators[0]}b{separators[1]}c"
        strings = _locale.merge(_locale.pack("en"), {"lightbox": {"close": close}})
        line = _locale.script_json(strings)
        for separator in separators:
            self.assertNotIn(separator, line)
        self.assertIn("a\\u2028b\\u2029c", line)
        self.assertNotIn("\n", line)
        self.assertIn('"loading":"Loading…"', line)  # letters as they are
        self.assertTrue(line.startswith('{"countdown":{"days":{"one":"day","other":"days"}'))

    def test_the_log(self):
        self.assertEqual(_locale.describe_lang({}), "en (default)")
        self.assertEqual(_locale.describe_lang({"lang": "en"}), "en")
        self.assertEqual(_locale.describe_lang({"lang": "sr-Latn"}), "sr-Latn")


class CheckTests(unittest.TestCase):
    """The messages of `validate` about `lang` and `strings`."""

    def test_valid_tags(self):
        for tag in ("en", "ru", "en-US", "sr-Latn", "sr-Latn-RS", "es-419", "de-CH-1996",
                    "zh-Hant-TW", "haw"):  # fmt: skip
            with self.subTest(tag=tag):
                # a language without a pack needs every key: given here
                strings = SERBIAN if _locale.pack_name(tag) is None else None
                self.assertEqual(site_errors(lang=tag, strings=strings), [])

    def test_a_bad_tag(self):
        expected = [
            "site.json: field 'lang' must be a language tag such as 'en', 'ru' or 'sr-Latn'"
        ]
        for tag in ("english", "e", "en_GB", "", " en", "en-", "en--US", "ru-RU-", 5, None, []):
            if tag is None:
                continue
            with self.subTest(tag=tag):
                self.assertEqual(site_errors(lang=tag), expected)

    def test_a_language_without_a_pack_needs_every_key(self):
        self.assertEqual(site_errors(lang="sr-Latn", strings=SERBIAN), [])
        errors = site_errors(
            lang="sr-Latn",
            strings=without(SERBIAN, "lightbox.position", "addToCalendar", "countdown.days"),
        )
        self.assertEqual(
            errors,
            [
                "site.json: field 'strings' must give every key for 'sr-Latn', which has no "
                "built-in strings; missing: addToCalendar, countdown.days, lightbox.position"
            ],
        )
        # no strings at all: one message with every key
        errors = site_errors(lang="de")
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith(
            "site.json: field 'strings' must give every key for 'de', which has no built-in "
            "strings; missing: addToCalendar, ampm, countdown.days, countdown.hours, "
        ))  # fmt: skip
        listed = errors[0].partition("; missing: ")[2].split(", ")
        self.assertEqual(listed, sorted(_locale.KEY_PATHS))

    def test_a_broken_key_is_not_missing_too(self):
        strings = dict(SERBIAN, countdown="dana", months=["januara"])
        self.assertEqual(
            site_errors(lang="sr-Latn", strings=strings),
            [
                "site.json: field 'strings.months' must be a list of 12 strings",
                "site.json: field 'strings.countdown' must be an object, got a string",
            ],
        )
        self.assertEqual(
            site_errors(lang="sr-Latn", strings=[]),
            ["site.json: field 'strings' must be an object, got an array"],
        )

    def test_unknown_keys_with_a_hint(self):
        self.assertEqual(
            site_errors(strings={
                "adToCalendar": "x",
                "lightbox": {"closee": "x"},
                "countdown": {"day": {"other": "x"}, "hours": {"other": "x", "others": "y"}},
            }),
            [
                "site.json: unknown field 'strings.adToCalendar' (did you mean 'addToCalendar'?)",
                "site.json: unknown field 'strings.lightbox.closee' (did you mean 'close'?)",
                "site.json: unknown field 'strings.countdown.day' (did you mean 'days'?)",
                "site.json: unknown field 'strings.countdown.hours.others' (did you mean "
                "'other'?)",
            ],
        )  # fmt: skip

    def test_labels_are_single_lines(self):
        for value, problem in (
            (5, "must be a string, got a number"),
            ("", "must not be empty"),
            ("  ", "must not be empty"),
            ("a\nb", "must be a single line (no line breaks)"),
        ):
            with self.subTest(value=value):
                self.assertEqual(
                    site_errors(strings={"programme": value, "lightbox": {"close": value}}),
                    [
                        f"site.json: field 'strings.programme' {problem}",
                        f"site.json: field 'strings.lightbox.close' {problem}",
                    ],
                )

    def test_lists(self):
        for key, value, problem in (
            ("months", ["a"] * 11, "must be a list of 12 strings"),
            ("months", "January", "must be a list of 12 strings"),
            ("weekdays", ["a"] * 6 + [1], "must be a list of 7 strings, Monday first"),
            ("ampm", ["am", "pm", "noon"], "must be a list of 2 strings"),
        ):
            with self.subTest(key=key, value=value):
                self.assertEqual(
                    site_errors(strings={key: value}), [f"site.json: field 'strings.{key}' {problem}"]
                )
        months = list(_locale.pack("en")["months"])
        months[3] = ""
        self.assertEqual(
            site_errors(strings={"months": months}),
            ["site.json: field 'strings.months[3]' must not be empty"],
        )

    def test_plural_forms(self):
        problem = (
            "must be an object of plural forms (zero, one, two, few, many, other) with at "
            "least 'other'"
        )
        for value in ("days", ["day", "days"], {"one": "day"}, {}):
            with self.subTest(value=value):
                self.assertEqual(
                    site_errors(strings={"countdown": {"days": value}}),
                    [f"site.json: field 'strings.countdown.days' {problem}"],
                )
        self.assertEqual(
            site_errors(strings={"countdown": {"days": {"other": "", "zero": "no days"}}}),
            ["site.json: field 'strings.countdown.days.other' must not be empty"],
        )
        # the categories of the plural rules, whatever the language uses
        every = dict.fromkeys(_locale.PLURAL_CATEGORIES, "x")
        self.assertEqual(site_errors(strings={"countdown": {"days": every}}), [])

    def test_patterns(self):
        known_date = "known: {d}, {dd}, {M}, {MM}, {month}, {yyyy}, {weekday}, {Weekday}"
        for key, value, problems in (
            ("date", "{d} {month}", ["must contain the placeholder {yyyy}"]),
            ("date", "{day} {month} {yyyy}", [
                f"has an unknown placeholder {{day}}; {known_date}",
                "must contain the placeholder {d} or {dd}",
            ]),
            ("dayMonth", "{d}", ["must contain the placeholder {M}, {MM} or {month}"]),
            ("time", "{H} h", ["must contain the placeholder {mm}"]),
            ("time", "{mm} min", ["must contain the placeholder {H}, {HH}, {h} or {hh}"]),
            ("dateTime", "{date}", ["must contain the placeholder {time}"]),
            ("when", "{date} {time", ["has a brace that is not part of a placeholder"]),
            ("when", "{date}, {time} {{x}}", ["has a brace that is not part of a placeholder"]),
            ("rangeSameDay", "{when}-{end}", [
                "has an unknown placeholder {end}; known: {when}, {endTime}",
                "must contain the placeholder {endTime}",
            ]),
            ("rangeOtherDay", "{when} - {endTime}", ["must contain the placeholder {endDay}"]),
            ("tab", "{dayMonth}", ["must contain the placeholder {time}"]),
            ("tab", "", ["must not be empty"]),
        ):  # fmt: skip
            with self.subTest(key=key, value=value):
                self.assertEqual(
                    site_errors(strings={key: value}),
                    [f"site.json: field 'strings.{key}' {problem}" for problem in problems],
                )
        self.assertEqual(
            site_errors(strings={"lightbox": {"position": "{n}"}}),
            ["site.json: field 'strings.lightbox.position' must contain the placeholder {total}"],
        )
        # the other placeholders a pattern may use
        self.assertEqual(
            site_errors(strings={
                "date": "{Weekday} {dd}.{MM}.{yyyy}", "time": "{hh}:{mm} {ampm}",
                "when": "{weekday} {dayMonth} {date} {time}", "tab": "{date} {Weekday} {time}",
                "lightbox": {"position": "{n}/{total}"},
            }),
            [],
        )  # fmt: skip

    def test_a_long_unknown_name_is_not_shown(self):
        name = "x" * 40
        self.assertEqual(
            site_errors(strings={"tab": f"{{{name}}} {{time}}"}),
            [
                "site.json: field 'strings.tab' has an unknown placeholder; known: {time}, "
                "{dayMonth}, {date}, {weekday}, {Weekday}"
            ],
        )


class PageTreeTests(unittest.TestCase):
    def tree(self, site: dict, index: int = 0) -> dict:
        report = F.Collector()
        self.assertTrue(_schema.check_data(site, F.invitations(), report).ok, report.errors)
        return _page.build_pages(site, F.invitations(), F.settings())[0][index]

    def test_english_by_default(self):
        site = F.site()
        self.assertNotIn("lang", site)
        tree = self.tree(site)
        self.assertEqual((tree["lang"], tree["ogLocale"]), ("en", "en_GB"))
        self.assertEqual(tree["ui"], _locale.ui_labels(_locale.pack("en")))
        event = tree["primaryEvent"]
        self.assertEqual(
            (event["dateText"], event["timeText"], event["dateTimeText"]),
            ("15 June 2030", "16:00", "15 June 2030, 16:00"),
        )
        self.assertEqual(_page.site_cover(site, F.settings())["lang"], "en")

    def test_the_tag_as_written(self):
        site = F.site()
        site["lang"] = "ru-RU"
        tree = self.tree(site)
        self.assertEqual(tree["lang"], "ru-RU")
        self.assertEqual(tree["ui"], _locale.ui_labels(_locale.pack("ru")))
        self.assertEqual(_page.site_cover(site, F.settings())["lang"], "ru-RU")

    def test_the_media_labels(self):
        site = F.site()
        site["lang"] = "en"
        site["media"]["story-1"].pop("alt")
        site["media"]["proposal"].pop("alt")
        tree = self.tree(site)
        items = {
            item["id"]: item for section in tree["sections"] if section["id"] == "story"
            for widget in section["widgets"] if widget["type"] == "media"
            for item in widget["items"]
        }  # fmt: skip
        self.assertEqual((items["story-1"]["alt"], items["story-1"]["label"]), ("Photo", "Photo"))
        self.assertEqual((items["proposal"]["alt"], items["proposal"]["label"]), ("Video", "Video, 0:20"))
        site["media"]["proposal"]["alt"] = "The proposal"
        tree = self.tree(site)
        labels = [
            item["label"] for section in tree["sections"] for widget in section["widgets"]
            if widget["type"] == "media" for item in widget["items"] if item["id"] == "proposal"
        ]  # fmt: skip
        self.assertEqual(labels, ["Video: The proposal, 0:20"])

    def test_a_language_without_a_pack(self):
        site = F.site()
        site["lang"], site["strings"] = "sr-Latn", SERBIAN
        tree = self.tree(site)
        self.assertEqual((tree["lang"], tree["ogLocale"]), ("sr-Latn", "sr_RS"))
        self.assertEqual(tree["ui"]["addToCalendar"], "Dodaj u kalendar")
        self.assertEqual(tree["primaryEvent"]["dateTimeText"], "15. juna 2030. u 16:00")
        # the dinner shows its end (`showEnd`)
        self.assertEqual(tree["primaryEvent"]["whenText"], "Subota, 15. juna 2030., 16:00–23:30")


class SourcesTests(unittest.TestCase):
    def test_the_markup_and_the_page_code_have_no_words_of_a_language(self):
        root = support.ROOT
        paths = [root / "template.html", root / "preview.html", root / "tools" / "_page.py",
                 root / "tools" / "_dates.py", root / ".github" / "workflows" / "ci.yml",
                 *sorted((root / "fragments").rglob("*.html"))]  # fmt: skip
        for path in paths:
            with self.subTest(path=path.relative_to(root).as_posix()):
                self.assertNotRegex(path.read_text(encoding="utf-8"), CYRILLIC)


SCRIPT = support.ROOT / "assets" / build.SCRIPT_FILE
#: The line of the page script that holds the strings.
STRINGS_LINE = re.compile(r"(?m)^  var STRINGS = (.*); /\* @strings \*/$")
CHROME = _preview.find_chrome()


def shipped_strings(out) -> dict:
    """The script strings of a built page script."""
    text = (out / "assets" / build.SCRIPT_FILE).read_text(encoding="utf-8")
    found = STRINGS_LINE.findall(text)
    assert len(found) == 1, len(found)
    return json.loads(found[0])


def plural_category(lang: str, count: int) -> str:
    """The category of a whole number (the Unicode plural rules)."""
    if lang == "en":
        return "one" if count == 1 else "other"
    # the rules of Russian and Serbian differ only in the name of the rest
    last, tens = count % 10, count % 100
    if last == 1 and tens != 11:
        return "one"
    if 2 <= last <= 4 and not 12 <= tens <= 14:
        return "few"
    return {"ru": "many", "sr": "other"}[lang]


#: One day, two hours, five minutes and 21 seconds before the start.
LEFT_SECONDS = 86400 + 2 * 3600 + 5 * 60 + 21


class ScriptStringsTests(unittest.TestCase):
    def test_the_source_holds_the_english_strings_as_the_build_writes_them(self):
        found = STRINGS_LINE.findall(SCRIPT.read_text(encoding="utf-8"))
        self.assertEqual(found, [_locale.script_json(_locale.pack("en"))])

    def test_the_build_rewrites_the_one_line(self):
        assets = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, assets, True)
        # line breaks of another system, kept as they are
        source ="a();\r\n  var STRINGS = {\"x\":1}; /* @strings */\r\nb();\r\n"
        (assets / build.SCRIPT_FILE).write_bytes(source.encode("utf-8"))
        build.write_script_strings(assets, _locale.site_strings({"lang": "sr", "strings": SERBIAN}))
        written = (assets / build.SCRIPT_FILE).read_bytes().decode("utf-8")
        lines = written.split("\r\n")
        self.assertEqual((lines[0], lines[2], lines[3]), ("a();", "b();", ""))
        self.assertTrue(lines[1].startswith('  var STRINGS = {"countdown":{"days":{"few":"dana",'))
        self.assertTrue(lines[1].endswith("}; /* @strings */"))

    def test_no_line_or_several_is_an_error(self):
        assets = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, assets, True)
        line = "var STRINGS = {}; /* @strings */\n"
        for text, count in (("", 0), ("var STRINGS = {};\n", 0), (line * 2, 2)):
            with self.subTest(count=count, text=text):
                (assets / build.SCRIPT_FILE).write_text(text, encoding="utf-8")
                with self.assertRaises(build.BuildError) as caught:
                    build.write_script_strings(assets, _locale.pack("en"))
                self.assertEqual(
                    str(caught.exception),
                    "assets/app.js: expected exactly one line 'var STRINGS = {…}; "
                    f"/* @strings */', found {count}",
                )
        (assets / build.SCRIPT_FILE).unlink()
        with self.assertRaises(build.BuildError):
            build.write_script_strings(assets, _locale.pack("en"))


class LanguageBuildTests(CliTestCase):
    """`validate` and `build` with the real template and page script."""

    template = REAL_TEMPLATE

    def setUp(self) -> None:
        super().setUp()
        shutil.copyfile(SCRIPT, self.code / "assets" / build.SCRIPT_FILE)

    def write_site(self, **changes) -> None:
        site = support.site_data()
        for key, value in changes.items():
            if value is None:
                site.pop(key, None)
            else:
                site[key] = value
        support.write_data(self.data, site=site)

    def page(self, token: str = support.TOKEN_A) -> str:
        return (self.out / token / "index.html").read_text(encoding="utf-8")

    def test_the_log_names_the_language(self):
        self.write_site(lang=None)
        result = support.run_main(self.code, "validate", "--data", self.data, "--media", self.media)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("validate: language: en (default)\nvalidate: OK - ", result.stdout)
        result = self.build_in_process()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"build: language: en \(default\)\nbuild: OK -> ")
        self.write_site(lang="sr-Latn", strings=SERBIAN)
        result = self.build_in_process()
        self.assertIn("build: language: sr-Latn\n", result.stdout)

    def test_english_pages(self):
        self.write_site(lang=None)
        result = self.build_in_process()
        self.assertEqual(result.returncode, 0, result.stderr)
        page = self.page()
        for text in ('<html lang="en" class="invitation">',
                     f"<title>Invitation · {support.COUPLE_NAMES}</title>",
                     '<meta property="og:locale" content="en_GB">',
                     '<time datetime="2030-06-01T16:00:00+03:00">1 June 2030, 16:00</time>',
                     ">Add to calendar</a>", 'aria-label="Time until the start"',
                     ">days</span>", ">seconds</span>", ">Programme</h4>", ">Directions",
                     'aria-label="Open in maps"', ">Google Maps</a>", ">Yandex Maps</a>",
                     ">Apple Maps</a>", ">this event is over</span>", ">happening now</span>",
                     "Saturday, 1 June 2030, 16:00"):  # fmt: skip
            with self.subTest(text=text):
                self.assertIn(text, page)

    def test_a_language_without_a_pack(self):
        self.write_site(lang="sr-Latn", strings=SERBIAN)
        result = support.run_main(self.code, "validate", "--data", self.data, "--media", self.media)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.build_in_process()
        self.assertEqual(result.returncode, 0, result.stderr)
        page = self.page()
        for text in ('<html lang="sr-Latn" class="invitation">',
                     f"<title>Pozivnica · {support.COUPLE_NAMES}</title>",
                     '<meta property="og:locale" content="sr_RS">', "1. juna 2030. u 16:00",
                     "Subota, 1. juna 2030., 16:00", ">Dodaj u kalendar</a>",
                     'aria-label="Prikaži na mapi"', ">Google mape</a>", ">Raspored</h4>",
                     ">događaj je završen</span>", ">sekundi</span>"):  # fmt: skip
            with self.subTest(text=text):
                self.assertIn(text, page)
        # no label of a pack: neither as text nor as the value of a label (the
        # fixture data is in Russian: a word it has itself may be on the page)
        data = (self.data / "site.json").read_text(encoding="utf-8")
        for name in ("en", "ru"):
            for key, value in _locale.ui_labels(_locale.pack(name)).items():
                if value in data:
                    continue
                with self.subTest(pack=name, key=key):
                    for written in (f">{value}<", f'aria-label="{value}"', f'content="{value} '):
                        self.assertNotIn(written, page)

    def test_missing_keys_stop_the_build(self):
        self.write_site(
            lang="sr-Latn", strings=without(SERBIAN, "mapApple", "months", "lightbox.loading")
        )
        expected = (
            "error: site.json: field 'strings' must give every key for 'sr-Latn', which has no "
            "built-in strings; missing: lightbox.loading, mapApple, months"
        )
        for result in (self.run_validate(), self.run_build()):
            self.assertEqual(result.returncode, 1)
            self.assertEqual(
                [line for line in result.stderr.splitlines() if line.startswith("error:")],
                [expected],
            )
        self.assertFalse(self.out.exists())

    def test_an_english_build_ships_the_script_as_it_is(self):
        self.write_site(lang=None)
        result = self.build_in_process()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.out / "assets" / build.SCRIPT_FILE).read_bytes(), SCRIPT.read_bytes())

    def test_the_script_gets_the_strings_of_the_site(self):
        for changes, expected in (
            ({"lang": "sr-Latn", "strings": SERBIAN}, SERBIAN),
            # a partial override of a pack: merged into the pack
            ({"lang": "en", "strings": {"lightbox": {"close": "Shut"}}},
             _locale.merge(_locale.pack("en"), {"lightbox": {"close": "Shut"}})),
        ):  # fmt: skip
            with self.subTest(lang=changes["lang"]):
                self.write_site(**changes)
                result = self.build_in_process()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(shipped_strings(self.out), _locale.script_strings(expected))
                # one line differs from the source, nothing else
                source = SCRIPT.read_text(encoding="utf-8").splitlines()
                shipped = (self.out / "assets" / build.SCRIPT_FILE).read_text(
                    encoding="utf-8").splitlines()  # fmt: skip
                self.assertEqual(len(shipped), len(source))
                differ = [n for n, (a, b) in enumerate(zip(source, shipped)) if a != b]
                self.assertEqual(len(differ), 1)
                self.assertIn("/* @strings */", source[differ[0]])
                # no attribute, no inline script on the pages: the CSP stays 'self'
                page = self.page()
                self.assertEqual(page.count("<script"), 1)
                self.assertIn('<script src="/assets/app.js" defer></script>', page)
                self.assertNotIn("countdown", page.split("<body>")[0].replace("app.js", ""))

    def test_a_script_without_the_line_of_strings_stops_the_build(self):
        (self.code / "assets" / build.SCRIPT_FILE).write_text("// no strings\n", encoding="utf-8")
        result = self.run_build()
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "error: assets/app.js: expected exactly one line 'var STRINGS = {…}; /* @strings */', "
            "found 0",
            result.stderr,
        )
        self.assertFalse(self.out.exists())


@unittest.skipUnless(CHROME, "Chrome or Chromium is not installed")
class CountdownInBrowserTests(support.TempDirTestCase):
    """The plural forms of the countdown as a real browser shows them."""

    def build(self, site: dict) -> Path:
        code = support.make_code_dir(self.tmp, template=REAL_TEMPLATE)
        shutil.copyfile(SCRIPT, code / "assets" / build.SCRIPT_FILE)
        shutil.copyfile(support.ROOT / "assets" / "app.css", code / "assets" / "app.css")
        data = support.write_data(self.tmp / "data", site=site)
        media = support.write_media(self.tmp / "media")
        out = self.tmp / "dist"
        build.build_site(
            data, media, out, code_dir=code, log=lambda _line: None,
            preview=build.PreviewOptions(enabled=False),
        )  # fmt: skip
        return out

    def countdown(self, site: dict) -> dict:
        start = site["events"][site["mainEvent"]]["start"]
        return support.countdown_in_browser(
            self.build(site), f"{support.TOKEN_A}/", CHROME, start, LEFT_SECONDS
        )

    def assertForms(self, found: dict, lang: str, forms: dict) -> None:
        self.assertTrue(found["shown"])
        self.assertEqual([cell[0] for cell in found["cells"]], list(_locale.COUNTDOWN_UNITS))
        for unit, value, label in found["cells"]:
            with self.subTest(unit=unit, value=value):
                self.assertEqual(label, forms[unit][plural_category(lang, int(value))])

    def test_english(self):
        site = support.site_data()
        self.assertNotIn("lang", site)
        found = self.countdown(site)
        self.assertEqual(found["lang"], "en")
        # 1 day, 2 hours, 5 minutes and about 21 seconds
        self.assertEqual([cell[1] for cell in found["cells"]][:3], ["1", "02", "05"])
        self.assertEqual([cell[2] for cell in found["cells"]][:3], ["day", "hours", "minutes"])
        self.assertForms(found, "en", _locale.pack("en")["countdown"])

    def test_a_language_without_a_pack(self):
        site = support.site_data(lang="sr-Latn", strings=SERBIAN)
        found = self.countdown(site)
        self.assertEqual(found["lang"], "sr-Latn")
        self.assertEqual([cell[2] for cell in found["cells"]][:3], ["dan", "sata", "minuta"])
        self.assertForms(found, "sr", SERBIAN["countdown"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
