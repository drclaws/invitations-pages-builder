"""The language of the pages: the built-in strings and those of the site.

`site.json` `"lang"` is a language tag (BCP 47: `en`, `ru`, `sr-Latn`), used
as written for `<html lang>`; without it the pages are in `DEFAULT_LANG`.
Its primary subtag, lower-cased, picks a built-in pack of strings,
`locales/<subtag>.json` next to this module (`ru-RU` -> `ru`, `en-US` ->
`en`); any other language has no pack.  `site.json` `"strings"` overrides
any key of the pack, or gives every key for a language without one.  The
groups `countdown` and `lightbox` merge key by key; a list (`months`,
`weekdays`, `ampm`) and the plural forms of one countdown unit replace the
value of the pack as a whole.

The keys (`KEY_PATHS`), by kind:

- `ogLocale`, the locale of the link preview tags (`en_GB`);
- labels (`LABELS`): the words of the pages, one line each;
- `months` (12 names, in the form a date uses), `weekdays` (7, Monday
  first), `ampm` (2: before and after noon);
- date and time patterns (`PATTERNS`): text with placeholders in braces,
  filled in by `tools._dates`;
- `countdown.<unit>`: the plural forms of a unit of the countdown timer,
  by the categories of the Unicode plural rules (`PLURAL_CATEGORIES`); the
  page script picks one with the rules of the browser;
- `lightbox.<key>`: the texts of the photo and video viewer
  (`LIGHTBOX_LABELS`) and the pattern of its position (`LIGHTBOX_PATTERNS`).

`check_site` lists the problems of `lang` and `strings` for the checks of
`site.json`; `site_strings` resolves the strings of valid data, `ui_labels`
and `script_strings` give the parts the page tree and the page script read.
Strings are site-level data, never guest data: they may go into the files
every page shares.  Standard library only; each pack is read once.
"""

from __future__ import annotations

import copy
import functools
import json
import re
from pathlib import Path
from typing import Any, Mapping, NamedTuple

from tools._data import PathPart, json_type

#: The language of a site without `lang`.
DEFAULT_LANG = "en"
#: The built-in packs: `<primary subtag>.json`.
LOCALES_DIR = Path(__file__).resolve().parent / "locales"
#: The subset of BCP 47 a tag must follow: language, script, region and
#: variants.
LANG_RE = re.compile(
    r"[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?"
    r"(-([A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*"
)
LANG_PROBLEM = "must be a language tag such as 'en', 'ru' or 'sr-Latn'"

#: The labels of the pages (the `ui` object of the page tree).
LABELS = (
    "invitationTitle",
    "addToCalendar",
    "programme",
    "directions",
    "placePending",
    "openOnMap",
    "mapGoogle",
    "mapYandex",
    "mapApple",
    "past",
    "eventPast",
    "now",
    "countdownLabel",
    "countdownDays",
    "countdownHours",
    "countdownMinutes",
    "countdownSeconds",
    "photo",
    "video",
)
#: Plain texts that are not labels of the pages.
TEXTS = ("ogLocale",)
#: Lists: key -> (length, the problem of a list of another shape).
LISTS = {
    "months": (12, "must be a list of 12 strings"),
    "weekdays": (7, "must be a list of 7 strings, Monday first"),
    "ampm": (2, "must be a list of 2 strings"),
}

_DAY = ("d", "dd")
_MONTH = ("M", "MM", "month")
_HOUR = ("H", "HH", "h", "hh")
_DATE = (*_DAY, *_MONTH, "yyyy", "weekday", "Weekday")
#: Patterns: key -> (the placeholders it may use, the groups it must use one
#: placeholder of each).
PATTERNS = {
    "date": (_DATE, (("yyyy",), _DAY, _MONTH)),
    "dayMonth": (_DATE, (_DAY, _MONTH)),
    "time": ((*_HOUR, "mm", "ampm"), (_HOUR, ("mm",))),
    "dateTime": (("date", "time"), (("date",), ("time",))),
    "when": (("date", "time", "weekday", "Weekday", "dayMonth"), (("date",), ("time",))),
    "rangeSameDay": (("when", "endTime"), (("when",), ("endTime",))),
    "rangeOtherDay": (("when", "endDay", "endTime"), (("when",), ("endDay",), ("endTime",))),
    "tab": (("time", "dayMonth", "date", "weekday", "Weekday"), (("time",),)),
}

