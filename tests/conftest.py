"""Shared fixtures.

The ``dataset`` fixture swaps the bundled data out for a small in-memory one.
That is how the no-match and empty-dataset paths get covered: relying on a state
being absent from the real dataset would turn every data expansion into a test
failure.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest

from random_address import _dataset
from random_address.types import Address


def address(
    *,
    address1: str = "1 Main Street",
    address2: str = "",
    city: str = "Springfield",
    state: str = "CA",
    postal_code: str = "90001",
    lat: float = 1.0,
    lng: float = 2.0,
) -> Address:
    """Build a single address, overriding only the fields a test cares about."""
    return {
        "address1": address1,
        "address2": address2,
        "city": city,
        "state": state,
        "postal_code": postal_code,
        "coordinates": {"lat": lat, "lng": lng},
    }


@pytest.fixture
def dataset(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[..., None]]:
    """Replace the bundled dataset for the duration of a test."""

    def install(*addresses: Address) -> None:
        _dataset.clear_caches()
        monkeypatch.setattr(_dataset, "load_addresses", lambda: tuple(addresses))

    yield install
    # Restore the real loader before clearing, so the caches being cleared are
    # the cached functions and not the stand-in.
    monkeypatch.undo()
    _dataset.clear_caches()
