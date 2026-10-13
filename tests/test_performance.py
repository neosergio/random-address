"""Opt-in timing budgets for the public lookups.

Skipped by default: wall-clock assertions are noisy on shared CI runners, and a
flaky failure teaches people to ignore red builds. Run them when touching the
loader, the indexes or the filters:

    RUN_PERFORMANCE_TESTS=1 pytest tests/test_performance.py

The budgets are deliberately loose, several times what a laptop measures (warm
lookups take microseconds; a radius scan over the whole dataset about 2 ms).
They exist to catch an accidental return to re-parsing the dataset on
every call (which 2.0.0 fixed, at roughly 3 ms a lookup), not to benchmark.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from time import perf_counter

import pytest

import random_address

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_PERFORMANCE_TESTS") != "1",
    reason="performance tests are opt-in; set RUN_PERFORMANCE_TESTS=1",
)

ITERATIONS = 1000


def seconds_per_call(call: Callable[[], object]) -> float:
    call()  # Load and index the dataset outside the timed window.
    start = perf_counter()
    for _ in range(ITERATIONS):
        call()
    return (perf_counter() - start) / ITERATIONS


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(lambda: random_address.real_random_address(), id="unfiltered"),
        pytest.param(lambda: random_address.real_random_address(state="CA"), id="state"),
        pytest.param(
            lambda: random_address.real_random_address(state="VA", city="Arlington"),
            id="state-and-city",
        ),
        pytest.param(lambda: random_address.count(postal_code="22204"), id="count"),
        pytest.param(
            lambda: random_address.real_random_addresses(25, state="FL"), id="batch-of-25"
        ),
    ],
)
def test_warm_lookups_stay_under_a_millisecond(call: Callable[[], object]) -> None:
    assert seconds_per_call(call) < 0.001


def test_an_unfiltered_radius_search_stays_under_ten_milliseconds() -> None:
    # The radius filter scans every candidate the other filters leave. With no
    # other filter that is the whole dataset, so this is the worst case, and the
    # one to revisit if the dataset ever grows past what a scan can afford.
    def call() -> object:
        return random_address.count(near=(38.88, -77.10), within_km=5)

    assert seconds_per_call(call) < 0.01
