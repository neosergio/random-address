"""Tests for the maintainer ingest script in data/add_addresses.py.

The script is not shipped, but it decides what goes into the dataset, so its
normalization and its rejection rules are worth pinning down. OpenAddresses
sources vary wildly: some are ALL CAPS and abbreviated, some carry no postal
code, some no city.
"""

from __future__ import annotations

import argparse
import random

import pytest
from add_addresses import (
    _allocate,
    _balanced_sample,
    _convert,
    _key,
    normalize_street,
    titlecase,
)


def options(**overrides) -> argparse.Namespace:
    defaults = {"state": "NC", "city": None, "allow_missing_city": False, "city_map": {}}
    return argparse.Namespace(**{**defaults, **overrides})


def feature(**properties) -> dict:
    defaults = {
        "number": "212",
        "street": "HERON CT SW",
        "unit": "",
        "city": "BOLIVIA",
        "postcode": "28422",
        "region": "",
    }
    return {
        "properties": {**defaults, **properties},
        "geometry": {"coordinates": [-78.4, 33.9]},
    }


class TestTitlecase:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("BOLIVIA", "Bolivia"),
            ("OCEAN ISLE BEACH", "Ocean Isle Beach"),
            ("WINSTON-SALEM", "Winston-Salem"),
            # str.title() would give "Chrissy'S Court" here.
            ("CHRISSY'S COURT", "Chrissy's Court"),
            ("US 17", "US 17"),
            # Would become "U.s. 80" if U.S. were not a known route designator.
            ("U.S. 80", "U.S. 80"),
            ("Already Title Cased", "Already Title Cased"),
        ],
    )
    def test_capitalizes_without_mangling(self, raw: str, expected: str) -> None:
        assert titlecase(raw) == expected

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("MCCRORY", "McCrory"),
            ("MCKINLEYVILLE", "McKinleyville"),
            ("O'NEALS", "O'Neals"),
            ("D'ANGELO", "D'Angelo"),
            # Not a particle: the apostrophe is possessive, so the s stays lower.
            ("CHRISSY'S", "Chrissy's"),
        ],
    )
    def test_handles_name_particles(self, raw: str, expected: str) -> None:
        assert titlecase(raw) == expected

    @pytest.mark.parametrize("name", ["MacArthur", "McKee", "O'Neal", "McKinleyville", "LaSalle"])
    def test_leaves_existing_mixed_case_alone(self, name: str) -> None:
        # The dataset already ships MacArthur and McCrory. Re-normalizing must not
        # flatten them into Macarthur and Mccrory.
        assert titlecase(name) == name


class TestNormalizeStreet:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("HERON CT SW", "Heron Court Southwest"),
            ("MORGANS RIDGE SE", "Morgans Ridge Southeast"),
            ("MAGNOLIA DR", "Magnolia Drive"),
            ("N MAIN ST", "North Main Street"),
            ("11TH AVE", "11th Avenue"),
            ("SUNSET BLVD", "Sunset Boulevard"),
            # ST here is Saint, not Street: it is not in the suffix position.
            ("ST JOHNS RD", "St Johns Road"),
            ("US 17 HWY", "US 17 Highway"),
            ("93RD AVE", "93rd Avenue"),
        ],
    )
    def test_expands_abbreviations(self, raw: str, expected: str) -> None:
        assert normalize_street(raw) == expected

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            # Washington DC has streets named S and E. The leading letter is the
            # street name, not a direction, and expanding it invents a new street.
            ("S Street", "S Street"),
            ("E Street", "E Street"),
            ("S Street Northwest", "S Street Northwest"),
            # Here the leading letter really is a direction: a name follows it.
            ("N Main Street", "North Main Street"),
            ("SE 4th Avenue", "Southeast 4th Avenue"),
        ],
    )
    def test_only_expands_a_leading_directional_when_a_street_name_follows(
        self, raw: str, expected: str
    ) -> None:
        assert normalize_street(raw) == expected

    @pytest.mark.parametrize(
        "street",
        [
            "U.S. 5",  # an initialism
            "North U.S.A Drive",
            "South Highway A1A",  # a route designator, not a word
            "Vermont 5A",
            "WB&A Road",  # the Washington, Baltimore and Annapolis railroad
            "William E Summers III Avenue",  # a Roman numeral
        ],
    )
    def test_preserves_designators_and_initialisms(self, street: str) -> None:
        # Every one of these is a real address in the dataset, and every one is
        # mangled by a naive title-caser.
        assert normalize_street(street) == street

    def test_is_idempotent_on_already_clean_data(self) -> None:
        # Sources that already publish clean data must survive untouched.
        for street in ("East 11th Avenue", "Sycamore Street", "Heron Court Southwest"):
            assert normalize_street(street) == street


