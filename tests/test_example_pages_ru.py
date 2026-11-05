"""The finished pages of the Russian example set (`examples/data-ru`): the
companion text in the form of address of each guest."""

from __future__ import annotations

import unittest

from tests import test_example_pages as pages


class RussianCompanionTests(pages.CompanionTests):
    DATA_SETS = ("data-ru",)
    OPENINGS = ("Мы, ", "Ждём ")
    COMPANION_WORD = "спутни"
    #: Four of eight guests come with a companion.
    COMPANIONS = {True: 4, False: 4}


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
