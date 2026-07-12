"""Tests for the random-address command line interface."""

from __future__ import annotations

import json

import pytest

from random_address.cli import main

from .conftest import address


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    """Run the CLI and return its exit code, stdout and stderr."""
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out.strip(), captured.err.strip()


class TestGet:
    def test_bare_invocation_prints_one_address(self, capsys) -> None:
        code, out, _ = run(capsys)

        assert code == 0
        assert len(out.splitlines()) == 1

    def test_filters_without_naming_the_get_command(self, capsys) -> None:
        code, out, _ = run(capsys, "--state", "CA")

        assert code == 0
        assert ", CA " in out

    def test_count_prints_one_address_per_line(self, capsys) -> None:
        _, out, _ = run(capsys, "--state", "FL", "--count", "3")

        assert len(out.splitlines()) == 3

    def test_seed_makes_output_reproducible(self, capsys) -> None:
        _, first, _ = run(capsys, "--seed", "42", "--count", "3")
        _, second, _ = run(capsys, "--seed", "42", "--count", "3")

        assert first == second

    def test_json_format_emits_an_object_for_a_single_address(self, capsys) -> None:
        _, out, _ = run(capsys, "--format", "json", "--state", "CA")

        payload = json.loads(out)

        assert isinstance(payload, dict)
        assert payload["state"] == "CA"

    def test_json_format_emits_an_array_for_several_addresses(self, capsys) -> None:
        _, out, _ = run(capsys, "--format", "json", "--count", "2")

        payload = json.loads(out)

        assert isinstance(payload, list)
        assert len(payload) == 2

    def test_csv_format_has_a_header_and_a_row_per_address(self, capsys) -> None:
        _, out, _ = run(capsys, "--format", "csv", "--count", "2")

        lines = out.splitlines()

        assert lines[0] == "address1,address2,city,state,postal_code,lat,lng"
        assert len(lines) == 3

    def test_repeat_allows_more_addresses_than_exist(self, capsys, dataset) -> None:
        dataset(address())

        code, out, _ = run(capsys, "--count", "3", "--repeat")

        assert code == 0
        assert len(out.splitlines()) == 3

    def test_unknown_filter_reports_an_error(self, capsys) -> None:
        code, out, err = run(capsys, "--state", "ZZ")

        assert code == 1
        assert out == ""
        assert "No address matches" in err

    def test_negative_count_reports_an_error(self, capsys) -> None:
        code, _, err = run(capsys, "--count", "-1")

        assert code == 2
        assert "must not be negative" in err


class TestListings:
    @pytest.mark.parametrize("command", ["states", "cities", "postal-codes"])
    def test_text_listing_pairs_each_value_with_a_count(self, capsys, command: str) -> None:
        code, out, _ = run(capsys, command)

        assert code == 0
        assert all(line.split()[-1].isdigit() for line in out.splitlines())

    def test_json_listing_maps_values_to_counts(self, capsys) -> None:
        _, out, _ = run(capsys, "states", "--format", "json")

        payload = json.loads(out)

        assert payload["CA"] > 0

    def test_summary_reports_the_dataset_totals(self, capsys) -> None:
        _, out, _ = run(capsys, "summary", "--format", "json")

        payload = json.loads(out)

        assert payload["total_addresses"] > 0
        assert set(payload) == {
            "total_addresses",
            "unique_states",
            "unique_cities",
            "unique_postal_codes",
        }
