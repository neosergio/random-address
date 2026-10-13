"""Functions to retrieve real random US addresses."""

from __future__ import annotations

import bisect
import math
import random as _random
from collections import Counter

from . import _dataset, _geo
from ._dataset import Field, matches, normalize
from .types import Address, Location, Seed, Summary

_SHARED_GENERATOR = _random.Random()

# A validated radius filter: the centre as (lat, lng), and the radius in km.
_Radius = tuple[_geo.Point, float]


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
    postal_code: str | int | None = None,
    near: Location | None = None,
    within_km: float | None = None,
    seed: Seed = None,
) -> Address:
    """Retrieve one real random address, optionally narrowed by filters.

    Filters combine, so passing both ``state`` and ``city`` returns an address
    that matches both. State codes and city names match case-insensitively.

    Args:
        state: Two-letter state code, for example ``"CA"``.
        city: City name, for example ``"Newark"``.
        postal_code: Postal code, for example ``"94560"``. An int is accepted
            and zero-padded, so ``6040`` means ``"06040"``.
        near: A point to search around: a ``(lat, lng)`` pair, a coordinates
            dictionary, or an address returned by an earlier call. Must be
            given together with ``within_km``.
        within_km: Keep only addresses within this many kilometres of
            ``near``. An address passed as ``near`` is itself within any
            radius, so it can be among the results.
        seed: Seed for a private random generator. Passing a seed makes the
            result reproducible without disturbing the global random state.

    Returns:
        An :class:`~random_address.types.Address` dictionary.

    Raises:
        ValueError: If only one of ``near`` and ``within_km`` is given, or
            either is out of range.
        NoMatchingAddressError: If no address matches the given filters.

    Example:
        >>> real_random_address(state="CA")
        {'address1': '37600 Sycamore Street', 'address2': '', 'city': 'Newark',
         'state': 'CA', 'postal_code': '94560',
         'coordinates': {'lat': 37.5261943, 'lng': -122.0304698}}
    """
    postal_code = _postal_code(postal_code)
    radius = _radius(near, within_km)
    pool = _pool(state=state, city=city, postal_code=postal_code, radius=radius)
    if not pool:
        raise NoMatchingAddressError(
            f"No address matches {_describe(state, city, postal_code, radius)}"
        )

    return _generator(seed).choice(pool)


def real_random_addresses(
    count: int = 1,
    *,
    state: str | None = None,
    city: str | None = None,
    postal_code: str | int | None = None,
    near: Location | None = None,
    within_km: float | None = None,
    seed: Seed = None,
    unique: bool = True,
) -> list[Address]:
    """Retrieve several real random addresses, optionally narrowed by filters.

    Args:
        count: How many addresses to return.
        state: Two-letter state code, for example ``"CA"``.
        city: City name, for example ``"Newark"``.
        postal_code: Postal code, for example ``"94560"``. An int is accepted
            and zero-padded, so ``6040`` means ``"06040"``.
        near: A point to search around: a ``(lat, lng)`` pair, a coordinates
            dictionary, or an address returned by an earlier call. Must be
            given together with ``within_km``.
        within_km: Keep only addresses within this many kilometres of
            ``near``. An address passed as ``near`` is itself within any
            radius, so it can be among the results.
        seed: Seed for a private random generator. The same seed and filters
            always produce the same addresses in the same order.
        unique: When true (the default) no address is returned twice. Pass
            ``False`` to sample with replacement.

    Returns:
        A list of :class:`~random_address.types.Address` dictionaries, empty
        when ``count`` is zero.

    Raises:
        ValueError: If ``count`` is negative, if only one of ``near`` and
            ``within_km`` is given, or if either is out of range.
        NoMatchingAddressError: If no address matches the given filters, or if
            ``unique`` is true and fewer than ``count`` addresses match.

    Example:
        >>> len(real_random_addresses(5, state="FL", seed=42))
        5
    """
    _check_count(count)
    postal_code = _postal_code(postal_code)
    radius = _radius(near, within_km)
    if count == 0:
        return []

    pool = _pool(state=state, city=city, postal_code=postal_code, radius=radius)
    if not pool:
        raise NoMatchingAddressError(
            f"No address matches {_describe(state, city, postal_code, radius)}"
        )

    generator = _generator(seed)
    if not unique:
        return generator.choices(pool, k=count)

    if count > len(pool):
        raise NoMatchingAddressError(
            f"Only {len(pool)} distinct addresses match "
            f"{_describe(state, city, postal_code, radius)}, but {count} were requested. "
            f"Pass unique=False to sample with replacement."
        )
    return generator.sample(pool, count)


