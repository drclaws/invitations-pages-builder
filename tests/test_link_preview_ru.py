"""The link preview in Russian: the tags of a site with `"lang": "ru"`, and
the description of the Russian example set, where a named text with forms
of address gives its common form, the same for every guest."""

from __future__ import annotations

import unittest

from tests import fixtures_ru as R
from tests import fixtures_v2 as F
from tests import support
from tests.test_link_preview import REAL_TEMPLATE, head, site_with_preview
from tools import _page, _schema


class RussianTagsTests(support.CliTestCase):
    template = REAL_TEMPLATE

    def test_the_tags_follow_the_language(self):
        support.write_data(self.data, site=site_with_preview(lang="ru"))
        result = self.build_in_process()
        self.assertEqual(result.returncode, 0, result.stderr)
        title = f"Приглашение · {support.COUPLE_NAMES}"
        for token in (support.TOKEN_A, support.TOKEN_B, support.TOKEN_C):
            page = head((self.out / token / "index.html").read_text(encoding="utf-8"))
            meta = dict(page.meta)
            self.assertEqual((page.title, meta["og:title"], meta["og:image:alt"]), (title,) * 3)
            self.assertEqual(meta["og:locale"], "ru_RU")
            # the description takes the date in the Russian pattern
            self.assertIn(" 1 июня 2030 ", meta["og:description"])


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
