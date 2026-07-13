# Changelog

## [2.1.0] - 2026-07-12

A dataset release. The library's API is unchanged, but the data it ships has been cleaned up and
the way it is stored has changed so that contributed data can actually be reviewed.

### Changed
- The dataset is stored as JSON Lines (`addresses-us.jsonl`), one address per line, sorted by state, city, postal code and street. The previous file was a single 513 KB line, so adding addresses for a requested city produced a diff nobody could review. Adding 50 addresses is now a 50-line diff. Parsing costs about 3 ms more once per process; repeat lookups are unaffected.

### Removed
- Twenty records that had no city at all (17 VT, plus one each in CA, MD and TN). They shipped in 2.0.0 with a blank `city`; they are now gone, so `city` can be relied on to be non-empty. **Nine postal codes went with them**, having existed only in those records. If you were looking up one of those postal codes, it now raises `NoMatchingAddressError`.
- `data/convert_to_all.py` and `data/convert_to_min.py`. They existed to keep a pretty file and a minified file in sync; with JSON Lines the file that ships is the file that is edited, so there is nothing to sync.
- `data/convert_address_from_geojson.py`, replaced by `data/add_addresses.py`.

### Added
- North Carolina, in response to a request for more NC cities: 50 addresses spread evenly across Durham, Chapel Hill, Morrisville, Raleigh and Hillsborough, from Durham County's address data. The dataset now holds 3,300 addresses across 18 states.
- `data/add_addresses.py`, a maintainer command for fulfilling data requests from GitHub issues. It samples an OpenAddresses GeoJSON file, taking the state, city, count and seed as arguments rather than hardcoding them. Records are validated before they are sampled, so a run yields the number of usable addresses asked for; anything with no street or city, a malformed postal code, coordinates outside the US, or a `region` that disagrees with `--state` is rejected and reported. Duplicates are skipped, so a source can be re-run safely. Supports `--dry-run` and `--replace-state`.
- Integrity tests over the dataset itself, run in CI on every pull request, so malformed contributed data fails on GitHub rather than in a user's test suite. They check the record shape, the state and postal code formats, coordinate bounds, the absence of duplicates, and that the file stays one sorted record per line.

### Fixed
- The ingest normalizer no longer corrupts street names it should leave alone. `S Street` and `E Street` in Washington DC are streets named after letters, not directions, and were being turned into `South Street`; `Highway A1A`, `Vermont 5A`, `WB&A Road`, `U.S. 5` and `William E Summers III Avenue` were all mangled by title-casing. `MCCRORY` and `O'NEALS` now become `McCrory` and `O'Neals` rather than `Mccrory` and `O'neals`, and an already mixed-case name such as `MacArthur` survives a second pass untouched. An integrity test now asserts that re-normalizing the whole dataset changes nothing, which catches both an un-normalized record and a normalizer that damages good data.
- The ingest script's duplicate key now includes `address2`. Two apartments in one building share a street address but are different addresses; without the unit in the key they collapsed into one, and in the Durham source that would have discarded 5,057 distinct units while reporting them as duplicates.
- Writing the dataset from a directory outside the repository no longer replaces the "Wrote N addresses" confirmation with a traceback from `Path.relative_to`, on a run that had in fact succeeded.
- Spelled out street abbreviations in 52 records that predate the ingest script. 50 Arlington addresses shipped as `1172 N VERMONT ST` and are now `1172 North Vermont Street`; `2A Cleveland Park Rd` and `1211 Rock Creek Trce` were also left abbreviated. Genuine highway names such as `4221 U.S. 5` are untouched. An integrity test now fails if an address ends in an unexpanded abbreviation.
- The workflows no longer run with the default, broadly-scoped `GITHUB_TOKEN`. They ask for `contents: read`, and the publish jobs re-grant `id-token: write` for Trusted Publishing. Checkouts no longer persist the token into `.git/config`.

### Documentation
- Reworded the claim that the addresses "geocode successfully (tested on Google's Geocoding API service)". Addresses added from now on are not run through Google, so that claim would decay as the dataset grows. What is true of every record, by construction, is that OpenAddresses ships it with the coordinates published by the government source, so it resolves to a real point on the map without a geocoding call. The README, the package description and the docstrings now say that instead.

## [2.0.0] - 2026-07-12

This is a breaking release. See "Upgrading from 1.x" in the README for the full mapping from
the old function names to the new ones.

### Changed
- **The four `real_random_address_by_*` functions are now filter arguments.** `real_random_address(state='CA', city='Newark')` combines filters, which was not previously possible. State codes and city names now match case-insensitively, and surrounding whitespace is ignored.
- **The `postalCode` key on returned addresses is now `postal_code`.**
- **No match now raises `NoMatchingAddressError` instead of returning an empty dict.** A falsy `{}` made typos such as `state='Ca'` fail silently.
- Dataset introspection functions were renamed: `list_available_states` to `list_states`, `list_states_with_counts` to `state_counts`, `get_summary` to `summary`, and so on for cities and postal codes.
- Seeding: results are now drawn from a generator private to this package. Seeding the global `random` module no longer changes what these functions return; pass `seed=` instead.
- Minimum supported Python is now 3.10.

