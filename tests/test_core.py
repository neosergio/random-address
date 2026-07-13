"""Tests for the public random_address API."""

from __future__ import annotations

import random
from importlib import metadata
from types import ModuleType

import pytest

import random_address
from random_address import (
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

from .conftest import address

ADDRESS_FIELDS = {"address1", "address2", "city", "state", "postal_code", "coordinates"}


class TestRealRandomAddress:
    def test_returns_a_fully_populated_address(self) -> None:
        result = real_random_address()

        assert set(result) == ADDRESS_FIELDS
        assert set(result["coordinates"]) == {"lat", "lng"}

    def test_filters_by_state(self) -> None:
        assert real_random_address(state="CA")["state"] == "CA"

    def test_filters_by_city(self) -> None:
        assert real_random_address(city="Newark")["city"] == "Newark"

    def test_filters_by_postal_code(self) -> None:
        assert real_random_address(postal_code="94560")["postal_code"] == "94560"

    def test_filters_combine(self, dataset) -> None:
        dataset(
            address(state="CA", city="Newark", address1="wanted"),
            address(state="CA", city="Fresno", address1="wrong city"),
            address(state="FL", city="Newark", address1="wrong state"),
        )

        assert real_random_address(state="CA", city="Newark")["address1"] == "wanted"

    def test_state_matching_is_case_insensitive(self) -> None:
        assert real_random_address(state="ca")["state"] == "CA"

    def test_city_matching_is_case_insensitive(self) -> None:
        assert real_random_address(city="newark")["city"] == "Newark"

    def test_surrounding_whitespace_is_ignored(self) -> None:
        assert real_random_address(state=" CA ")["state"] == "CA"

    def test_unknown_filter_raises(self) -> None:
        with pytest.raises(NoMatchingAddressError, match="state='ZZ'"):
            real_random_address(state="ZZ")

    def test_contradictory_filters_raise(self, dataset) -> None:
        dataset(address(state="CA", city="Newark"))

        with pytest.raises(NoMatchingAddressError):
            real_random_address(state="FL", city="Newark")

    def test_empty_dataset_raises_instead_of_crashing(self, dataset) -> None:
        dataset()

        # v1 raised IndexError here, contradicting its own documented contract.
        with pytest.raises(NoMatchingAddressError):
            real_random_address()

    def test_same_seed_gives_the_same_address(self) -> None:
        assert real_random_address(seed=42) == real_random_address(seed=42)

    def test_different_seeds_give_different_addresses(self) -> None:
        assert real_random_address(seed=1) != real_random_address(seed=2)

    def test_seeding_does_not_disturb_the_global_random_stream(self) -> None:
        random.seed(1234)
        expected = [random.random() for _ in range(3)]

        random.seed(1234)
        real_random_address(seed=99)
        actual = [random.random() for _ in range(3)]

        assert actual == expected


class TestRealRandomAddresses:
    def test_returns_the_requested_count(self) -> None:
        assert len(real_random_addresses(5)) == 5

    def test_defaults_to_one(self) -> None:
        assert len(real_random_addresses()) == 1

    def test_zero_count_returns_empty_list(self) -> None:
        assert real_random_addresses(0) == []

    def test_negative_count_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be negative"):
            real_random_addresses(-1)

    def test_results_are_distinct_by_default(self, dataset) -> None:
        dataset(*(address(address1=f"{n} Main Street") for n in range(10)))

        results = real_random_addresses(10)

        assert len({result["address1"] for result in results}) == 10

    def test_requesting_more_than_exist_raises(self, dataset) -> None:
        dataset(address(), address())

        with pytest.raises(NoMatchingAddressError, match="Only 2 distinct addresses"):
            real_random_addresses(3)

    def test_repeats_are_allowed_when_unique_is_false(self, dataset) -> None:
        dataset(address())

        assert len(real_random_addresses(4, unique=False)) == 4

    def test_respects_filters(self) -> None:
        results = real_random_addresses(3, state="FL")

        assert [result["state"] for result in results] == ["FL", "FL", "FL"]

    def test_same_seed_gives_the_same_sequence(self) -> None:
        assert real_random_addresses(5, seed=42) == real_random_addresses(5, seed=42)

    def test_unknown_filter_raises(self) -> None:
        with pytest.raises(NoMatchingAddressError):
            real_random_addresses(2, state="ZZ")


class TestDatasetIntrospection:
    def test_list_states_is_sorted_and_unique(self) -> None:
        states = list_states()

        assert states == sorted(set(states))
        assert "CA" in states

    def test_listings_agree_with_their_counts(self) -> None:
        assert list_states() == list(state_counts())
        assert list_cities() == list(city_counts())
        assert list_postal_codes() == list(postal_code_counts())

    def test_counts_add_up_to_the_dataset_size(self, dataset) -> None:
        dataset(
            address(state="CA"),
            address(state="CA"),
            address(state="FL"),
        )

        assert state_counts() == {"CA": 2, "FL": 1}

    def test_blank_values_are_left_out_of_listings(self, dataset) -> None:
        # 20 records in the bundled dataset have no city at all.
        dataset(address(city="Newark"), address(city=""))

        assert list_cities() == ["Newark"]

    def test_summary_matches_the_listings(self) -> None:
        statistics = summary()

        assert statistics["unique_states"] == len(list_states())
        assert statistics["unique_cities"] == len(list_cities())
        assert statistics["unique_postal_codes"] == len(list_postal_codes())
        assert statistics["total_addresses"] > 0


class TestPackageSurface:
    def test_public_names_are_exactly_what_is_advertised(self) -> None:
        exported = {
            name
            for name, value in vars(random_address).items()
            if not name.startswith("_") and not isinstance(value, ModuleType)
        }

        assert exported == set(random_address.__all__)

    @pytest.mark.parametrize("leaked", ["os", "sys", "json", "random", "logging", "Counter"])
    def test_standard_library_is_not_re_exported(self, leaked: str) -> None:
        # v1 used a bare star-import, which leaked all of these into the package.
        assert not hasattr(random_address, leaked)

    def test_bundled_dataset_records_all_have_the_same_shape(self) -> None:
        from random_address._dataset import load_addresses

        assert {frozenset(record) for record in load_addresses()} == {frozenset(ADDRESS_FIELDS)}

    def test_version_matches_the_installed_distribution(self) -> None:
        # __version__ and the version in pyproject.toml are two places to bump,
        # and a release tag will happily go out with them disagreeing.
        assert random_address.__version__ == metadata.version("random-address")