#: The units of the countdown timer.
COUNTDOWN_UNITS = ("days", "hours", "minutes", "seconds")
#: The categories of the Unicode plural rules (what `Intl.PluralRules`
#: returns); every unit has at least `other`.
PLURAL_CATEGORIES = ("zero", "one", "two", "few", "many", "other")
PLURAL_PROBLEM = (
    f"must be an object of plural forms ({', '.join(PLURAL_CATEGORIES)}) with at least 'other'"
)
#: The texts of the photo and video viewer: names of the dialog, button
#: labels, the names of an item, notes.
LIGHTBOX_LABELS = (
    "photos",
    "mixed",
    "image",
    "video",
    "close",
    "prev",
    "next",
    "prevItem",
    "nextItem",
    "itemImage",
    "itemVideo",
    "loading",
    "error",
    "videoError",
)
#: The live region of the viewer: `{item} {n} of {total}`.
LIGHTBOX_PATTERNS = {"position": (("item", "n", "total"), (("n",), ("total",)))}
#: The groups that merge key by key, and their keys.
GROUPS = {
    "countdown": COUNTDOWN_UNITS,
    "lightbox": (*LIGHTBOX_LABELS, *LIGHTBOX_PATTERNS),
}
#: The keys of `strings` (and of a pack), in the order of the packs.
TOP_KEYS = (*TEXTS, *LABELS, *LISTS, *PATTERNS, *GROUPS)
#: Every key, dotted for the keys of the groups (`countdown.days`).
KEY_PATHS = tuple(
    item
    for key in TOP_KEYS
    for item in ([f"{key}.{name}" for name in GROUPS[key]] if key in GROUPS else [key])
)
#: The parts of the strings the page script reads (`script_strings`).
SCRIPT_GROUPS = ("countdown", "lightbox")

#: A placeholder of a pattern: a name in braces.
PLACEHOLDER_RE = re.compile(r"\{([A-Za-z][A-Za-z0-9]*)\}")


class Problem(NamedTuple):
    """A problem of `lang` or `strings`.

    `text` follows `field '<path>'`; for an unknown field (`unknown`) the
    message is the unknown-field one of the checks, with a hint among
    `known`.
    """

    path: tuple[PathPart, ...]
    text: str = ""
    unknown: bool = False
    known: tuple[str, ...] = ()


# --------------------------------------------------------------------------
# The packs and the strings of a site
# --------------------------------------------------------------------------


def is_lang(value: Any) -> bool:
    """True for a language tag of the accepted subset."""
    return isinstance(value, str) and LANG_RE.fullmatch(value) is not None


@functools.lru_cache(maxsize=None)
def packs() -> frozenset[str]:
    """The names of the built-in packs."""
    if not LOCALES_DIR.is_dir():
        return frozenset()
    return frozenset(
        path.stem for path in LOCALES_DIR.glob("*.json") if re.fullmatch(r"[a-z]{2,3}", path.stem)
    )


def pack_name(lang: str) -> str | None:
    """The built-in pack of a language tag (its primary subtag), or None."""
    primary = lang.split("-", 1)[0].lower()
    return primary if primary in packs() else None