def real_random_cluster(
    count: int,
    *,
    within_km: float,
    state: str | None = None,
    city: str | None = None,
    postal_code: str | int | None = None,
    seed: Seed = None,
) -> list[Address]:
    """Retrieve a group of real addresses that all lie close together.

    One matching address is chosen at random as the centre, and the group is
    filled from the matching addresses within ``within_km`` of it, so every
    address is at most ``within_km`` from the centre and at most twice that from
    each other. Centres that do not have enough neighbours are skipped, so the
    group can come from anywhere the filters allow rather than from one place
    you had to know about in advance. To build a group around a point of your
    own, use :func:`real_random_addresses` with ``near`` instead.

    Args:
        count: How many addresses the group holds, the centre included.
        within_km: The radius around the centre, in kilometres.
        state: Two-letter state code, for example ``"CA"``.
        city: City name, for example ``"Newark"``.
        postal_code: Postal code, for example ``"94560"``. An int is accepted
            and zero-padded, so ``6040`` means ``"06040"``.
        seed: Seed for a private random generator. The same seed and filters
            always produce the same group in the same order.

    Returns:
        ``count`` distinct addresses, the centre first. Empty when ``count`` is
        zero.

    Raises:
        ValueError: If ``count`` or ``within_km`` is negative, or ``within_km``
            is not a finite number.
        NoMatchingAddressError: If no address matches the filters, or none of
            them has ``count - 1`` neighbours within ``within_km``.

    Example:
        >>> group = real_random_cluster(5, within_km=2, state="VA", seed=1)
        >>> len(group)
        5
    """
    _check_count(count)
    postal_code = _postal_code(postal_code)
    # Validated through the same path as near/within_km, with a dummy centre,
    # so the two radius arguments reject exactly the same values.
    _radius((0.0, 0.0), within_km)
    if count == 0:
        return []

    pool = _pool(state=state, city=city, postal_code=postal_code)
    if not pool:
        raise NoMatchingAddressError(f"No address matches {_describe(state, city, postal_code)}")
    # Past this point there are addresses, so with no filters the scope is the
    # whole dataset, not the "empty dataset" _describe falls back to.
    filtered = any(value is not None for value in (state, city, postal_code))
    scope = f"matching {_describe(state, city, postal_code)}" if filtered else "in the dataset"
    if count > len(pool):
        raise NoMatchingAddressError(
            f"Only {len(pool)} addresses {scope}, so no group of {count} exists."
        )

    # Sorted by latitude, so each centre only measures the addresses in its own
    # latitude band instead of the whole pool. A degree of latitude is at least
    # 110.5 km anywhere, so this band can only be wider than needed, never
    # narrower.
    by_latitude = sorted(pool, key=lambda address: address["coordinates"]["lat"])
    latitudes = [address["coordinates"]["lat"] for address in by_latitude]
    band = within_km / 110.5

    generator = _generator(seed)
    centres = list(range(len(by_latitude)))
    generator.shuffle(centres)
    for index in centres:
        centre = by_latitude[index]
        point = (centre["coordinates"]["lat"], centre["coordinates"]["lng"])
        low = bisect.bisect_left(latitudes, point[0] - band)
        high = bisect.bisect_right(latitudes, point[0] + band)
        neighbours = [
            address
            for position in range(low, high)
            if position != index
            for address in (by_latitude[position],)
            if _geo.distance_km(
                point, (address["coordinates"]["lat"], address["coordinates"]["lng"])
            )
            <= within_km
        ]
        if len(neighbours) >= count - 1:
            return [centre, *generator.sample(neighbours, count - 1)]

    raise NoMatchingAddressError(
        f"No {count} addresses {scope} lie within {within_km:g} km of a common centre."
    )


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


