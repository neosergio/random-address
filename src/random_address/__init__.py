"""Retrieve real random US addresses, with coordinates, for tests and fixtures.

The addresses come from OpenAddresses, which collects data published by national,
state and local governments. Each one carries the latitude and longitude given by
that source, so it resolves to a real point on the map without a geocoding call.
"""

from .core import (
    NoMatchingAddressError,
    city_counts,
    count,
    list_cities,
    list_postal_codes,
    list_states,
    postal_code_counts,
    real_random_address,
    real_random_addresses,
    state_counts,
    summary,
)
from .types import Address, Coordinates, Seed, Summary

__all__ = [
    "Address",
    "Coordinates",
    "NoMatchingAddressError",
    "Seed",
    "Summary",
    "city_counts",
    "count",
    "list_cities",
    "list_postal_codes",
    "list_states",
    "postal_code_counts",
    "real_random_address",
    "real_random_addresses",
    "state_counts",
    "summary",
]

__version__ = "2.1.1"
