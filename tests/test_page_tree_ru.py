"""The page tree of the Russian example set (`tests/fixtures_ru.py`): the
forms of address, the Russian dates and the labels of the `ru` pack."""

from __future__ import annotations

import copy
import unittest
from datetime import timedelta

from tests import fixtures_ru as R
from tests import fixtures_v2 as F
from tests import support
from tests import test_page_tree as T
from tools import _page, _schema
from tools._media import MediaInfo

section, widgets, events_widget, walk_events = T.section, T.widgets, T.events_widget, T.walk_events
dinner_card, photos_pending = T.dinner_card, T.photos_pending


def build(mutate=None, site=None, invitations=None, **settings):
    """The trees of the Russian set (or of the given data)."""
    site = R.ru_site() if site is None else site
    invitations = R.ru_invitations() if invitations is None else invitations
    return T.build(mutate, site=site, invitations=invitations, **settings)


#: A text in place of the link `photos`, in both forms (fictional).
PENDING = {
    "ty": "Фотографии появятся здесь позже — мы тебе напишем",
    "vy": "Фотографии появятся здесь позже — мы вам напишем",
}


class RootTests(unittest.TestCase):
    def test_root_values(self):
        page = build()[0]
        # the canonical name of the form, whatever name the data gives
        self.assertEqual(R.RU_INVITATIONS[0]["form"], "ty")
        self.assertEqual(
            (page["form"], page["informal"], page["formal"]), ("informal", True, False)
        )
        other = build()[4]
        self.assertEqual(R.RU_INVITATIONS[4]["form"], "vy")
        self.assertEqual(
            (other["form"], other["informal"], other["formal"]), ("formal", False, True)
        )
        self.assertEqual(page["coupleNames"], "Алиса и Боб")
        self.assertEqual(page["rsvpDeadline"], "1 мая 2030")
        self.assertEqual((page["lang"], page["ogLocale"]), ("ru", "ru_RU"))


class TextTests(unittest.TestCase):
    def test_forms_of_address(self):
        pages = build()
        self.assertIn("с тобой", section(pages[0], "invite")["widgets"][-1]["text"])
        self.assertIn("с вами", section(pages[4], "invite")["widgets"][-1]["text"])

    def test_texts_use_the_primary_event(self):
        pages = build()
        self.assertEqual(section(pages[2], "invite")["widgets"][-1]["text"].splitlines()[0], "Ждём тебя 15 июня 2030 в 11:00.")
        self.assertEqual(section(pages[0], "invite")["widgets"][-1]["text"].splitlines()[0], "Ждём тебя 15 июня 2030 в 16:00.")

    def test_widgets_switched_on_in_the_form_of_the_guest(self):
        pages = build()
        self.assertIn("со спутником", section(pages[0], "invite")["widgets"][1]["text"])
        self.assertIn("Пожалуйста, сообщи нам", section(pages[0], "invite")["widgets"][1]["text"])
        self.assertIn("Для вас забронирован номер", section(pages[5], "travel")["widgets"][2]["text"])

    def test_placeholders_of_the_site(self):
        page = build()[0]
        rsvp = section(page, "rsvp")["widgets"]
        self.assertIn("до 1 мая 2030", rsvp[0]["text"])
        self.assertEqual(rsvp[1]["text"], "Алиса и Боб")
        self.assertEqual(section(build()[4], "invite")["title"], "Дорогие Пегги и Виктор!")


