"""Loading and indexing of the bundled address dataset.

The dataset is read from disk exactly once per process and then kept in memory.
Lookup indexes are built lazily on first use, so filtering by state, city or
postal code is a dictionary hit rather than a scan over every address.

The data is stored as JSON Lines, one address per line, sorted by state, city,
postal code and street. That is what keeps data contributions reviewable: adding
a city shows up as a contiguous block of new lines rather than as a single
rewritten 500 KB line.
"""

from __future__ import annotations

import json
from collections import defaultdict
from functools import cache
from importlib import resources
from importlib.resources.abc import Traversable
from typing import Literal, TypeAlias

from .types import Address

DATA_FILE = ("data", "addresses-us.jsonl")

Field: TypeAlias = Literal["state", "city", "postal_code"]

FIELDS: tuple[Field, ...] = ("state", "city", "postal_code")


def normalize(field: Field, value: str) -> str:
    """Put a filter value into the same form used by the lookup indexes.

    State codes are compared upper-cased and city names case-folded, so that
    ``"ca"`` and ``"newark"`` match the same addresses as ``"CA"`` and
    ``"Newark"``. Runs of whitespace inside a city name collapse to one space,
    so ``"Saint  Paul"`` pasted from a form still finds Saint Paul.
    """
    if field == "state":
        return value.strip().upper()
    if field == "city":
        return " ".join(value.split()).casefold()
    return value.strip()


def data_source() -> Traversable:
    """Return the bundled dataset file.

    A zip-imported package gets a Traversable rather than a Path, and a
    third-party loader's Traversable is not guaranteed to take several children
    in one joinpath call, so the components are descended one at a time: every
    loader agrees on that. Both the loader and the dataset integrity tests come
    through here, so the walk is written once.

    The package is named from ``__name__`` rather than ``__package__``, which
    is typed ``str | None`` and would need narrowing for no benefit.
    """
    source = resources.files(__name__.rpartition(".")[0])
    for part in DATA_FILE:
        source = source.joinpath(part)

    return source


@cache
def load_addresses() -> tuple[Address, ...]:
    """Return every address in the bundled dataset.

    The result is cached, so the file is parsed only on the first call.
    """
    with data_source().open("r", encoding="utf-8") as handle:
        return tuple(json.loads(line) for line in handle if line.strip())


@cache
def index(field: Field) -> dict[str, tuple[Address, ...]]:
    """Return a mapping from a normalized field value to its addresses."""
    buckets: dict[str, list[Address]] = defaultdict(list)
    for address in load_addresses():
        value = address.get(field)
        if value:
            # pyrefly widens TypedDict.get on a Literal key to object; mypy
            # correctly infers str | None. Remove once pyrefly agrees.
            buckets[normalize(field, value)].append(address)  # pyrefly: ignore[bad-argument-type]
    return {key: tuple(addresses) for key, addresses in buckets.items()}


def matches(address: Address, field: Field, value: str) -> bool:
    """Report whether an address's field equals ``value`` after normalization."""
    own_value = address.get(field)
    if not own_value:
        return False
    # Same pyrefly TypedDict.get inference gap as in index().
    return normalize(field, own_value) == normalize(field, value)  # pyrefly: ignore[bad-argument-type]


def clear_caches() -> None:
    """Drop the cached dataset and indexes.

    Only needed by the test suite, which swaps the dataset out for fixtures.
    """
    load_addresses.cache_clear()
    index.cache_clear()
