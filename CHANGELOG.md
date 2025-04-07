# Changelog

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

[1.3.0]: https://github.com/neosergio/random-address/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/neosergio/random-address/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/neosergio/random-address/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/neosergio/random-address/compare/v0.1.2...v1.1.1
[1.0.0]: https://github.com/neosergio/random-address/compare/v0.1.2...v1.0.0
[0.1.2]: https://github.com/neosergio/random-address/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/neosergio/random-address/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/neosergio/random-address/compare/v0.0.11...v0.1.0
[0.0.11]: https://github.com/neosergio/random-address/releases/tag/v0.0.11