class LinkTests(unittest.TestCase):
    PHOTOS = {"id": "photos", "text": "Фотографии с ужина", "pending": ""}

    def test_a_hidden_link_leaves_its_text_in_the_form_of_the_guest(self):
        pages = build(photos_pending(PENDING))
        # in the invitation's form of address: #1, #3 and #4 use "ty", the rest "vy"
        for number in (0, 2, 3, 4, 5, 6):
            invitation = R.RU_INVITATIONS[number]
            with self.subTest(invitation=number + 1):
                expected = {"id": "photos", "href": "", "text": "", "pending": PENDING[invitation["form"]]}
                self.assertEqual(dinner_card(pages[number])["links"], [expected])
                self.assertNotIn(invitation["token"], repr(pages[number]))
                # the same node of the event everywhere in the tree
                for event in walk_events(pages[number]):
                    if event["id"] == "dinner":
                        self.assertEqual(event["links"], [expected])
        self.assertEqual(
            [dinner_card(pages[number])["links"][0]["pending"] for number in (0, 4)],
            [PENDING["ty"], PENDING["vy"]],
        )
        # shown: the button, and no text in its place
        for number in (1, 7):
            token = R.RU_INVITATIONS[number]["token"]
            with self.subTest(invitation=number + 1):
                self.assertEqual(
                    dinner_card(pages[number])["links"], [{**self.PHOTOS, "href": f"/photos/{token}/"}]
                )
                self.assertNotIn("Фотографии появятся", repr(pages[number]))

    def test_the_switch_of_the_guest_swaps_the_text_and_the_button(self):
        def change(site, invitations):
            photos_pending(PENDING)(site, invitations)
            invitations[0]["events"]["dinner"] = {"links": {"photos": {"visible": True}}}
            invitations[1]["events"]["dinner"]["links"]["photos"]["visible"] = False

        pages = build(change)
        token = R.RU_INVITATIONS[0]["token"]
        self.assertEqual(dinner_card(pages[0])["links"], [{**self.PHOTOS, "href": f"/photos/{token}/"}])
        # the second guest is addressed informally
        self.assertEqual(
            dinner_card(pages[1])["links"],
            [{"id": "photos", "href": "", "text": "", "pending": PENDING["ty"]}],
        )

    def test_named_texts_and_placeholders_in_the_text(self):
        pages = build(photos_pending("{text:announce} Фотографии — {eventTitle}, {greeting} {{скоро}}"))
        for number, title in ((0, "Праздничный ужин"), (2, "Регистрация")):
            invitation = R.RU_INVITATIONS[number]
            with self.subTest(invitation=number + 1):
                self.assertEqual(
                    dinner_card(pages[number])["links"][0]["pending"],
                    f"Мы, Алиса и Боб, женимся! Фотографии — {title}, {invitation['greeting']} {{скоро}}",
                )


def without_forms(value):
    """The data with every text of forms replaced by its formal variant."""
    if isinstance(value, dict):
        if value and set(value) <= {"ty", "vy", "informal", "formal", "all"}:
            return value.get("vy", value.get("formal"))
        return {key: without_forms(item) for key, item in value.items()}
    if isinstance(value, list):
        return [without_forms(item) for item in value]
    return value


class FormOfAddressTests(unittest.TestCase):
    """`form` is needed only by a page that shows a text with forms."""

    def trees(self, site, invitations):
        report = F.Collector()
        index = _schema.check_data(site, invitations, report)
        self.assertEqual(report.errors, [])
        self.assertTrue(index.ok)
        pages, _usage = _page.build_pages(site, invitations, F.settings(), report)
        return pages, report

    def test_a_page_without_texts_of_forms_needs_no_form(self):
        site = without_forms(R.ru_site())
        invitations = R.ru_invitations()
        for invitation in invitations:
            invitation.pop("form")
        pages, report = self.trees(site, invitations)
        self.assertEqual(report.errors, [])
        for page in pages:
            self.assertEqual((page["form"], page["informal"], page["formal"]), ("", False, False))
        # the same texts as with a form
        expected, _usage = _page.build_pages(site, R.ru_invitations(), F.settings())
        self.assertEqual(
            [page["sections"] for page in pages], [page["sections"] for page in expected]
        )

    def test_a_page_with_a_text_of_forms_needs_one(self):
        invitations = R.ru_invitations()
        invitations[1].pop("form")
        _pages, report = self.trees(R.ru_site(), invitations)
        # once per page, with the first field that needs it
        self.assertEqual(
            report.errors,
            [
                "invitation #2: field 'form' is required: this page shows a text with forms of "
                "address (first: site.json field 'sections[1].widgets[2].text'); set "
                '"informal" or "formal"'
            ],
        )

    def test_a_named_text_with_forms_counts(self):
        site = without_forms(R.ru_site())
        site["texts"]["wait"] = {"informal": "Wait for us", "formal": "Please wait for us"}
        invitations = R.ru_invitations()
        invitations[0].pop("form")
        # a note has no forms, but the named texts in it take the form of the page
        invitations[0]["sections"]["personal"]["note"] = "{text:wait}"
        _pages, report = self.trees(site, invitations)
        self.assertEqual(
            report.errors,
            [
                "invitation #1: field 'form' is required: this page shows a text with forms of "
                "address (first: field 'sections.personal.note'); set \"informal\" or \"formal\""
            ],
        )
        # a section before the note
        self.assertEqual(site["sections"][1]["id"], "invite")
        site["sections"][1]["widgets"].insert(0, {"type": "text", "text": "{text:wait}"})
        _pages, report = self.trees(site, invitations)
        self.assertEqual(len(report.errors), 1)
        self.assertIn("(first: site.json field 'sections[1].widgets[0].text')", report.errors[0])

    def test_without_a_report_the_tree_is_refused(self):
        invitation = R.ru_invitations()[1]
        invitation.pop("form")
        with self.assertRaises(_page.TextError) as caught:
            _page.build_page(R.ru_site(), invitation, F.settings())
        self.assertIn("field 'form' is required", str(caught.exception))

    def test_the_aliases_and_the_canonical_names_give_the_same_page(self):
        names = {"ty": "informal", "vy": "formal"}
        renamed = R.ru_invitations()
        for invitation in renamed:
            invitation["form"] = names[invitation["form"]]
        self.assertEqual(build(invitations=renamed), build())


