"""The description of the link preview of the Russian example set: a named
text with forms of address gives its common form, the same for every guest."""

from __future__ import annotations

import unittest

from tests import fixtures_ru as R
from tests import fixtures_v2 as F
from tools import _page, _schema


class LinkDescriptionTreeTests(unittest.TestCase):
    def test_the_main_event_and_the_common_form(self):
        site, invitations = R.ru_site(), R.ru_invitations()
        report = F.Collector()
        self.assertTrue(_schema.check_data(site, invitations, report).ok, report.errors)
        pages, _usage = _page.build_pages(site, invitations, F.settings(), report)
        expected = "Мы, Алиса и Боб, женимся! Ждём вас 15 июня 2030 в 16:00."
        # invitation #3 and #5 have the registration as their primary event;
        # #1 is addressed informally, #5 formally: the common form for both
        self.assertEqual({page["linkDescription"] for page in pages}, {expected})
        self.assertEqual(pages[2]["primaryEvent"]["id"], "ceremony")
        self.assertEqual((pages[0]["form"], pages[4]["form"]), ("informal", "formal"))
        self.assertEqual(report.messages, [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