### Added
- `real_random_addresses(count)` returns several addresses at once, distinct by default, with `unique=False` to sample with replacement.
- A `seed` argument on both lookup functions makes fixtures reproducible without touching the global random state.
- A `random-address` command line interface, with `--state`, `--city`, `--postal-code`, `--count`, `--seed` and `--format text|json|csv`, plus `states`, `cities`, `postal-codes` and `summary` subcommands.
- Type information is now shipped (`py.typed`), exposing the `Address`, `Coordinates` and `Summary` types to type checkers and editors.

### Fixed
- `real_random_address()` raised `IndexError` on an empty dataset despite documenting that it returned `{}`. It now raises `NoMatchingAddressError`, consistently with every other lookup.
- The package no longer re-exports the standard library. A bare `from .random_address import *` had been leaking `os`, `sys`, `json`, `random`, `logging` and `Counter` as public attributes of `random_address`.
- The dataset is read from disk and indexed once per process instead of being re-parsed on every single call. A thousand filtered lookups went from roughly 3.4 seconds to under 2 milliseconds.
- Addresses are loaded through `importlib.resources` rather than by deriving a path from `sys.modules`, which failed for zipped and frozen installs.
- Every record in the dataset now has the same six keys. Twenty records were missing `city` entirely; their city is an empty string. They remain reachable by state and postal code, and are left out of the city listings. (Removed altogether in 2.1.0.)

### Removed
- Travis CI, `tox.ini`, `setup.py`, `setup.cfg` and `MANIFEST.in`, replaced by a PEP 621 `pyproject.toml`, ruff, and GitHub Actions for testing (Python 3.10 to 3.14) and for publishing to PyPI via Trusted Publishing.

## [1.3.0] - 2025-04-07
### Added
- Added functions `list_available_states`, `list_available_postal_codes`, and `list_available_cities` to explore dataset content.
- Added functions `list_states_with_counts`, `list_postal_codes_with_counts`, and `list_cities_with_counts` to get frequency distributions.
- Added function `get_summary` to retrieve dataset-wide stats like total addresses, and number of unique states, cities, and postal codes.

## [1.2.1] - 2025-03-31
### Added
- Added addresses dataset for Arlington County, Virginia (VA).
- Script added to randomly select and transform addresses from geojson dataset to desired JSON format.
- Script added to convert `addresses-us-all.json` to its minified version `addresses-us-all.min.json`.

### Fixed
- GitHub Actions workflows updated to fix compatibility issues with Python 3.10 and later.
- Fixed pylint warnings related to encoding specification when opening files and lazy formatting for logging messages.
- Fixed pytest import error by installing the package in editable mode within GitHub Actions workflow.

## [1.2.0] - 2025-03-29
### Added
- New function `real_random_address_by_city` to retrieve addresses filtered by city name.
- Improved documentation and examples in Google-style docstrings for all functions.
- Explicit support for Python versions 3.10, 3.11, 3.12, and 3.13 added to classifiers and `python_requires`.

### Fixed
- Bug fix: Handled cases where city name might be missing in JSON data to prevent AttributeError when calling `.lower()`.
- Enhanced test suite by adding more robust assertions and new test cases for validating returned address fields.

## [1.1.1] - 2021-05-27
### Added
- New function real_random_address_by_state to get results filtered by state code (two characters format. i,e CA, FL).
- New function real_random_address_by_postal_code to get results filtered by postal code

## [1.0.0] - 2021-05-24
### Changed
- Classifier about development status to stable
- Shield in README about code maintainability

## [0.1.2] - 2021-05-23
### Added
- GitHub Actions implemented in commit changes flow.
- TravisCI integration for test building process.

### Fixed
- Fix comments and implementation of reading source json file to pass lint checks.

## [0.1.1] - 2021-05-23
### Added
- Classifiers in setup, in order to improve documentation in pypi.org site.

## [0.1.0] - 2021-05-22
### Added
- Helpful information about project and example of expected value in README.

## [0.0.11] - 2021-05-19
### Added
- First public preview release.

[2.1.0]: https://github.com/neosergio/random-address/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/neosergio/random-address/compare/v1.3.0...v2.0.0
[1.3.0]: https://github.com/neosergio/random-address/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/neosergio/random-address/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/neosergio/random-address/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/neosergio/random-address/compare/v0.1.2...v1.1.1
[1.0.0]: https://github.com/neosergio/random-address/compare/v0.1.2...v1.0.0
[0.1.2]: https://github.com/neosergio/random-address/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/neosergio/random-address/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/neosergio/random-address/compare/v0.0.11...v0.1.0
[0.0.11]: https://github.com/neosergio/random-address/releases/tag/v0.0.11