class RegistryTextTests(unittest.TestCase):
    """The descriptions of the registries and the texts of a programme are
    texts like any other: they stay on the page of the guest."""

    @staticmethod
    def with_texts(site, _invitations):
        site["texts"]["wait"] = {
            "ty": "Просим тебя подождать у входа.",
            "vy": "Просим вас подождать у входа.",
        }
        site["events"]["ceremony"]["description"] = "Зал небольшой. {text:wait}"
        site["locations"]["manor"]["description"] = {
            "ty": "Тебя встретят у ворот, {greeting}",
            "vy": "Вас встретят у ворот, {greeting}",
        }
        site["schedules"]["dinner"][0]["title"] = {"ty": "Встречаем тебя", "vy": "Встречаем вас"}
        site["schedules"]["dinner"][0]["text"] = "Сбор к {eventTime}."

    @staticmethod
    def ceremony(page):
        return next(item for item in walk_events(page) if item["id"] == "ceremony")

    @staticmethod
    def place(page, location_id):
        places = [item["location"] for item in walk_events(page)]
        places += [widget["location"] for widget in widgets(page, "location")]
        return next(item for item in places if item["id"] == location_id)

    def test_an_event_description_uses_the_named_texts_in_the_form_of_the_guest(self):
        pages = build(self.with_texts)
        # invitation #1: ty, #5: vy
        self.assertEqual(
            self.ceremony(pages[0])["description"], "Зал небольшой. Просим тебя подождать у входа."
        )
        self.assertEqual(
            self.ceremony(pages[4])["description"], "Зал небольшой. Просим вас подождать у входа."
        )

    def test_a_place_description_has_forms_and_the_greeting(self):
        pages = build(self.with_texts)
        manor = self.place(pages[4], "manor")
        self.assertEqual(manor["description"], "Вас встретят у ворот, Дорогие Пегги и Виктор!")

    def test_a_programme_item_has_forms_and_placeholders(self):
        pages = build(self.with_texts)
        # the programme of the dinner; #1 sees it in the card of the event
        item = next(
            entry
            for page_event in walk_events(pages[0])
            if page_event["program"] is not None
            for entry in page_event["program"]["items"]
        )
        self.assertEqual(item["title"], "Встречаем тебя")
        # {eventTime} is that of the primary event of the guest, as everywhere
        self.assertEqual(item["text"], "Сбор к 16:00.")

    def test_a_description_without_a_text_is_left_as_it_is(self):
        manor = self.place(build()[0], "manor")
        self.assertEqual(manor["description"], R.RU_SITE["locations"]["manor"]["description"])


