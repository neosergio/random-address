"""Public type definitions for the random_address package."""

from __future__ import annotations

from typing import TypeAlias, TypedDict

Seed: TypeAlias = int | float | str | bytes | bytearray | None
"""Anything accepted by :class:`random.Random`."""


class Coordinates(TypedDict):
    """Latitude and longitude of an address."""

    lat: float
    lng: float


class Address(TypedDict):
    """A single real US address that geocodes successfully."""

    address1: str
    address2: str
    city: str
    state: str
    postal_code: str
    coordinates: Coordinates


class Summary(TypedDict):
    """Dataset-wide statistics."""

    total_addresses: int
    unique_states: int
    unique_cities: int
    unique_postal_codes: int
