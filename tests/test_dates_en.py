"""The dates in English, through the built-in `en` pack (`tools/_dates.py`):
the international format by default, the US one as an override."""

from __future__ import annotations

import unittest
from datetime import datetime

from tools import _dates as dates
from tools import _locale
from tools._dates import parse_date_iso as at

#: A site without `lang`: English, the default.
EN = _locale.site_strings({})
#: The US format: a documented `strings` override of the `en` pack.
US_FORMAT = {
    "date": "{month} {d}, {yyyy}",
    "dayMonth": "{month} {d}",
    "time": "{h}:{mm} {ampm}",
    "ampm": ["AM", "PM"],
}
US = _locale.site_strings({"lang": "en-US", "strings": US_FORMAT})


class InternationalFormatTests(unittest.TestCase):
    start = at("2030-06-15T16:00+03:00")

    def test_the_default_language_is_english(self):
        self.assertEqual(_locale.DEFAULT_LANG, "en")
        self.assertEqual(EN, _locale.pack("en"))

    def test_the_card_of_an_event(self):
        self.assertEqual(dates.format_when(EN, self.start), "Saturday, 15 June 2030, 16:00")

    def test_an_end_on_the_same_day(self):
        self.assertEqual(
            dates.format_when(EN, self.start, at("2030-06-15T23:30+03:00")),
            "Saturday, 15 June 2030, 16:00–23:30",
        )

    def test_an_end_on_the_next_day(self):
        self.assertEqual(
            dates.format_when(EN, at("2030-06-15T22:00+03:00"), at("2030-06-16T02:00+03:00")),
            "Saturday, 15 June 2030, 22:00 – 16 June, 02:00",
        )

    def test_an_end_in_the_next_year(self):
        self.assertEqual(
            dates.format_when(EN, at("2030-12-31T22:00+03:00"), at("2031-01-01T02:00+03:00")),
            "Tuesday, 31 December 2030, 22:00 – 1 January 2031, 02:00",
        )

    def test_the_date_widget(self):
        self.assertEqual(dates.format_date_time(EN, self.start), "15 June 2030, 16:00")

    def test_the_tabs(self):
        morning = at("2030-06-15T11:00+03:00")
        self.assertEqual(dates.format_tab(EN, morning, False), "15 June, 11:00")
        # every event on one day: the time alone
        self.assertEqual(dates.format_tab(EN, morning, True), "11:00")

    def test_a_morning_time_has_two_digits(self):
        for text, expected in (
            ("2030-06-15T09:30+03:00", "09:30"),
            ("2030-06-15T00:05+03:00", "00:05"),
            ("2030-06-15T12:00+03:00", "12:00"),
            ("2030-06-15T23:59+03:00", "23:59"),
        ):
            with self.subTest(text=text):
                self.assertEqual(dates.format_time(EN, at(text)), expected)

    def test_every_month_and_weekday(self):
        months = ("January", "February", "March", "April", "May", "June", "July", "August",
                  "September", "October", "November", "December")  # fmt: skip
        for number, name in enumerate(months, start=1):
            with self.subTest(month=name):
                moment = at(f"2030-{number:02d}-05T12:00+03:00")
                self.assertEqual(dates.format_date(EN, moment), f"5 {name} 2030")
                self.assertEqual(dates.format_day_month(EN, moment), f"5 {name}")
        weekdays = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
        # 10 June 2030 is a Monday
        for offset, name in enumerate(weekdays):
            with self.subTest(weekday=name):
                moment = at(f"2030-06-{10 + offset:02d}T16:00+03:00")
                self.assertEqual(
                    dates.format_when(EN, moment), f"{name}, {10 + offset} June 2030, 16:00"
                )

    def test_the_placeholders_of_a_text(self):
        from tools import _page

        site = {
            "coupleNames": "Ann and Ben",
            "mainEvent": "dinner",
            "events": {"dinner": {"title": "Dinner", "location": "hall",
                                  "start": "2030-06-15T16:00:00+03:00"}},
            "locations": {"hall": {"name": "Example Hall"}},
        }  # fmt: skip
        values = _page.text_values(site, "dinner")
        self.assertEqual((values["eventDate"], values["eventTime"]), ("15 June 2030", "16:00"))