class DateTextTests(unittest.TestCase):
    """The dates in Russian: genitive months, capitalised weekdays, 24 hours."""

    def test_different_days(self):
        page = build()[0]
        self.assertEqual(
            [item["tabText"] for item in events_widget(page)["items"]],
            ["15 июня, 11:00", "15 июня, 16:00", "16 июня, 12:00"],
        )

    def test_event_strings(self):
        dinner = build()[0]["primaryEvent"]
        self.assertEqual(dinner["dateText"], "15 июня 2030")
        self.assertEqual(dinner["timeText"], "16:00")
        self.assertEqual(dinner["whenText"], "Суббота, 15 июня 2030, 16:00–23:30")

    def test_the_end_is_on_the_page_only_with_show_end(self):
        pages = build()
        brunch = next(e for e in events_widget(pages[0])["items"] if e["id"] == "brunch")
        self.assertEqual(brunch["whenText"], "Воскресенье, 16 июня 2030, 12:00")

        def change(site, invitations):
            site["events"]["dinner"]["showEnd"] = False
            site["events"]["brunch"]["showEnd"] = True
            site["events"]["ceremony"]["showEnd"] = True
            site["events"]["ceremony"].pop("end")

        page = build(change)[0]
        found = {item["id"]: item for item in events_widget(page)["items"]}
        self.assertEqual(found["dinner"]["whenText"], "Суббота, 15 июня 2030, 16:00")
        self.assertEqual(found["brunch"]["whenText"], "Воскресенье, 16 июня 2030, 12:00–15:00")
        self.assertEqual(found["ceremony"]["whenText"], "Суббота, 15 июня 2030, 11:00")

    def test_default_duration(self):
        pages = build(lambda s, i: s["events"]["brunch"].pop("end"), default_duration=timedelta(hours=2))
        brunch = next(e for e in events_widget(pages[0])["items"] if e["id"] == "brunch")
        self.assertEqual(brunch["endISO"], "2030-06-16T14:00:00+03:00")
        self.assertEqual(brunch["whenText"], "Воскресенье, 16 июня 2030, 12:00")

    def test_notes_get_placeholders(self):
        pages = build(lambda s, i: i[0]["sections"]["personal"].update(note="До {eventDate}, {{пока}}!"))
        self.assertEqual(section(pages[0], "personal")["note"], "До 15 июня 2030, {пока}!")

    def test_set_without_places(self):
        site = {"lang": "ru", **F.pending_site()}
        event = build(site=site, invitations=F.pending_invitations())[0]["primaryEvent"]
        self.assertEqual(event["whenText"], "Суббота, 10 августа 2030, 15:00")


class MediaTests(unittest.TestCase):
    def photos(self, mutate=None, **settings):
        page = build(mutate, **settings)[0]
        return {item["id"]: item for item in page["primaryEvent"]["location"]["photos"]}

    def test_labels(self):
        photos = self.photos()
        self.assertEqual(photos["venue-1"]["label"], "Усадьба со стороны пруда")
        self.assertEqual(photos["walk"]["label"], "Видео: Прогулка по усадьбе, 0:05")
        # the media widget without a layout: the grid
        story = widgets(build()[0], "media")[0]
        self.assertEqual(story["layout"], "grid")
        self.assertEqual(story["items"][1]["ratio"], "720 / 1280")

    def test_without_description_and_duration(self):
        def change(site, invitations):
            site["media"]["walk"].pop("alt")
            site["media"]["venue-1"].pop("alt")

        info = dict(F.MEDIA_INFO)
        info["walk.mp4"] = MediaInfo("walk.mp4")
        photos = self.photos(change, media_info=info)
        self.assertEqual((photos["walk"]["alt"], photos["walk"]["label"]), ("Видео", "Видео"))
        self.assertEqual(photos["venue-1"]["alt"], "Фотография")

    def test_credit_of_the_directions(self):
        place = build()[0]["primaryEvent"]["location"]
        self.assertEqual(place["directionsCredit"], R.RU_SITE["locations"]["manor"]["directionsCredit"])
        self.assertTrue(place["directionsCredit"].endswith("Картографическая служба Энска"))


