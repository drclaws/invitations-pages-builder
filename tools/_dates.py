"""Dates in the language of the site, and event end times.

Everything is written in the event's own UTC offset, that is in the local
time of the place: never in UTC and never in the time zone of the machine
that runs the build.  The names of the months and weekdays and the patterns
of dates and times come from the resolved strings of the site
(`tools._locale.site_strings`), never from the operating system's locale.

The formatting functions take those strings first, then `datetime` values
with a UTC offset (as `parse_date_iso` reads them from the data); a value
without an offset raises `ValueError`.  Pure functions, no input/output.
Standard library only.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping, NamedTuple

from tools._locale import fill

#: The resolved strings of a site (`tools._locale.site_strings`).
Strings = Mapping[str, Any]

_DATE_ISO_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}(?::\d{2}(?:\.\d{3}|\.\d{6})?)?)"
    r"(Z|z|[+-]\d{2}:\d{2})?\Z"
)


def parse_date_iso(value: str) -> datetime:
    """Parse a date and time from the data; a UTC offset is required.

    Accepts a strict subset of ISO 8601 so that the result does not depend on
    the Python version (3.10's `fromisoformat` is stricter than 3.11's), and
    normalises the `Z` suffix, which `fromisoformat` rejects before 3.11.
    """
    match = _DATE_ISO_RE.match(value) if isinstance(value, str) else None
    if not match:
        raise ValueError(
            "must be an ISO 8601 date and time with a UTC offset, "
            "e.g. 2030-01-02T18:30:00+03:00"
        )
    if not match.group(3):
        raise ValueError(
            "has no UTC offset; append the offset, e.g. +03:00 (or Z for UTC)"
        )
    offset = match.group(3)
    text = f"{match.group(1)}T{match.group(2)}" + (
        "+00:00" if offset in ("Z", "z") else offset
    )
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError("is not a valid date and time") from None
    if parsed.utcoffset() is None:  # pragma: no cover - guarded by the regex
        raise ValueError("has no UTC offset")
    return parsed


def _require_offset(moment: datetime) -> datetime:
    if not isinstance(moment, datetime) or moment.utcoffset() is None:
        raise ValueError("expected a date and time with a UTC offset")
    return moment


def _in_offset_of(moment: datetime, reference: datetime) -> datetime:
    """The same moment on the clock of `reference` (its UTC offset)."""
    return moment.astimezone(timezone(reference.utcoffset()))


def _weekdays(strings: Strings, moment: datetime) -> dict[str, str]:
    """`{weekday}` and `{Weekday}`: the name, and the name with its first
    letter upper-cased."""
    weekday = strings["weekdays"][moment.weekday()]
    return {"weekday": weekday, "Weekday": weekday[:1].upper() + weekday[1:]}


def _date_values(strings: Strings, moment: datetime) -> dict[str, str]:
    """The placeholders of the `date` and `dayMonth` patterns."""
    _require_offset(moment)
    return {
        "d": str(moment.day),
        "dd": f"{moment.day:02d}",
        "M": str(moment.month),
        "MM": f"{moment.month:02d}",
        "month": strings["months"][moment.month - 1],
        "yyyy": f"{moment.year:04d}",
        **_weekdays(strings, moment),
    }


def format_time(strings: Strings, moment: datetime) -> str:
    """The `time` pattern: `{H}`/`{HH}` the hour of 24 (without and with a
    leading zero), `{h}`/`{hh}` the hour of 12, `{mm}` the minutes, `{ampm}`
    the half of the day."""
    _require_offset(moment)
    hour = moment.hour
    twelve = hour % 12 or 12
    return fill(
        strings["time"],
        {
            "H": str(hour),
            "HH": f"{hour:02d}",
            "h": str(twelve),
            "hh": f"{twelve:02d}",
            "mm": f"{moment.minute:02d}",
            "ampm": strings["ampm"][1 if hour >= 12 else 0],
        },
    )


def format_day_month(strings: Strings, moment: datetime) -> str:
    """The `dayMonth` pattern: a date without the year (`15 June`)."""
    return fill(strings["dayMonth"], _date_values(strings, moment))


def format_date(strings: Strings, moment: datetime) -> str:
    """The `date` pattern: `{d}`/`{dd}` the day, `{M}`/`{MM}` the number of
    the month, `{month}` its name, `{yyyy}` the year, `{weekday}` and
    `{Weekday}` the day of the week (`15 June 2030`)."""
    return fill(strings["date"], _date_values(strings, moment))


def format_date_time(strings: Strings, moment: datetime) -> str:
    """The `dateTime` pattern of the date widget: `{date}` and `{time}`."""
    return fill(
        strings["dateTime"],
        {"date": format_date(strings, moment), "time": format_time(strings, moment)},
    )


def format_when(strings: Strings, start: datetime, end: datetime | None = None) -> str:
    """The time of an event for its card.

    The `when` pattern (`{date}`, `{time}`, `{dayMonth}`, `{weekday}`,
    `{Weekday}`): `Saturday, 15 June 2030, 16:00`.  With an end on the same
    local day the `rangeSameDay` pattern (`{when}` and `{endTime}`:
    `…, 16:00–23:30`); with an end on another day `rangeOtherDay` (`{when}`,
    `{endDay}`, `{endTime}`: `…, 22:00 – 16 June, 02:00`), where `{endDay}`
    is the `dayMonth` of the end, or its `date` when the year changes too.
    The end is shown on the start's clock.
    """
    _require_offset(start)
    text = fill(
        strings["when"],
        {
            "date": format_date(strings, start),
            "time": format_time(strings, start),
            "dayMonth": format_day_month(strings, start),
            **_weekdays(strings, start),
        },
    )
    if end is None:
        return text
    _require_offset(end)
    if end <= start:
        raise ValueError("the end must be later than the start")
    end = _in_offset_of(end, start)
    end_time = format_time(strings, end)
    if end.date() == start.date():
        return fill(strings["rangeSameDay"], {"when": text, "endTime": end_time})
    day = format_day_month(strings, end) if end.year == start.year else format_date(strings, end)
    return fill(strings["rangeOtherDay"], {"when": text, "endDay": day, "endTime": end_time})


def same_local_day(moments: Iterable[datetime]) -> bool:
    """True when all the moments fall on one day, each on its own clock."""
    return len({_require_offset(moment).date() for moment in moments}) <= 1


def format_tab(strings: Strings, start: datetime, same_day: bool) -> str:
    """An event tab label: the time alone when every event of the set falls
    on one day (see `same_local_day`), otherwise the `tab` pattern (`{time}`,
    `{dayMonth}`, `{date}`, `{weekday}`, `{Weekday}`: `15 June, 11:00`)."""
    time = format_time(strings, start)
    if same_day:
        return time
    return fill(
        strings["tab"],
        {
            "time": time,
            "dayMonth": format_day_month(strings, start),
            "date": format_date(strings, start),
            **_weekdays(strings, start),
        },
    )


#: How long an event without an end lasts.
DEFAULT_EVENT_DURATION = timedelta(hours=6)


class TimelineEntry(NamedTuple):
    """An event of `event_timeline` with the end it effectively has."""

    id: str
    start: datetime
    #: The given end, or the start plus the default duration.
    end: datetime
    #: True when the end was given.
    explicit: bool


def event_timeline(
    events: Iterable[tuple[str, datetime, datetime | None]],
    default_duration: timedelta = DEFAULT_EVENT_DURATION,
) -> list[TimelineEntry]:
    """Events `(id, start, end or None)` in order, each with an end.

    The order is by start, then by id.  An event without an end lasts
    `default_duration`; that end is given on its start's clock.  An event's
    end never depends on the other events: it is the same for everybody who
    sees the event (and in its calendar file).

    An end that is not later than its start raises `ValueError`.
    """
    if default_duration <= timedelta(0):
        raise ValueError("the default duration must be positive")
    ordered: list[tuple[datetime, str, datetime | None]] = []
    for event_id, start, end in events:
        _require_offset(start)
        if end is not None:
            _require_offset(end)
            if end <= start:
                raise ValueError("the end of an event must be later than its start")
        ordered.append((start, event_id, end))
    ordered.sort(key=lambda item: (item[0], item[1]))
    timeline: list[TimelineEntry] = []
    for start, event_id, end in ordered:
        if end is not None:
            timeline.append(TimelineEntry(event_id, start, end, True))
            continue
        # added in UTC: the duration is real time whatever the start's clock
        effective = _in_offset_of(start.astimezone(timezone.utc) + default_duration, start)
        timeline.append(TimelineEntry(event_id, start, effective, False))
    return timeline