class UsFormatTests(unittest.TestCase):
    """`{month} {d}, {yyyy}` and a 12-hour clock."""

    def test_the_card_with_an_end(self):
        self.assertEqual(
            dates.format_when(US, at("2030-06-15T16:00+03:00"), at("2030-06-15T23:30+03:00")),
            "Saturday, June 15, 2030, 4:00 PM–11:30 PM",
        )

    def test_the_tabs_and_the_date_widget(self):
        morning = at("2030-06-15T11:00+03:00")
        self.assertEqual(dates.format_tab(US, morning, False), "June 15, 11:00 AM")
        self.assertEqual(dates.format_date_time(US, morning), "June 15, 2030, 11:00 AM")

    def test_noon_and_midnight(self):
        for text, expected in (
            ("2030-06-15T00:00+03:00", "12:00 AM"),
            ("2030-06-15T00:30+03:00", "12:30 AM"),
            ("2030-06-15T11:59+03:00", "11:59 AM"),
            ("2030-06-15T12:00+03:00", "12:00 PM"),
            ("2030-06-15T13:05+03:00", "1:05 PM"),
        ):
            with self.subTest(text=text):
                self.assertEqual(dates.format_time(US, at(text)), expected)

    def test_the_rest_of_the_pack_stays(self):
        self.assertEqual(US["weekdays"], EN["weekdays"])
        self.assertEqual(US["when"], EN["when"])


class TokenTests(unittest.TestCase):
    """Every placeholder of the date and time patterns."""

    def strings(self, **patterns):
        return _locale.merge(EN, patterns)

    def test_the_date_tokens(self):
        strings = self.strings(date="{dd}.{MM}.{yyyy} ({weekday}, {Weekday}; {d}/{M}, {month})")
        self.assertEqual(
            dates.format_date(strings, at("2030-06-05T09:00+03:00")),
            "05.06.2030 (Wednesday, Wednesday; 5/6, June)",
        )

    def test_the_time_tokens(self):
        strings = self.strings(time="{H}|{HH}|{h}|{hh}|{mm}|{ampm}")
        self.assertEqual(dates.format_time(strings, at("2030-06-05T09:07+03:00")), "9|09|9|09|07|am")
        self.assertEqual(
            dates.format_time(strings, at("2030-06-05T21:07+03:00")), "21|21|9|09|07|pm"
        )

    def test_a_weekday_in_lower_case_is_capitalised_by_weekday(self):
        strings = self.strings(weekdays=["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
        self.assertEqual(
            dates.format_when(strings, at("2030-06-15T16:00+03:00")), "Sat, 15 June 2030, 16:00"
        )

    def test_the_when_and_tab_tokens(self):
        strings = self.strings(
            when="{weekday} {dayMonth} at {time} ({date})", tab="{Weekday} {date} {time}"
        )
        moment = at("2030-06-15T16:00+03:00")
        self.assertEqual(
            dates.format_when(strings, moment), "Saturday 15 June at 16:00 (15 June 2030)"
        )
        self.assertEqual(dates.format_tab(strings, moment, False), "Saturday 15 June 2030 16:00")

    def test_a_moment_without_an_offset_is_rejected(self):
        naive = datetime(2030, 6, 15, 16, 0)
        for function in (dates.format_time, dates.format_date, dates.format_date_time):
            with self.subTest(function=function.__name__):
                with self.assertRaises(ValueError):
                    function(EN, naive)
        with self.assertRaises(ValueError):
            dates.format_tab(EN, naive, False)

    def test_a_placeholder_without_a_value(self):
        with self.assertRaises(ValueError):
            dates.format_date(self.strings(date="{d} {time}"), at("2030-06-15T16:00+03:00"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