def count(
    *,
    state: str | None = None,
    city: str | None = None,
    postal_code: str | int | None = None,
    near: Location | None = None,
    within_km: float | None = None,
) -> int:
    """Count the addresses matching the given filters, without drawing one.

    Filters combine and are matched exactly as they are by
    :func:`real_random_address`, so state codes and city names are
    case-insensitive and surrounding whitespace is ignored. Postal codes are
    matched exactly.

    Unlike the lookup functions, this returns ``0`` rather than raising when
    nothing matches: asking how many addresses there are is a question that a
    zero answers.

    Args:
        state: Two-letter state code, for example ``"CA"``. Counts every state
            when omitted.
        city: City name, for example ``"Newark"``. Counts every city when
            omitted.
        postal_code: Postal code, for example ``"94560"``. Counts every postal
            code when omitted.
        near: A point to search around: a ``(lat, lng)`` pair, a coordinates
            dictionary, or an address returned by an earlier call. Must be
            given together with ``within_km``.
        within_km: Keep only addresses within this many kilometres of
            ``near``. An address passed as ``near`` is itself within any
            radius, so it can be among the results.

    Returns:
        How many addresses match, or the size of the whole dataset when no
        filter is given.

    Example:
        >>> count()
        3400
        >>> count(state="CA")
        331
        >>> count(state="VA", city="Arlington")
        50
        >>> count(state="ZZ")
        0

    Raises:
        ValueError: If only one of ``near`` and ``within_km`` is given, or
            either is out of range. A bad radius is a mistake in the question,
            not an answer of zero.
    """
    postal_code = _postal_code(postal_code)
    radius = _radius(near, within_km)
    return len(_pool(state=state, city=city, postal_code=postal_code, radius=radius))


def _check_count(count: int) -> None:
    # bool is an int, and True would otherwise quietly mean one address.
    if isinstance(count, bool) or not isinstance(count, int):
        raise TypeError(f"count must be an int, got {count!r}")
    if count < 0:
        raise ValueError("count must not be negative")


def _postal_code(postal_code: str | int | None) -> str | None:
    """Accept a postal code as text, or as an int that lost its leading zeros.

    ``06040`` cannot be written as an int literal, and a ZIP read from a CSV or
    a spreadsheet often arrives as ``6040``. Padding to five digits recovers it
    exactly. Anything that is not a five-digit number is rejected rather than
    guessed at.
    """
    if postal_code is None or isinstance(postal_code, str):
        return postal_code
    if isinstance(postal_code, bool) or not isinstance(postal_code, int):
        raise TypeError(f"postal_code must be a str or an int, got {postal_code!r}")
    if not 0 <= postal_code <= 99999:
        raise ValueError(f"postal_code must have at most five digits, got {postal_code}")
    return f"{postal_code:05d}"


def _radius(near: Location | None, within_km: float | None) -> _Radius | None:
    """Validate the radius filter, which takes both of its arguments or neither.

    Either one alone is rejected rather than given a default. ``near`` with no
    radius has no sensible meaning, and ``within_km`` with no centre would be a
    filter that silently does nothing.
    """
    if near is None and within_km is None:
        return None
    if near is None:
        raise ValueError("within_km needs near, the point to measure from")
    if within_km is None:
        raise ValueError("near needs within_km, the radius to search")
    if isinstance(within_km, bool) or not isinstance(within_km, (int, float)):
        raise ValueError(f"within_km must be a number, got {within_km!r}")
    if not math.isfinite(within_km) or within_km < 0:
        raise ValueError(f"within_km must be a non-negative number, got {within_km}")
    return _geo.point(near), float(within_km)


def _pool(
    *,
    state: str | None,
    city: str | None,
    postal_code: str | None,
    radius: _Radius | None = None,
) -> tuple[Address, ...]:
    """Return every address matching all of the filters that were supplied."""
    candidates = _attribute_pool(state=state, city=city, postal_code=postal_code)
    if radius is None:
        return candidates

    centre, within_km = radius
    return tuple(
        address
        for address in candidates
        if _geo.distance_km(centre, (address["coordinates"]["lat"], address["coordinates"]["lng"]))
        <= within_km
    )


def _attribute_pool(
    *,
    state: str | None,
    city: str | None,
    postal_code: str | None,
) -> tuple[Address, ...]:
    """Return every address matching the state, city and postal code filters."""
    supplied: tuple[tuple[Field, str | None], ...] = (
        ("state", state),
        ("city", city),
        ("postal_code", postal_code),
    )
    active: dict[Field, str] = {field: value for field, value in supplied if value is not None}
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


def _describe(
    state: str | None,
    city: str | None,
    postal_code: str | None,
    radius: _Radius | None = None,
) -> str:
    """Render the active filters for an error message."""
    active = [
        f"{field}={value!r}"
        for field, value in (("state", state), ("city", city), ("postal_code", postal_code))
        if value is not None
    ]
    if radius is not None:
        (lat, lng), within_km = radius
        active.append(f"within_km={within_km:g} of ({lat:g}, {lng:g})")
    return ", ".join(active) if active else "an empty dataset"
