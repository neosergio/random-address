"""Add addresses to the bundled dataset from an OpenAddresses GeoJSON file.

This is a maintainer tool, not part of the published package. It exists to serve
the workflow in the README: somebody opens an issue asking for a city, you
download the matching GeoJSON from OpenAddresses, and you sample a handful of
addresses from it.

    python data/add_addresses.py arlington.geojson --state VA --city Arlington
    python data/add_addresses.py boise.geojson --state ID --count 50 --seed 7
    python data/add_addresses.py vermont.geojson --state VT --replace-state
    python data/add_addresses.py nc.geojson --state NC --count 50 \
        --cities "Charlotte,Raleigh,Durham,Asheville,Wilmington"

Records are validated before they are sampled, so a run always yields the number
of good addresses you asked for rather than that many candidates. Anything
rejected is reported by reason.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, TypeGuard

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET = REPO_ROOT / "src" / "random_address" / "data" / "addresses-us.jsonl"

POSTCODE = re.compile(r"^(\d{5})(?:-\d{4})?$")

# Loose bounds covering the continental US, Alaska, Hawaii and Puerto Rico. The
# state label comes from the command line rather than from the data, so a
# tighter per-state box would mostly be checking the operator, not the source.
MIN_LAT, MAX_LAT = 17.0, 72.0
MIN_LNG, MAX_LNG = -180.0, -64.0

DEFAULT_COUNT = 50

# Many OpenAddresses sources publish ALL CAPS, abbreviated data ("212 HERON CT
# SW", "BOLIVIA"), and the dataset is written out title-cased and spelled out
# ("108 East 11th Avenue", "Anchorage"). Normalizing on the way in keeps a
# contributed city from looking like a different library's data.
DIRECTIONALS = {
    "N": "North",
    "S": "South",
    "E": "East",
    "W": "West",
    "NE": "Northeast",
    "NW": "Northwest",
    "SE": "Southeast",
    "SW": "Southwest",
}

STREET_SUFFIXES = {
    "ALY": "Alley",
    "AVE": "Avenue",
    "BLVD": "Boulevard",
    "BND": "Bend",
    "BRG": "Bridge",
    "CIR": "Circle",
    "CMN": "Common",
    "CRES": "Crescent",
    "CT": "Court",
    "CTR": "Center",
    "CV": "Cove",
    "DR": "Drive",
    "EXT": "Extension",
    "FRK": "Fork",
    "GDN": "Garden",
    "GLN": "Glen",
    "GRV": "Grove",
    "HL": "Hill",
    "HLS": "Hills",
    "HTS": "Heights",
    "HWY": "Highway",
    "KNL": "Knoll",
    "LN": "Lane",
    "LNDG": "Landing",
    "MDW": "Meadow",
    "MNR": "Manor",
    "PKWY": "Parkway",
    "PL": "Place",
    "PLZ": "Plaza",
    "PT": "Point",
    "RD": "Road",
    "RDG": "Ridge",
    "RTE": "Route",
    "SQ": "Square",
    "ST": "Street",
    "TER": "Terrace",
    "TERR": "Terrace",
    "TPKE": "Turnpike",
    "TRCE": "Trace",
    "TRL": "Trail",
    "VIS": "Vista",
    "VLG": "Village",
    "VW": "View",
    "XING": "Crossing",
}

# Route designators stay upper-cased: "US 17", "NC 211", "SR 1105". Dotted forms
# such as "U.S. 5" are handled by _is_dotted_initialism rather than listed here.
ROUTE_PREFIXES = {"US", "NC", "SR", "CR", "FM", "I", "SC", "TH"}

# Suffixes in both their abbreviated and spelled-out forms, used to tell a
# directional apart from a street actually named after a letter.
SUFFIX_WORDS = {suffix.upper() for suffix in STREET_SUFFIXES.values()} | set(STREET_SUFFIXES)

# "William E Summers III Avenue" is a real address. Single letters are left out:
# I, V, X and C are far more often initials or street names than numerals.
ROMAN_NUMERALS = {"II", "III", "IV", "VI", "VII", "VIII", "IX", "XI", "XII"}

# "93RD" becomes "93rd", but "5A" and "A1A" are route designators and stay put.
ORDINAL = re.compile(r"^(\d+)(ST|ND|RD|TH)$", re.IGNORECASE)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    existing = _read_dataset()
    if args.replace_state:
        kept = [a for a in existing if a["state"] != args.state]
        print(f"Dropping {len(existing) - len(kept)} existing {args.state} addresses")
        existing = kept

    seen = {_key(address) for address in existing}
    rejected: Counter[str] = Counter()
    candidates: list[dict[str, Any]] = []

    for feature in _read_features(args.source):
        address, reason = _convert(feature, args)
        if address is None:
            rejected[reason] += 1
            continue
        key = _key(address)
        if key in seen:
            rejected["duplicate"] += 1
            continue
        seen.add(key)
        candidates.append(address)

    if not candidates:
        print("No usable addresses found.", file=sys.stderr)
        _report(rejected)
        _explain_wholesale_rejection(rejected)
        return 1

    generator = random.Random(args.seed)
    if args.cities:
        selected = _balanced_sample(candidates, args.cities, args.count, generator)
    else:
        count = min(args.count, len(candidates))
        if count < args.count:
            print(f"Warning: only {count} usable addresses available, asked for {args.count}")
        selected = generator.sample(candidates, count)

    if not selected:
        print("No usable addresses found.", file=sys.stderr)
        return 1

    print(f"Selected {len(selected)} addresses for {args.state}")
    _report_by_city(selected)
    _report(rejected)

    if args.dry_run:
        print("\nDry run, nothing written. Sample:")
        for address in selected[:5]:
            print(
                f"  {address['address1']}, {address['city']}, "
                f"{address['state']} {address['postal_code']}"
            )
        return 0

    merged = sorted(existing + selected, key=_sort_key)
    _write_dataset(merged)

    print(f"\nWrote {len(merged)} addresses to {_display_path(DATASET)}")
    print("Remember to credit the source under Attribution in README.md.")
    return 0


def _display_path(path: Path) -> Path:
    """Show the dataset path relative to the caller, when that makes sense.

    relative_to raises when the working directory is not an ancestor, and doing
    that here would replace the "Wrote N addresses" confirmation with a traceback
    on a run that had already succeeded.
    """
    try:
        return path.relative_to(Path.cwd())
    except ValueError:
        return path


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("source", type=Path, help="OpenAddresses GeoJSON file.")
    parser.add_argument(
        "--state",
        required=True,
        type=lambda value: value.strip().upper(),
        help="Two-letter state code to file these addresses under.",
    )
    parser.add_argument(
        "--city",
        help="City name, used only for records whose source has no city of its own.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        help=f"How many addresses to sample. Defaults to {DEFAULT_COUNT}.",
    )
    parser.add_argument(
        "--city-map",
        type=_city_map,
        default={},
        dest="city_map",
        help="Rename city values on the way in, for sources that publish codes "
        'rather than names. For example "DURH=Durham,CHAP=Chapel Hill".',
    )
    parser.add_argument(
        "--cities",
        type=_city_list,
        default=[],
        help="Comma-separated cities to sample from, for example "
        '"Charlotte,Raleigh,Chapel Hill". The count is split evenly between them. '
        "Without this, the sample is drawn from the whole file.",
    )
    parser.add_argument("--seed", help="Seed, so a sample can be reproduced.")
    parser.add_argument(
        "--allow-missing-city",
        action="store_true",
        help="Keep records with no city instead of rejecting them. They will be "
        "reachable by state and postal code but absent from the city listings.",
    )
    parser.add_argument(
        "--replace-state",
        action="store_true",
        help="Drop the existing addresses for this state before adding. Use when "
        "re-importing a state from a better source.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would happen without writing the dataset.",
    )

    args = parser.parse_args(argv)
    if len(args.state) != 2:
        parser.error("--state must be a two-letter code, for example VA")
    if args.count < 1:
        parser.error("--count must be at least 1")
    return args


def _read_features(path: Path) -> Iterator[dict[str, Any]]:
    """Yield features from either a line-delimited or a FeatureCollection file.

    OpenAddresses ships line-delimited GeoJSON, but exports and hand-edited files
    are often a single FeatureCollection object, so both are accepted.
    """
    text = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        for line in text.splitlines():
            if line.strip():
                yield json.loads(line)
        return

    if isinstance(payload, dict) and "features" in payload:
        yield from payload["features"]
    elif isinstance(payload, list):
        yield from payload
    else:
        yield payload


def _convert(
    feature: dict[str, Any],
    args: argparse.Namespace,
) -> tuple[dict[str, Any] | None, str]:
    """Turn one GeoJSON feature into an address, or explain why it cannot be."""
    properties = feature.get("properties") or {}

    number = str(properties.get("number") or "").strip()
    street = str(properties.get("street") or "").strip()
    if not number or not street:
        return None, "no street address"

    # OpenAddresses usually carries the state in `region`. When it does, trust it
    # over the command line: it is the one cheap guard against filing a source
    # under the wrong --state, which no coordinate check would catch.
    region = str(properties.get("region") or "").strip().upper()
    if region and region != args.state:
        return None, f"state is {region}, not {args.state}"

    city = str(properties.get("city") or "").strip() or (args.city or "")
    city = getattr(args, "city_map", {}).get(city.upper()) or titlecase(city)
    if not city:
        if not args.allow_missing_city:
            return None, "no city"
    elif not any(character.isalpha() for character in city):
        # Sources carry the occasional corrupt row whose city is punctuation.
        return None, "no city"

    match = POSTCODE.match(str(properties.get("postcode") or "").strip())
    if not match:
        return None, "bad postal code"

    coordinates = (feature.get("geometry") or {}).get("coordinates")
    if not _valid_coordinates(coordinates):
        return None, "bad coordinates"

    lng, lat = float(coordinates[0]), float(coordinates[1])
    return {
        "address1": f"{number} {normalize_street(street)}",
        "address2": str(properties.get("unit") or "").strip(),
        "city": city,
        "state": args.state,
        "postal_code": match.group(1),
        "coordinates": {"lat": lat, "lng": lng},
    }, ""


def titlecase(text: str) -> str:
    """Capitalize each word, leaving designators and initialisms alone.

    Not ``str.title()``, which mangles apostrophes: ``"CHRISSY'S".title()`` gives
    ``"Chrissy'S"``. Hyphenated names are capitalized on both sides, so
    ``WINSTON-SALEM`` becomes ``Winston-Salem``.
    """
    words = []
    for word in text.split():
        preserved = _preserved(word)
        if preserved is not None:
            words.append(preserved)
            continue
        words.append("-".join(_capitalize(part) for part in word.split("-")))
    return " ".join(words)


def _preserved(word: str) -> str | None:
    """Return the word as it should stand, or None to capitalize it normally.

    Street names are full of tokens that must not be title-cased. These are all
    real entries in the dataset:

        U.S. 5, U.S.A       an initialism
        A1A, Vermont 5A     a route designator
        WB&A Road           the Washington, Baltimore and Annapolis railroad
        William E Summers III   a Roman numeral
        93RD Avenue         an ordinal, which does need lower-casing

    Ordinals are checked first, since they are the one alphanumeric token that
    should be reshaped rather than preserved.
    """
    if word.upper() in ROUTE_PREFIXES or word.upper() in ROMAN_NUMERALS:
        return word.upper()

    ordinal = ORDINAL.match(word)
    if ordinal:
        return ordinal.group(1) + ordinal.group(2).lower()

    letters = [character for character in word if character.isalpha()]
    if not letters or not all(letter.isupper() for letter in letters):
        return None

    # An all-caps token carrying a digit, a dot or an ampersand is a designator,
    # not a word. Apostrophes and hyphens do not count, or CHRISSY'S and
    # WINSTON-SALEM would never be capitalized.
    if any(character.isdigit() or character in ".&" for character in word):
        return word

    return None


def _capitalize(word: str) -> str:
    """Capitalize one word, respecting name particles and existing mixed case.

    A word that is already mixed case is left exactly as it is, so ``MacArthur``
    and ``McKee`` survive a second pass untouched. Only all-upper or all-lower
    words are reshaped, since those carry no capitalization to preserve.

    ``Mc`` and single-letter particles (``O'Neal``, ``D'Angelo``) get their next
    letter capitalized. ``Mac`` deliberately does not: a blanket rule would turn
    ``MACON`` into ``MacOn`` and ``MACHADO`` into ``MacHado``, which is worse than
    leaving ``MACARTHUR`` as ``Macarthur``.
    """
    if not word:
        return word
    if not word.isupper() and not word.islower():
        return word

    capitalized = word[0].upper() + word[1:].lower()

    if len(capitalized) > 2 and capitalized.startswith("Mc"):
        return "Mc" + capitalized[2].upper() + capitalized[3:]

    particle, apostrophe, rest = capitalized.partition("'")
    if apostrophe and len(particle) == 1 and rest:
        return f"{particle}'{rest[0].upper()}{rest[1:]}"

    return capitalized


def normalize_street(street: str) -> str:
    """Title-case a street and spell out its abbreviations.

    ``HERON CT SW`` becomes ``Heron Court Southwest``.

    A suffix is only expanded in the suffix position, that is, the last token or
    the one before a trailing directional. Expanding abbreviations anywhere would
    turn ``ST JOHNS RD`` into ``Street Johns Road``, because there ``ST`` is
    Saint, not Street.
    """
    tokens = street.split()
    if not tokens:
        return ""

    suffix_at = len(tokens) - 1
    if len(tokens) > 1 and tokens[-1].upper() in DIRECTIONALS:
        tokens[-1] = DIRECTIONALS[tokens[-1].upper()]
        suffix_at -= 1

    if suffix_at > 0 and tokens[suffix_at].upper() in STREET_SUFFIXES:
        tokens[suffix_at] = STREET_SUFFIXES[tokens[suffix_at].upper()]

    # A leading directional is only a directional when a street name follows it.
    # Washington DC has streets actually named S and E, so "S Street" is S Street,
    # not South Street, while "N Main St" really is North Main Street. The tell is
    # whether the next token is the suffix.
    if (
        len(tokens) > 2
        and tokens[0].upper() in DIRECTIONALS
        and tokens[1].upper() not in SUFFIX_WORDS
    ):
        tokens[0] = DIRECTIONALS[tokens[0].upper()]

    return titlecase(" ".join(tokens))


def _valid_coordinates(coordinates: Any) -> TypeGuard[Sequence[float]]:
    # A TypeGuard rather than a bool: the caller indexes the coordinates right
    # after this returns true, and only the guard establishes that it may.
    if not isinstance(coordinates, (list, tuple)) or len(coordinates) < 2:
        return False
    try:
        lng, lat = float(coordinates[0]), float(coordinates[1])
    except (TypeError, ValueError):
        return False
    if lat != lat or lng != lng:  # NaN
        return False
    return MIN_LAT <= lat <= MAX_LAT and MIN_LNG <= lng <= MAX_LNG


def _key(address: dict[str, Any]) -> tuple[str, str, str, str]:
    """Identify an address for duplicate detection.

    address2 is part of the key: two apartments in one building share a street
    address but are different addresses. Leaving it out collapsed them, and in
    the Durham source that would have discarded 5,057 distinct units while
    reporting them as duplicates.
    """
    return (
        address["state"].upper(),
        address["postal_code"],
        address["address1"].casefold(),
        address["address2"].casefold(),
    )


def _sort_key(address: dict[str, Any]) -> tuple[str, ...]:
    return (
        address["state"],
        address["city"],
        address["postal_code"],
        address["address1"],
        address["address2"],
    )


def _read_dataset() -> list[dict[str, Any]]:
    with DATASET.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _write_dataset(addresses: list[dict[str, Any]]) -> None:
    with DATASET.open("w", encoding="utf-8") as handle:
        for address in addresses:
            handle.write(json.dumps(address) + "\n")


def _city_list(value: str) -> list[str]:
    return [city.strip() for city in value.split(",") if city.strip()]


def _city_map(value: str) -> dict[str, str]:
    mapping = {}
    for pair in value.split(","):
        if not pair.strip():
            continue
        code, _, name = pair.partition("=")
        if not code.strip() or not name.strip():
            raise argparse.ArgumentTypeError(f"expected CODE=Name, got {pair.strip()!r}")
        mapping[code.strip().upper()] = name.strip()
    return mapping


def _balanced_sample(
    candidates: list[dict[str, Any]],
    cities: list[str],
    count: int,
    generator: random.Random,
) -> list[dict[str, Any]]:
    """Sample ``count`` addresses split as evenly as possible across ``cities``."""
    pools: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for address in candidates:
        pools[address["city"].casefold()].append(address)

    wanted: dict[str, list[dict[str, Any]]] = {}
    for city in cities:
        pool = pools.get(city.casefold())
        if pool:
            wanted[pool[0]["city"]] = pool
        else:
            print(f"Warning: no usable addresses found for {city!r}", file=sys.stderr)

    if not wanted:
        return []

    quotas = _allocate(count, {city: len(pool) for city, pool in wanted.items()})
    if sum(quotas.values()) < count:
        print(
            f"Warning: only {sum(quotas.values())} addresses available across "
            f"{len(wanted)} cities, asked for {count}"
        )

    selected: list[dict[str, Any]] = []
    for city, quota in quotas.items():
        selected.extend(generator.sample(wanted[city], quota))
    return selected


def _allocate(total: int, capacity: dict[str, int]) -> dict[str, int]:
    """Split ``total`` across the keys of ``capacity``, as evenly as each allows.

    A city that cannot supply its even share does not cost the sample its size:
    the shortfall is handed to the cities that still have addresses left. Asking
    for 50 across five cities where one holds only 3 gives 3 + 12 + 12 + 12 + 11,
    not 3 + 10 + 10 + 10 + 10.
    """
    quotas = dict.fromkeys(capacity, 0)
    remaining = min(total, sum(capacity.values()))

    while remaining > 0:
        open_cities = [city for city in capacity if quotas[city] < capacity[city]]
        if not open_cities:
            break

        share, extra = divmod(remaining, len(open_cities))
        if share == 0:
            # Fewer left to hand out than there are cities: one each, in order.
            for city in open_cities[:extra]:
                quotas[city] += 1
            break

        for city in open_cities:
            taken = min(share, capacity[city] - quotas[city])
            quotas[city] += taken
            remaining -= taken

    return quotas


def _report_by_city(selected: list[dict[str, Any]]) -> None:
    counts = Counter(address["city"] for address in selected)
    width = max(len(city) for city in counts)
    for city, total in sorted(counts.items()):
        print(f"  {city:<{width}}  {total}")


def _explain_wholesale_rejection(rejected: Counter[str]) -> None:
    """Point at the source when it is the source, not the records, that is wrong.

    Plenty of OpenAddresses sources publish no postal codes at all. Reading
    "123132 bad postal code" and concluding the tool is broken is the obvious
    mistake to make, so say what is actually going on.
    """
    if not rejected:
        return

    reason, total = rejected.most_common(1)[0]
    if total < sum(rejected.values()) * 0.9:
        return

    if reason == "bad postal code":
        print(
            "\nEvery record was rejected for the same reason: this source publishes "
            "no postal codes.\nThat is a property of the source, not of the data in "
            "it. Pick an OpenAddresses source\nwhose conform declares `postcode`; "
            "for a whole state, the `statewide` source usually does.",
            file=sys.stderr,
        )
    elif reason == "no city":
        print(
            "\nEvery record was rejected for the same reason: this source publishes "
            "no city.\nPass --city to supply one for the whole file.",
            file=sys.stderr,
        )


def _report(rejected: Counter[str]) -> None:
    if not rejected:
        return
    print("Rejected:")
    for reason, total in rejected.most_common():
        print(f"  {total:>6}  {reason}")


if __name__ == "__main__":
    raise SystemExit(main())