def inline_texts(site: dict) -> dict:
    """The site as it would be written without named texts: the section
    `invite` holds the texts itself (without the common form)."""
    texts = site.pop("texts")
    for widget in site["sections"][1]["widgets"]:
        text = widget["text"]
        if isinstance(text, str) and text.startswith("{text:"):
            value = texts[text[len("{text:") : -1]]
            widget["text"] = (
                value if isinstance(value, str) else {form: value[form] for form in ("ty", "vy")}
            )
    return site


class NamedTextTests(unittest.TestCase):
    texts = {
        "announce": "Мы, {coupleNames}, женимся!",
        "invite": {
            "ty": "Ждём тебя {eventDate} в {eventTime}. {text:sign}",
            "vy": "Ждём вас {eventDate} в {eventTime}. {text:sign}",
            "all": "ALL-FORM {eventDate}",
        },
        "sign": "{{{coupleNames}}}",
    }

    def with_texts(self, site, _invitations):
        site.pop("linkPreview")
        site["texts"] = copy.deepcopy(self.texts)
        widgets = site["sections"][1]["widgets"]
        widgets[0]["text"] = "{text:announce}"
        widgets[2]["text"] = "{text:invite}"

    @staticmethod
    def invite_texts(page) -> list[str]:
        section = next(item for item in page["sections"] if item["id"] == "invite")
        return [widget["text"] for widget in section["widgets"]]

    def test_the_form_and_the_primary_event_of_the_guest(self):
        pages = build(self.with_texts)
        # invitation #2: ty, the main event; #3: ty, the registration first;
        # #5: vy, the registration first; #6: vy, the main event
        self.assertEqual(
            self.invite_texts(pages[1]),
            ["Мы, Алиса и Боб, женимся!", "Ждём тебя 15 июня 2030 в 16:00. {Алиса и Боб}"],
        )
        self.assertEqual(self.invite_texts(pages[2])[1], "Ждём тебя 15 июня 2030 в 11:00. {Алиса и Боб}")
        self.assertEqual(self.invite_texts(pages[4])[1], "Ждём вас 15 июня 2030 в 11:00. {Алиса и Боб}")
        self.assertEqual(self.invite_texts(pages[5])[1], "Ждём вас 15 июня 2030 в 16:00. {Алиса и Боб}")

    def test_the_common_form_is_not_used_on_pages(self):
        for page in build(self.with_texts):
            self.assertNotIn("ALL-FORM", repr(page))

    def test_a_note_may_use_a_text(self):
        def mutate(site, invitations):
            self.with_texts(site, invitations)
            invitations[1]["events"]["dinner"]["note"] = "{text:invite}"

        pages = build(mutate)
        cards = [widget for section in pages[1]["sections"] for widget in section["widgets"]
                 if widget["type"] == "events"][0]["items"]  # fmt: skip
        dinner = next(item for item in cards if item["id"] == "dinner")
        self.assertEqual(dinner["note"], "Ждём тебя 15 июня 2030 в 16:00. {Алиса и Боб}")


class NamedTextsChangeNothingTests(unittest.TestCase):
    """The control case with forms of address: the same texts written in
    place or as named texts give the same pages."""

    def render(self, site, invitations) -> list[tuple[str, str]]:
        report = F.Collector()
        index = _schema.check_data(site, invitations, report)
        self.assertTrue(index.ok, report.errors)
        trees, _usage = _page.build_pages(site, invitations, F.settings(), report)
        self.assertEqual(report.messages, [])
        template = support.build.load_template(support.ROOT / support.build.TEMPLATE_FILE)
        return support.build.render_pages(template, invitations, trees)

    def test_the_pages_are_byte_for_byte_the_same(self):
        site = R.ru_site()
        site.pop("linkPreview")  # the description needs the named texts
        before = self.render(inline_texts(copy.deepcopy(site)), R.ru_invitations())
        after = self.render(site, R.ru_invitations())
        self.assertEqual(len(before), len(R.RU_INVITATIONS))
        self.assertEqual(after, before)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
