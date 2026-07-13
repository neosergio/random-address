"""Command line interface for random-address."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections.abc import Sequence

from . import __version__
from .core import (
    NoMatchingAddressError,
    city_counts,
    postal_code_counts,
    real_random_addresses,
    state_counts,
    summary,
)
from .types import Address

CSV_COLUMNS = ("address1", "address2", "city", "state", "postal_code", "lat", "lng")

# Flags that belong to the top-level parser rather than to the default command.
_TOP_LEVEL_FLAGS = frozenset({"-h", "--help", "-V", "--version"})


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line interface and return a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(_with_default_command(argv if argv is not None else sys.argv[1:]))

    try:
        output = args.handler(args)
    except NoMatchingAddressError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(output)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="random-address",
        description="Retrieve real random US addresses, with coordinates, for tests and fixtures.",
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers()

    get = subparsers.add_parser(
        "get",
        help="Retrieve random addresses (the default command).",
        description=(
            "Retrieve random addresses. Filters combine, so --state and --city "
            "together match addresses satisfying both."
        ),
    )
    get.add_argument("--state", help="Two-letter state code, for example CA.")
    get.add_argument("--city", help="City name, for example Newark.")
    get.add_argument("--postal-code", dest="postal_code", help="Postal code, for example 94560.")
    get.add_argument("-n", "--count", type=int, default=1, help="How many addresses to return.")
    get.add_argument(
        "--seed",
        help="Seed for reproducible output. The same seed and filters always give the same result.",
    )
    get.add_argument(
        "--repeat",
        action="store_true",
        help="Allow the same address to be returned more than once.",
    )
    get.add_argument(
        "-f",
        "--format",
        choices=("text", "json", "csv"),
        default="text",
        help=(
            "Output format. json emits a single object when --count is 1, "
            "otherwise an array. Defaults to text."
        ),
    )
    get.set_defaults(handler=_handle_get)

    for name, counts, help_text in (
        ("states", state_counts, "List the state codes in the dataset."),
        ("cities", city_counts, "List the cities in the dataset."),
        ("postal-codes", postal_code_counts, "List the postal codes in the dataset."),
    ):
        listing = subparsers.add_parser(name, help=help_text, description=help_text)
        listing.add_argument(
            "-f",
            "--format",
            choices=("text", "json"),
            default="text",
            help="Output format. Defaults to text.",
        )
        listing.set_defaults(handler=_make_listing_handler(counts))

    stats = subparsers.add_parser(
        "summary",
        help="Show dataset-wide statistics.",
        description="Show dataset-wide statistics.",
    )
    stats.add_argument(
        "-f",
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    stats.set_defaults(handler=_handle_summary)

    return parser


def _with_default_command(argv: Sequence[str]) -> list[str]:
    """Insert the implicit ``get`` command, so ``random-address --state CA`` works."""
    arguments = list(argv)
    if not arguments:
        return ["get"]
    if arguments[0].startswith("-") and arguments[0] not in _TOP_LEVEL_FLAGS:
        return ["get", *arguments]
    return arguments


def _handle_get(args: argparse.Namespace) -> str:
    addresses = real_random_addresses(
        args.count,
        state=args.state,
        city=args.city,
        postal_code=args.postal_code,
        seed=args.seed,
        unique=not args.repeat,
    )

    if args.format == "json":
        payload = addresses[0] if args.count == 1 else addresses
        return json.dumps(payload, indent=2)
    if args.format == "csv":
        return _to_csv(addresses)
    return "\n".join(_to_text(address) for address in addresses)


def _make_listing_handler(counts):
    def handler(args: argparse.Namespace) -> str:
        values = counts()
        if args.format == "json":
            return json.dumps(values, indent=2)
        width = max((len(value) for value in values), default=0)
        return "\n".join(f"{value:<{width}}  {count}" for value, count in values.items())

    return handler


def _handle_summary(args: argparse.Namespace) -> str:
    statistics = summary()
    if args.format == "json":
        return json.dumps(statistics, indent=2)
    width = max(len(key) for key in statistics)
    return "\n".join(f"{key:<{width}}  {value}" for key, value in statistics.items())


def _to_text(address: Address) -> str:
    """Render an address as a single human-readable line."""
    street = " ".join(part for part in (address["address1"], address["address2"]) if part)
    return f"{street}, {address['city']}, {address['state']} {address['postal_code']}"


def _to_csv(addresses: list[Address]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for address in addresses:
        writer.writerow(
            (
                address["address1"],
                address["address2"],
                address["city"],
                address["state"],
                address["postal_code"],
                address["coordinates"]["lat"],
                address["coordinates"]["lng"],
            )
        )
    return buffer.getvalue().rstrip("\n")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