class TestConvert:
    def test_normalizes_a_typical_all_caps_record(self) -> None:
        address, reason = _convert(feature(), options())

        assert reason == ""
        assert address["address1"] == "212 Heron Court Southwest"
        assert address["city"] == "Bolivia"
        assert address["state"] == "NC"
        assert address["postal_code"] == "28422"

    def test_truncates_zip_plus_four(self) -> None:
        address, _ = _convert(feature(postcode="28422-1234"), options())

        assert address["postal_code"] == "28422"

    @pytest.mark.parametrize(
        ("overrides", "reason"),
        [
            ({"postcode": ""}, "bad postal code"),
            ({"postcode": "ABCDE"}, "bad postal code"),
            ({"city": ""}, "no city"),
            ({"number": ""}, "no street address"),
            ({"street": ""}, "no street address"),
        ],
    )
    def test_rejects_unusable_records(self, overrides: dict, reason: str) -> None:
        address, actual = _convert(feature(**overrides), options())

        assert address is None
        assert actual == reason

    def test_rejects_a_record_whose_region_contradicts_the_state(self) -> None:
        address, reason = _convert(feature(region="CA"), options(state="NC"))

        assert address is None
        assert reason == "state is CA, not NC"

    def test_city_option_fills_in_a_source_that_omits_it(self) -> None:
        address, _ = _convert(feature(city=""), options(city="Arlington"))

        assert address["city"] == "Arlington"

    def test_city_map_expands_a_source_that_publishes_codes(self) -> None:
        address, _ = _convert(
            feature(city="DURH"),
            options(city_map={"DURH": "Durham", "CHAP": "Chapel Hill"}),
        )

        assert address["city"] == "Durham"

    def test_city_map_preserves_names_it_does_not_cover(self) -> None:
        address, _ = _convert(feature(city="BOLIVIA"), options(city_map={"DURH": "Durham"}))

        assert address["city"] == "Bolivia"

    def test_rejects_a_corrupt_city_with_no_letters_in_it(self) -> None:
        # The Durham source contains one row whose city is a single quote mark.
        address, reason = _convert(feature(city='"'), options())

        assert address is None
        assert reason == "no city"

    def test_allow_missing_city_still_works(self) -> None:
        address, _ = _convert(feature(city=""), options(allow_missing_city=True))

        assert address["city"] == ""

    def test_rejects_coordinates_outside_the_us(self) -> None:
        outside = feature()
        outside["geometry"]["coordinates"] = [12.5, 48.1]

        address, reason = _convert(outside, options())

        assert address is None
        assert reason == "bad coordinates"


class TestKey:
    def address(self, **overrides) -> dict:
        base = {
            "state": "NC",
            "postal_code": "27701",
            "address1": "100 Main Street",
            "address2": "",
        }
        return {**base, **overrides}

    def test_two_units_at_one_street_address_are_not_duplicates(self) -> None:
        # 5,057 street addresses in the Durham source repeat with different units.
        # Without address2 in the key they collapse into one and the rest are
        # reported, wrongly, as duplicates.
        unit_1 = self.address(address2="#APT 1")
        unit_2 = self.address(address2="#APT 2")

        assert _key(unit_1) != _key(unit_2)

    def test_the_same_address_twice_is_a_duplicate(self) -> None:
        assert _key(self.address()) == _key(self.address())

    def test_matching_ignores_case(self) -> None:
        assert _key(self.address(address1="100 MAIN STREET")) == _key(
            self.address(address1="100 main street")
        )

    def test_the_same_street_in_two_states_is_not_a_duplicate(self) -> None:
        assert _key(self.address(state="NC")) != _key(self.address(state="CA"))


class TestAllocate:
    def test_splits_evenly_when_every_city_can_supply_its_share(self) -> None:
        assert _allocate(50, {"Charlotte": 900, "Raleigh": 900, "Durham": 900}) == {
            "Charlotte": 17,
            "Raleigh": 17,
            "Durham": 16,
        }

    def test_hands_a_short_city_s_shortfall_to_the_others(self) -> None:
        # Durham can only supply 3, so the sample is still 50, not 3 + 4 * 10.
        quotas = _allocate(50, {"Charlotte": 900, "Raleigh": 900, "Durham": 3, "Asheville": 900})

        assert quotas["Durham"] == 3
        assert sum(quotas.values()) == 50

    def test_never_exceeds_a_city_s_capacity(self) -> None:
        quotas = _allocate(100, {"Small": 2, "Tiny": 1})

        assert quotas == {"Small": 2, "Tiny": 1}
        assert sum(quotas.values()) == 3

    def test_hands_out_one_each_when_fewer_remain_than_cities(self) -> None:
        quotas = _allocate(2, {"A": 5, "B": 5, "C": 5})

        assert sum(quotas.values()) == 2
        assert sorted(quotas.values()) == [0, 1, 1]


class TestBalancedSample:
    def addresses(self, city: str, n: int) -> list[dict]:
        return [{"city": city, "address1": f"{i} Main Street"} for i in range(n)]

    def test_splits_the_count_across_the_named_cities(self) -> None:
        candidates = self.addresses("Charlotte", 100) + self.addresses("Raleigh", 100)

        selected = _balanced_sample(candidates, ["Charlotte", "Raleigh"], 10, random.Random(1))

        cities = [a["city"] for a in selected]
        assert len(selected) == 10
        assert cities.count("Charlotte") == 5
        assert cities.count("Raleigh") == 5

    def test_ignores_cities_not_named(self) -> None:
        candidates = self.addresses("Charlotte", 50) + self.addresses("Bolivia", 50)

        selected = _balanced_sample(candidates, ["Charlotte"], 10, random.Random(1))

        assert {a["city"] for a in selected} == {"Charlotte"}

    def test_matches_city_names_case_insensitively(self) -> None:
        candidates = self.addresses("Chapel Hill", 20)

        selected = _balanced_sample(candidates, ["chapel hill"], 5, random.Random(1))

        assert len(selected) == 5
        assert {a["city"] for a in selected} == {"Chapel Hill"}

    def test_returns_nothing_when_no_named_city_is_present(self) -> None:
        candidates = self.addresses("Charlotte", 50)

        assert _balanced_sample(candidates, ["Fresno"], 10, random.Random(1)) == []
