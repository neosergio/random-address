"""Tests for COVERAGE.md and the script that generates it."""

from __future__ import annotations

from typing import Any

from coverage_report import COVERAGE, STATE_NAMES, _read_dataset, render

from .test_dataset import US_STATES


def test_coverage_page_matches_the_dataset() -> None:
    # A data change that forgets to regenerate the page fails here, on the pull
    # request, instead of shipping a page that describes an older dataset.
    assert COVERAGE.read_text(encoding="utf-8") == render(_read_dataset()), (
        "COVERAGE.md is stale. Run: python data/coverage_report.py"
    )


def test_names_every_state_the_dataset_accepts() -> None:
    assert set(STATE_NAMES) == US_STATES


def test_counts_cities_case_insensitively() -> None:
    def address(city: str, postal_code: str) -> dict[str, Any]:
        return {"state": "VA", "city": city, "postal_code": postal_code}

    page = render([address("Arlington", "22204"), address("ARLINGTON", "22205")])

    assert "| VA | Virginia | 2 | 1 | 2 |" in page
    assert "- **1** of 51 states" in page
