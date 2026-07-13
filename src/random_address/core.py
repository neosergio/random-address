"""Functions to retrieve real random US addresses."""

from __future__ import annotations

import random as _random
from collections import Counter

from . import _dataset
from ._dataset import Field, matches, normalize
from .types import Address, Seed, Summary

_SHARED_GENERATOR = _random.Random()


class NoMatchingAddressError(LookupError):
    """No address in the dataset satisfies the request.

    Raised when the given filters match nothing, and when
    :func:`real_random_addresses` is asked for more distinct addresses than the
    filters can supply.
    """


def real_random_address(
    *,
    state: str | None = None,
    city: str | None = None,
    postal_code: str | None = None,
    seed: Seed = None,
) -> Address:
    """Retrieve one real random address, optionally narrowed by filters.

    Filters combine, so passing both ``state`` and ``city`` returns an address
    that matches both. State codes and city names match case-insensitively.

    Args:
        state: Two-letter state code, for example ``"CA"``.
        city: City name, for example ``"Newark"``.
        postal_code: Postal code, for example ``"94560"``.
        seed: Seed for a private random generator. Passing a seed makes the
            result reproducible without disturbing the global random state.

    Returns:
        An :class:`~random_address.types.Address` dictionary.

    Raises:
        NoMatchingAddressError: If no address matches the given filters.

    Example:
        >>> real_random_address(state="CA")
        {'address1': '37600 Sycamore Street', 'address2': '', 'city': 'Newark',
         'state': 'CA', 'postal_code': '94560',
         'coordinates': {'lat': 37.5261943, 'lng': -122.0304698}}
    """
    pool = _pool(state=state, city=city, postal_code=postal_code)
    if not pool:
        raise NoMatchingAddressError(f"No address matches {_describe(state, city, postal_code)}")

    return _generator(seed).choice(pool)


def real_random_addresses(
    count: int = 1,
    *,
    state: str | None = None,
    city: str | None = None,
    postal_code: str | None = None,
    seed: Seed = None,
    unique: bool = True,
) -> list[Address]:
    """Retrieve several real random addresses, optionally narrowed by filters.

    Args:
        count: How many addresses to return.
        state: Two-letter state code, for example ``"CA"``.
        city: City name, for example ``"Newark"``.
        postal_code: Postal code, for example ``"94560"``.
        seed: Seed for a private random generator. The same seed and filters
            always produce the same addresses in the same order.
        unique: When true (the default) no address is returned twice. Pass
            ``False`` to sample with replacement.

    Returns:
        A list of :class:`~random_address.types.Address` dictionaries, empty
        when ``count`` is zero.

    Raises:
        ValueError: If ``count`` is negative.
        NoMatchingAddressError: If no address matches the given filters, or if
            ``unique`` is true and fewer than ``count`` addresses match.

    Example:
        >>> len(real_random_addresses(5, state="FL", seed=42))
        5
    """
    if count < 0:
        raise ValueError("count must not be negative")
    if count == 0:
        return []

    pool = _pool(state=state, city=city, postal_code=postal_code)
    if not pool:
        raise NoMatchingAddressError(f"No address matches {_describe(state, city, postal_code)}")

    generator = _generator(seed)
    if not unique:
        return generator.choices(pool, k=count)

    if count > len(pool):
        raise NoMatchingAddressError(
            f"Only {len(pool)} distinct addresses match "
            f"{_describe(state, city, postal_code)}, but {count} were requested. "
            f"Pass unique=False to sample with replacement."
        )
    return generator.sample(pool, count)


def list_states() -> list[str]:
    """Return every state code in the dataset, alphabetically sorted."""
    return list(state_counts())


def list_cities() -> list[str]:
    """Return every city name in the dataset, alphabetically sorted."""
    return list(city_counts())


def list_postal_codes() -> list[str]:
    """Return every postal code in the dataset, alphabetically sorted."""
    return list(postal_code_counts())


def state_counts() -> dict[str, int]:
    """Return how many addresses the dataset holds per state code."""
    return _counts("state")


def city_counts() -> dict[str, int]:
    """Return how many addresses the dataset holds per city."""
    return _counts("city")


def postal_code_counts() -> dict[str, int]:
    """Return how many addresses the dataset holds per postal code."""
    return _counts("postal_code")


def summary() -> Summary:
    """Return dataset-wide statistics."""
    return {
        "total_addresses": len(_dataset.load_addresses()),
        "unique_states": len(_counts("state")),
        "unique_cities": len(_counts("city")),
        "unique_postal_codes": len(_counts("postal_code")),
    }


def _pool(
    *,
    state: str | None,
    city: str | None,
    postal_code: str | None,
) -> tuple[Address, ...]:
    """Return every address matching all of the filters that were supplied."""
    active: dict[Field, str] = {
        field: value
        for field, value in (("state", state), ("city", city), ("postal_code", postal_code))
        if value is not None
    }
    if not active:
        return _dataset.load_addresses()

    # Start from the smallest matching bucket, so combined filters never scan
    # the whole dataset.
    candidates = min(
        (_dataset.index(field).get(normalize(field, value), ()) for field, value in active.items()),
        key=len,
    )
    if len(active) == 1:
        return candidates

    return tuple(
        address
        for address in candidates
        if all(matches(address, field, value) for field, value in active.items())
    )


def _counts(field: Field) -> dict[str, int]:
    """Count addresses per value of ``field``, keeping the dataset's own casing."""
    counter = Counter(address[field] for address in _dataset.load_addresses() if address.get(field))
    return dict(sorted(counter.items()))


def _generator(seed: Seed) -> _random.Random:
    """Return a private generator when seeded, otherwise the package's shared one.

    A seeded call gets its own :class:`random.Random`, so reproducible fixtures
    never perturb the random stream the rest of the process draws from.
    """
    return _SHARED_GENERATOR if seed is None else _random.Random(seed)


def _describe(state: str | None, city: str | None, postal_code: str | None) -> str:
    """Render the active filters for an error message."""
    active = [
        f"{field}={value!r}"
        for field, value in (("state", state), ("city", city), ("postal_code", postal_code))
        if value is not None
    ]
    return ", ".join(active) if active else "an empty dataset"
