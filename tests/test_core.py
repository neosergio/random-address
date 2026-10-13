"""Tests for the public random_address API."""

from __future__ import annotations

import random
from collections.abc import Callable
from importlib import metadata
from types import ModuleType
from typing import Any, TypedDict

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
    real_random_cluster,
    state_counts,
    summary,
)

from .conftest import InstallDataset, address


class AttributeFilters(TypedDict, total=False):
    """The string filters, so ``count(**filters)`` type-checks against them alone."""

    state: str
    city: str
    postal_code: str


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
    def test_is_always_a_non_negative_int(self, filters: AttributeFilters) -> None:
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
    def test_counts_zero_when_nothing_matches(self, filters: AttributeFilters) -> None:
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


class TestNear:
    """The radius filter. Coordinates are on the equator, where 0.01 degrees of
    longitude is about 1.11 km, so the expected distances are easy to check."""

    @pytest.fixture
    def points(self, dataset: InstallDataset) -> None:
        dataset(
            address(address1="centre", lat=0.0, lng=0.0),
            address(address1="one km east", lat=0.0, lng=0.009),
            address(address1="two km east", lat=0.0, lng=0.018, state="FL"),
            address(address1="far away", lat=0.0, lng=1.0),
        )

    @pytest.mark.usefixtures("points")
    def test_keeps_only_addresses_inside_the_radius(self) -> None:
        found = real_random_addresses(2, near=(0.0, 0.0), within_km=1.5)

        assert {result["address1"] for result in found} == {"centre", "one km east"}

    @pytest.mark.usefixtures("points")
    def test_count_agrees_with_the_lookup(self) -> None:
        assert count(near=(0.0, 0.0), within_km=1.5) == 2
        assert count(near=(0.0, 0.0), within_km=2.5) == 3
        assert count(near=(0.0, 0.0), within_km=500) == 4

    @pytest.mark.usefixtures("points")
    def test_the_boundary_is_inclusive(self) -> None:
        assert count(near=(0.0, 0.0), within_km=0) == 1

    @pytest.mark.usefixtures("points")
    def test_accepts_an_address_as_the_centre(self) -> None:
        centre = real_random_address(near=(0.0, 0.0), within_km=0)

        # An address is within any radius of itself, so it counts.
        assert count(near=centre, within_km=1.5) == 2

    @pytest.mark.usefixtures("points")
    def test_accepts_a_coordinates_dict_as_the_centre(self) -> None:
        assert count(near={"lat": 0.0, "lng": 0.0}, within_km=1.5) == 2

    @pytest.mark.usefixtures("points")
    def test_combines_with_the_other_filters(self) -> None:
        assert count(state="CA", near=(0.0, 0.0), within_km=2.5) == 2
        assert real_random_address(state="FL", near=(0.0, 0.0), within_km=2.5)["address1"] == (
            "two km east"
        )

    @pytest.mark.usefixtures("points")
    def test_nothing_in_range_raises_and_names_the_radius(self) -> None:
        with pytest.raises(NoMatchingAddressError, match=r"within_km=0\.5 of \(10, 10\)"):
            real_random_address(near=(10.0, 10.0), within_km=0.5)

        assert count(near=(10.0, 10.0), within_km=0.5) == 0

    @pytest.mark.usefixtures("points")
    def test_too_few_in_range_raises_for_unique_samples(self) -> None:
        with pytest.raises(NoMatchingAddressError, match="Only 2 distinct"):
            real_random_addresses(3, near=(0.0, 0.0), within_km=1.5)

    @pytest.mark.parametrize(
        ("near", "within_km", "message"),
        [
            ((0.0, 0.0), None, "near needs within_km"),
            (None, 5, "within_km needs near"),
            ((0.0, 0.0), -1, "non-negative"),
            ((0.0, 0.0), float("nan"), "non-negative"),
            ((0.0, 0.0), float("inf"), "non-negative"),
            ((0.0, 0.0), True, "must be a number"),
            ((0.0, 0.0), "5", "must be a number"),
            ((91.0, 0.0), 5, "latitude"),
            ((0.0, -181.0), 5, "longitude"),
            ((float("nan"), 0.0), 5, "latitude"),
            ((0.0,), 5, "pair"),
            ("0,0", 5, "pair"),
            ({"lat": 0.0}, 5, "numeric"),
            ({"lat": True, "lng": 0.0}, 5, "numeric"),
            ({"coordinates": None}, 5, "'lat' and 'lng'"),
        ],
    )
    def test_rejects_a_malformed_radius(self, near: Any, within_km: Any, message: str) -> None:
        # A mistake in the question is a ValueError everywhere, never a count of 0.
        for call in (
            lambda: real_random_address(near=near, within_km=within_km),
            lambda: real_random_addresses(1, near=near, within_km=within_km),
            lambda: count(near=near, within_km=within_km),
        ):
            with pytest.raises(ValueError, match=message):
                call()

    def test_a_bad_radius_is_reported_even_for_zero_addresses(self) -> None:
        with pytest.raises(ValueError, match="within_km needs near"):
            real_random_addresses(0, within_km=5)

    def test_works_against_the_real_dataset(self) -> None:
        centre = real_random_address(state="VA", city="Arlington", seed=1)
        nearby = real_random_addresses(5, near=centre, within_km=10, seed=1)

        assert all(result["state"] in {"VA", "DC", "MD"} for result in nearby)


