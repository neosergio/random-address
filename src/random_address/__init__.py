"""Retrieve real random US addresses that geocode successfully."""

from .core import (
    NoMatchingAddressError,
    city_counts,
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
    "list_cities",
    "list_postal_codes",
    "list_states",
    "postal_code_counts",
    "real_random_address",
    "real_random_addresses",
    "state_counts",
    "summary",
]

__version__ = "2.0.0"
