"""Integrity checks on the bundled dataset.

Address data arrives from contributors through GitHub issues, so these run in CI
on every pull request. They are what make it safe to accept outside data: a
malformed record fails here rather than in a user's test suite.

They also pin the file's physical layout. The dataset is one address per line,
sorted, so that adding a city shows up as a reviewable diff. An editor that
reflows the file, or a contributor who hand-appends instead of running
data/add_addresses.py, breaks that property silently. These tests make it loud.

The file is parsed inside fixtures rather than at import. Parsing it at import
means a malformed line blows up collection, and the very test written to report
that malformed line never gets to run.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from importlib import resources
from math import isfinite

import pytest
from add_addresses import DIRECTIONALS, STREET_SUFFIXES, normalize_street

from random_address._dataset import DATA_FILE

ADDRESS_FIELDS = {"address1", "address2", "city", "state", "postal_code", "coordinates"}

STATE = re.compile(r"^[A-Z]{2}$")
POSTAL_CODE = re.compile(r"^\d{5}$")

# Loose bounds covering the continental US, Alaska, Hawaii and Puerto Rico.
MIN_LAT, MAX_LAT = 17.0, 72.0
MIN_LNG, MAX_LNG = -180.0, -64.0


@pytest.fixture(scope="session")
def lines() -> list[str]:
    source = resources.files("random_address").joinpath(*DATA_FILE)
    return source.read_text(encoding="utf-8").splitlines()


@pytest.fixture(scope="session")
def records(lines: list[str]) -> list[dict]:
    return [json.loads(line) for line in lines]


def sort_key(record: dict) -> tuple[str, ...]:
    # Missing fields would raise KeyError here and mask the field-presence test,
    # which reports the real problem far more clearly.
    return tuple(
        record.get(field, "") for field in ("state", "city", "postal_code", "address1", "address2")
    )


class TestLayout:
    def test_every_line_is_one_json_object(self, lines: list[str]) -> None:
        for number, line in enumerate(lines, start=1):
            assert line.strip(), f"line {number} is blank"
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                pytest.fail(f"line {number} is not valid JSON: {error}")
            assert isinstance(record, dict), f"line {number} is not an object"

    def test_lines_are_canonically_formatted(self, lines: list[str]) -> None:
        # Guards against an editor or formatter reflowing the file, which would
        # turn every future data contribution into an unreadable diff.
        for number, line in enumerate(lines, start=1):
            assert json.dumps(json.loads(line)) == line, (
                f"line {number} is not canonical json.dumps output; "
                f"re-run data/add_addresses.py rather than editing by hand"
            )

    def test_records_are_sorted(self, records: list[dict]) -> None:
        assert sorted(records, key=sort_key) == records, (
            "dataset is out of order; re-run data/add_addresses.py, which sorts on write"
        )


class TestRecords:
    def test_every_record_has_exactly_the_expected_fields(self, records: list[dict]) -> None:
        for record in records:
            assert set(record) == ADDRESS_FIELDS, record

    @pytest.mark.parametrize("field", ["address1", "city", "state", "postal_code"])
    def test_required_fields_are_non_empty_strings(self, records: list[dict], field: str) -> None:
        for record in records:
            value = record[field]
            assert isinstance(value, str) and value.strip(), f"{field} is empty in {record}"

    def test_address2_is_a_string_and_may_be_blank(self, records: list[dict]) -> None:
        # A unit or apartment number is genuinely optional.
        for record in records:
            assert isinstance(record["address2"], str)

    def test_state_is_a_two_letter_code(self, records: list[dict]) -> None:
        for record in records:
            assert STATE.match(record["state"]), record

    def test_postal_code_is_five_digits(self, records: list[dict]) -> None:
        for record in records:
            assert POSTAL_CODE.match(record["postal_code"]), record

    def test_coordinates_are_finite_and_inside_the_us(self, records: list[dict]) -> None:
        for record in records:
            coordinates = record["coordinates"]
            assert set(coordinates) == {"lat", "lng"}, record

            lat, lng = coordinates["lat"], coordinates["lng"]
            assert isinstance(lat, float) and isfinite(lat), record
            assert isinstance(lng, float) and isfinite(lng), record
            assert MIN_LAT <= lat <= MAX_LAT, record
            assert MIN_LNG <= lng <= MAX_LNG, record

    def test_street_abbreviations_are_spelled_out(self, records: list[dict]) -> None:
        # 50 Arlington records shipped as "1172 N VERMONT ST" because the old
        # ingest script did no normalization. Only the final token is checked:
        # DC really does have a street named S ("1200 S Street"), and "4221 U.S. 5"
        # is a highway, so neither is an abbreviation to expand.
        abbreviations = set(STREET_SUFFIXES) | set(DIRECTIONALS)

        offenders = [
            record["address1"]
            for record in records
            if record["address1"].split()[-1].upper() in abbreviations
        ]

        assert not offenders, (
            f"{len(offenders)} addresses end in an unexpanded abbreviation, "
            f"for example {offenders[:3]}"
        )

    def test_normalizing_the_dataset_again_changes_nothing(self, records: list[dict]) -> None:
        """The ingest normalizer must be a no-op on data it has already produced.

        This is the strongest guard on the pair: it catches both an un-normalized
        record that slipped in, and a normalizer that would corrupt good data.
        It is how "S Street" (a real DC street), "Highway A1A", "WB&A Road" and
        "Summers III Avenue" were caught, all of which a naive title-caser breaks.
        """
        house_number = re.compile(r"^(\d+\S*)\s+(.*)$")
        damaged = []

        for record in records:
            match = house_number.match(record["address1"])
            if not match:
                continue
            number, street = match.groups()
            renormalized = f"{number} {normalize_street(street)}"
            if renormalized != record["address1"]:
                damaged.append((record["address1"], renormalized))

        assert not damaged, (
            f"{len(damaged)} addresses change when re-normalized, for example {damaged[:3]}. "
            f"Either the record is not normalized, or normalize_street corrupts it."
        )

    def test_there_are_no_duplicate_addresses(self, records: list[dict]) -> None:
        counts = Counter(
            (
                record["state"],
                record["postal_code"],
                record["address1"].casefold(),
                record["address2"].casefold(),
            )
            for record in records
        )
        duplicates = [key for key, total in counts.items() if total > 1]

        assert not duplicates, f"duplicate addresses: {sorted(duplicates)[:5]}"
