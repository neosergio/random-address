"""Tests for the public random_address API."""

from __future__ import annotations

import random
from collections.abc import Callable
from importlib import metadata
from types import ModuleType

import pytest

import random_address
from random_address import (
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

from .conftest import InstallDataset, address

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

    def test_filters_combine(self, dataset: InstallDataset) -> None:
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

    def test_contradictory_filters_raise(self, dataset: InstallDataset) -> None:
        dataset(address(state="CA", city="Newark"))

        with pytest.raises(NoMatchingAddressError):
            real_random_address(state="FL", city="Newark")

    def test_empty_dataset_raises_instead_of_crashing(self, dataset: InstallDataset) -> None:
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

    def test_results_are_distinct_by_default(self, dataset: InstallDataset) -> None:
        dataset(*(address(address1=f"{n} Main Street") for n in range(10)))

        results = real_random_addresses(10)

        assert len({result["address1"] for result in results}) == 10

    def test_requesting_more_than_exist_raises(self, dataset: InstallDataset) -> None:
        dataset(address(), address())

        with pytest.raises(NoMatchingAddressError, match="Only 2 distinct addresses"):
            real_random_addresses(3)

    def test_repeats_are_allowed_when_unique_is_false(self, dataset: InstallDataset) -> None:
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

    def test_counts_add_up_to_the_dataset_size(self, dataset: InstallDataset) -> None:
        dataset(
            address(state="CA"),
            address(state="CA"),
            address(state="FL"),
        )

        assert state_counts() == {"CA": 2, "FL": 1}

    def test_blank_values_are_left_out_of_listings(self, dataset: InstallDataset) -> None:
        # 20 records in the bundled dataset have no city at all.
        dataset(address(city="Newark"), address(city=""))

        assert list_cities() == ["Newark"]

    def test_summary_matches_the_listings(self) -> None:
        statistics = summary()

        assert statistics["unique_states"] == len(list_states())
        assert statistics["unique_cities"] == len(list_cities())
        assert statistics["unique_postal_codes"] == len(list_postal_codes())
        assert statistics["total_addresses"] == count()

    @pytest.mark.parametrize("counts", [state_counts, city_counts, postal_code_counts])
    def test_every_address_is_counted_exactly_once(
        self, counts: Callable[[], dict[str, int]]
    ) -> None:
        # _counts skips a falsy value, so these sums only equal the total because
        # no bundled record has a blank state, city or postal code. The dataset
        # integrity tests are what hold that true; if one ever regressed, the
        # blank would vanish from the listings and this is where it would surface.
        assert sum(counts().values()) == count()


class TestCount:
    """Counting is asserted against the other introspection functions.

    Hardcoding 3300 here would mean every data expansion broke the suite, which
    is exactly the friction the dataset workflow is meant to avoid. The numbers
    these tests use come from the dataset itself; what is pinned is that count()
    and the counts dictionaries can never disagree.
    """

    def test_with_no_filters_counts_the_whole_dataset(self) -> None:
        assert count() == summary()["total_addresses"]

    def test_agrees_with_state_counts(self) -> None:
        assert {state: count(state=state) for state in list_states()} == state_counts()

    def test_agrees_with_city_counts(self) -> None:
        assert {city: count(city=city) for city in list_cities()} == city_counts()

    def test_agrees_with_postal_code_counts(self) -> None:
        expected = postal_code_counts()
        assert {code: count(postal_code=code) for code in list_postal_codes()} == expected

    def test_counts_what_the_lookup_actually_returns(self) -> None:
        # The pool count() measures is the pool real_random_addresses draws from,
        # so asking for exactly that many distinct addresses must not raise.
        total = count(state="VA", city="Arlington")

        assert len(real_random_addresses(total, state="VA", city="Arlington", seed=1)) == total

    def test_state_matching_ignores_case_and_whitespace(self) -> None:
        assert count(state="ca") == count(state="CA") == count(state="  Ca  ")

    def test_city_matching_ignores_case_and_whitespace(self) -> None:
        city = list_cities()[0]

        assert count(city=city.upper()) == count(city=city.lower()) == count(city=f"  {city}  ")

    def test_postal_code_is_matched_exactly(self) -> None:
        code = list_postal_codes()[0]

        assert count(postal_code=code) > 0
        # A prefix is a different postal code, not a looser spelling of this one.
        assert count(postal_code=code[:-1]) == 0

    @pytest.mark.parametrize(
        "filters",
        [
            {},
            {"state": "CA"},
            {"city": "Arlington"},
            {"postal_code": "22204"},
            {"state": "VA", "city": "Arlington"},
            {"state": "ZZ"},
        ],
    )
    def test_is_always_a_non_negative_int(self, filters: dict[str, str]) -> None:
        result = count(**filters)

        assert type(result) is int
        assert result >= 0

    @pytest.mark.parametrize(
        "filters",
        [
            {"state": "ZZ"},
            {"city": "Nowhere"},
            {"postal_code": "00000"},
            {"state": "ZZ", "city": "Nowhere"},
            {"state": "ZZ", "city": "Nowhere", "postal_code": "00000"},
            # Each value exists, but no single address carries both.
            {"state": "CA", "city": "Arlington"},
        ],
    )
    def test_counts_zero_when_nothing_matches(self, filters: dict[str, str]) -> None:
        assert count(**filters) == 0

    def test_no_match_counts_zero_rather_than_raising(self) -> None:
        # real_random_address raises here; count answers the question instead.
        with pytest.raises(NoMatchingAddressError):
            real_random_address(state="ZZ")

        assert count(state="ZZ") == 0

    def test_filters_combine(self, dataset: InstallDataset) -> None:
        dataset(
            address(state="CA", city="Newark", postal_code="94560"),
            address(state="CA", city="Fresno", postal_code="93650"),
            address(state="FL", city="Newark", postal_code="32409"),
        )

        assert count() == 3
        assert count(state="CA") == 2
        assert count(city="Newark") == 2
        assert count(postal_code="94560") == 1
        assert count(state="CA", city="Newark") == 1
        assert count(state="CA", postal_code="93650") == 1
        assert count(city="Newark", postal_code="32409") == 1
        assert count(state="CA", city="Newark", postal_code="94560") == 1

    def test_narrowing_never_widens(self, dataset: InstallDataset) -> None:
        dataset(
            address(state="CA", city="Newark", postal_code="94560"),
            address(state="CA", city="Newark", postal_code="94561"),
            address(state="CA", city="Fresno", postal_code="93650"),
        )

        assert count(state="CA", city="Newark") <= count(state="CA")
        assert count(state="CA", city="Newark", postal_code="94560") <= count(
            state="CA", city="Newark"
        )

    def test_an_empty_dataset_counts_zero(self, dataset: InstallDataset) -> None:
        dataset()

        assert count() == 0


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