class TestInputForms:
    def test_an_int_postal_code_is_zero_padded(self, dataset: InstallDataset) -> None:
        # 06040 cannot be written as an int, and a ZIP read from a spreadsheet
        # often arrives as 6040. Padding recovers it exactly.
        dataset(address(postal_code="06040"), address(postal_code="94560"))

        assert real_random_address(postal_code=6040)["postal_code"] == "06040"
        assert count(postal_code=94560) == 1
        assert len(real_random_addresses(1, postal_code=6040)) == 1

    @pytest.mark.parametrize(
        ("postal_code", "error"),
        [(True, TypeError), (6040.0, TypeError), (-1, ValueError), (100000, ValueError)],
    )
    def test_rejects_postal_codes_that_are_not_five_digits(
        self, postal_code: Any, error: type[Exception]
    ) -> None:
        with pytest.raises(error):
            count(postal_code=postal_code)

    def test_whitespace_inside_a_city_name_is_collapsed(self, dataset: InstallDataset) -> None:
        dataset(address(city="Saint Paul"))

        assert count(city="Saint   Paul") == 1
        assert count(city=" saint\tpaul ") == 1

    @pytest.mark.parametrize("bad", [2.0, "2", True])
    def test_count_must_be_an_int(self, bad: Any) -> None:
        with pytest.raises(TypeError, match="count must be an int"):
            real_random_addresses(bad)


class TestRealRandomCluster:
    """Points on the equator, where 0.009 degrees of longitude is about 1 km."""

    @pytest.fixture
    def towns(self, dataset: InstallDataset) -> None:
        dataset(
            # Three addresses within a kilometre of each other, in CA...
            address(address1="a", lat=0.0, lng=0.0),
            address(address1="b", lat=0.0, lng=0.004),
            address(address1="c", lat=0.0, lng=0.008),
            # ...a pair close together in FL...
            address(address1="d", state="FL", lat=0.0, lng=5.0),
            address(address1="e", state="FL", lat=0.0, lng=5.004),
            # ...and one on its own.
            address(address1="f", lat=0.0, lng=10.0),
        )

    @pytest.mark.usefixtures("towns")
    def test_every_address_is_within_the_radius_of_the_centre(self) -> None:
        for seed in range(20):
            group = real_random_cluster(3, within_km=1, seed=seed)

            assert {member["address1"] for member in group} == {"a", "b", "c"}
            # The centre comes first; the group's spread is twice the radius.
            centre = group[0]["coordinates"]["lng"]
            assert all(abs(m["coordinates"]["lng"] - centre) <= 0.009 for m in group)

    @pytest.mark.usefixtures("towns")
    def test_filters_narrow_where_the_group_can_come_from(self) -> None:
        group = real_random_cluster(2, within_km=1, state="FL", seed=1)

        assert {member["address1"] for member in group} == {"d", "e"}

    @pytest.mark.usefixtures("towns")
    def test_is_reproducible_with_a_seed(self) -> None:
        assert real_random_cluster(2, within_km=1, seed=9) == real_random_cluster(
            2, within_km=1, seed=9
        )

    @pytest.mark.usefixtures("towns")
    def test_raises_when_no_group_is_compact_enough(self) -> None:
        # b sits about 0.445 km from both a and c, so 0.5 km would succeed with b
        # as the centre. At 0.4 km no address reaches two others.
        with pytest.raises(NoMatchingAddressError, match=r"within 0\.4 km"):
            real_random_cluster(3, within_km=0.4)

    @pytest.mark.usefixtures("towns")
    def test_raises_when_the_filters_hold_fewer_than_count(self) -> None:
        with pytest.raises(NoMatchingAddressError, match="Only 2 addresses matching state='FL'"):
            real_random_cluster(3, within_km=1000, state="FL")

    @pytest.mark.usefixtures("towns")
    def test_unknown_filter_raises(self) -> None:
        with pytest.raises(NoMatchingAddressError, match="state='ZZ'"):
            real_random_cluster(2, within_km=1, state="ZZ")

    @pytest.mark.usefixtures("towns")
    def test_a_single_address_is_its_own_group(self) -> None:
        assert len(real_random_cluster(1, within_km=0, seed=3)) == 1

    def test_zero_count_returns_an_empty_group(self) -> None:
        assert real_random_cluster(0, within_km=1) == []

    @pytest.mark.parametrize(
        ("kwargs", "error"),
        [
            ({"count": -1, "within_km": 1}, ValueError),
            ({"count": 2, "within_km": -1}, ValueError),
            ({"count": 2, "within_km": float("inf")}, ValueError),
            ({"count": 2.0, "within_km": 1}, TypeError),
        ],
    )
    def test_rejects_malformed_arguments(
        self, kwargs: dict[str, Any], error: type[Exception]
    ) -> None:
        with pytest.raises(error):
            real_random_cluster(**kwargs)

    def test_finds_a_group_in_the_real_dataset(self) -> None:
        group = real_random_cluster(5, within_km=2, state="VA", seed=1)

        assert len({member["address1"] for member in group}) == 5
        assert all(member["state"] == "VA" for member in group)


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