@functools.lru_cache(maxsize=None)
def _read_pack(name: str) -> dict:
    return json.loads((LOCALES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def pack(name: str) -> dict:
    """The strings of a built-in pack (a copy)."""
    return copy.deepcopy(_read_pack(name))


def site_lang(site: Mapping[str, Any]) -> str:
    """The language tag of the pages, as written (`DEFAULT_LANG` without one)."""
    return site.get("lang", DEFAULT_LANG)


def describe_lang(site: Mapping[str, Any]) -> str:
    """`ru`, or `en (default)` when `site.json` has no `lang`: for the log."""
    return site["lang"] if "lang" in site else f"{DEFAULT_LANG} (default)"


def merge(base: Mapping[str, Any], strings: Mapping[str, Any]) -> dict:
    """`strings` over `base`: the groups key by key, everything else (a
    list, the plural forms of a unit) as a whole."""
    merged = copy.deepcopy(dict(base))
    for key, value in strings.items():
        if key in GROUPS and isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = {**merged[key], **copy.deepcopy(value)}
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def site_strings(site: Mapping[str, Any]) -> dict:
    """The resolved strings of a site whose data is valid: its pack (none
    for a language without one) with `strings` over it."""
    name = pack_name(site_lang(site))
    return merge(pack(name) if name else {}, site.get("strings", {}))


def ui_labels(strings: Mapping[str, Any]) -> dict[str, str]:
    """The labels of the pages (`ui` of the page tree)."""
    return {key: strings[key] for key in LABELS}


def script_strings(strings: Mapping[str, Any]) -> dict:
    """What the page script reads: `{"countdown": …, "lightbox": …}`."""
    return {key: strings[key] for key in SCRIPT_GROUPS}


def script_json(strings: Mapping[str, Any]) -> str:
    """The script strings as one line of JSON, the way the build writes
    them into the page script: keys sorted, no spaces, letters as they are;
    U+2028 and U+2029 escaped (older engines end a line of code at them)."""
    text = json.dumps(
        script_strings(strings), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return text.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def fill(pattern: str, values: Mapping[str, str]) -> str:
    """A pattern with its placeholders replaced by `values`; a placeholder
    without a value raises `ValueError` (the checks prevent it)."""

    def replace(match: re.Match) -> str:
        name = match.group(1)
        if name not in values:
            raise ValueError(f"the pattern has no value for the placeholder {{{name}}}")
        return values[name]

    return PLACEHOLDER_RE.sub(replace, pattern)


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------


def check_site(site: Mapping[str, Any]) -> list[Problem]:
    """The problems of `lang` and `strings` of `site.json`, in order.

    For a language without a pack every key is required: one problem lists
    the missing ones (sorted, dotted).  A key that is given but broken is
    reported on its own and not counted as missing.
    """
    problems: list[Problem] = []
    lang: str | None = DEFAULT_LANG
    if "lang" in site:
        lang = site["lang"] if is_lang(site["lang"]) else None
        if lang is None:
            problems.append(Problem(("lang",), LANG_PROBLEM))
    given: set[str] = set()
    if "strings" in site:
        strings = site["strings"]
        if isinstance(strings, dict):
            problems.extend(_check_strings(strings, given))
        else:
            problems.append(Problem(("strings",), f"must be an object, got {json_type(strings)}"))
            given.update(KEY_PATHS)  # reported: nothing is counted as missing
    if lang is not None and pack_name(lang) is None:
        missing = sorted(set(KEY_PATHS) - given)
        if missing:
            problems.append(
                Problem(
                    ("strings",),
                    f"must give every key for '{lang}', which has no built-in strings; "
                    f"missing: {', '.join(missing)}",
                )
            )
    return problems


def check_pack(strings: Mapping[str, Any]) -> list[Problem]:
    """The problems of a complete set of strings (a pack): every key, each
    of its kind."""
    given: set[str] = set()
    problems = _check_strings(strings, given)
    missing = sorted(set(KEY_PATHS) - given)
    if missing:
        problems.append(Problem((), f"misses the keys {', '.join(missing)}"))
    return problems


def _check_strings(strings: Mapping[str, Any], given: set[str]) -> list[Problem]:
    """The problems of the keys of `strings`; `given` collects the dotted
    keys that are present."""
    problems: list[Problem] = []
    for key, value in strings.items():
        path = ("strings", key)
        if key not in TOP_KEYS:
            problems.append(Problem(path, unknown=True, known=TOP_KEYS))
        elif key in GROUPS:
            problems.extend(_check_group(key, value, given))
        else:
            given.add(key)
            problems.extend(_check_value(key, value, path))
    return problems


def _check_group(group: str, value: Any, given: set[str]) -> list[Problem]:
    path = ("strings", group)
    keys = GROUPS[group]
    if not isinstance(value, dict):
        given.update(f"{group}.{key}" for key in keys)  # reported: not missing
        return [Problem(path, f"must be an object, got {json_type(value)}")]
    problems: list[Problem] = []
    for key, item in value.items():
        if key not in keys:
            problems.append(Problem((*path, key), unknown=True, known=keys))
            continue
        given.add(f"{group}.{key}")
        if group == "countdown":
            problems.extend(_check_plural(item, (*path, key)))
        elif key in LIGHTBOX_PATTERNS:
            problems.extend(_check_pattern(item, (*path, key), *LIGHTBOX_PATTERNS[key]))
        else:
            problems.extend(_check_line(item, (*path, key)))
    return problems


def _check_value(key: str, value: Any, path: tuple[PathPart, ...]) -> list[Problem]:
    if key in LISTS:
        return _check_list(value, path, *LISTS[key])
    if key in PATTERNS:
        return _check_pattern(value, path, *PATTERNS[key])
    return _check_line(value, path)


def _check_line(value: Any, path: tuple[PathPart, ...]) -> list[Problem]:
    """A non-empty single-line string."""
    if not isinstance(value, str):
        return [Problem(path, f"must be a string, got {json_type(value)}")]
    if not value.strip():
        return [Problem(path, "must not be empty")]
    if "\n" in value or "\r" in value:
        return [Problem(path, "must be a single line (no line breaks)")]
    return []


def _check_list(value: Any, path: tuple[PathPart, ...], length: int, problem: str) -> list[Problem]:
    if not (
        isinstance(value, list)
        and len(value) == length
        and all(isinstance(item, str) for item in value)
    ):
        return [Problem(path, problem)]
    return [
        found for index, item in enumerate(value) for found in _check_line(item, (*path, index))
    ]


def _check_plural(value: Any, path: tuple[PathPart, ...]) -> list[Problem]:
    if not isinstance(value, dict):
        return [Problem(path, PLURAL_PROBLEM)]
    problems: list[Problem] = []
    for category, form in value.items():
        if category not in PLURAL_CATEGORIES:
            problems.append(Problem((*path, category), unknown=True, known=PLURAL_CATEGORIES))
        else:
            problems.extend(_check_line(form, (*path, category)))
    if "other" not in value:
        problems.append(Problem(path, PLURAL_PROBLEM))
    return problems


def _listed(names: tuple[str, ...]) -> str:
    shown = [f"{{{name}}}" for name in names]
    return shown[0] if len(shown) == 1 else f"{', '.join(shown[:-1])} or {shown[-1]}"


def _check_pattern(
    value: Any,
    path: tuple[PathPart, ...],
    known: tuple[str, ...],
    required: tuple[tuple[str, ...], ...],
) -> list[Problem]:
    """A pattern: a non-empty line whose braces are all placeholders of
    `known`, with one placeholder of each group of `required`."""
    problems = _check_line(value, path)
    if problems:
        return problems
    rest = PLACEHOLDER_RE.sub("", value)
    if "{" in rest or "}" in rest:
        return [Problem(path, "has a brace that is not part of a placeholder")]
    names = PLACEHOLDER_RE.findall(value)
    listed = ", ".join(f"{{{name}}}" for name in known)
    for name in dict.fromkeys(names):
        if name not in known:
            shown = f" {{{name}}}" if len(name) <= 32 else ""
            problems.append(
                Problem(path, f"has an unknown placeholder{shown}; known: {listed}")
            )
    for group in required:
        if not any(name in names for name in group):
            problems.append(Problem(path, f"must contain the placeholder {_listed(group)}"))
    return problems
