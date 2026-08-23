# Random Address

This is a tool to retrieve a real address from a list of real, random US addresses. It is meant for testing: seeding fixtures, exercising address forms, and giving geolocation code something genuine to work with.

The address data comes from the [OpenAddresses](https://openaddresses.io/) project, which collects address data published by national, state and local governments. Every address ships with the latitude and longitude given by that authoritative source, so each one resolves to a real point on the map without a geocoding round trip. All of the addresses are in the public domain, and they are deliberately not linked to people or businesses.

The addresses were pulled from OpenAddresses where the "Required attribute" field was present and not "Yes". See "Attribution" below for a list of sources.

This project was inspired by [Real, Random Address Data (RRAD)](https://github.com/EthanRBrown/rrad) project.

![PyPI](https://img.shields.io/pypi/v/random-address)
![PyPI - License](https://img.shields.io/pypi/l/random-address)
![PyPI - Downloads](https://img.shields.io/pypi/dm/random-address)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/random-address)
![PyPI - Status](https://img.shields.io/pypi/status/random-address)
[![PyPI Total Downloads](https://static.pepy.tech/personalized-badge/random-address?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=total-downloads)](https://pepy.tech/projects/random-address)


## Installation

Run the following to install:

```bash
$ pip install random-address
```

Requires Python 3.10 or newer.

## Usage

```python
>>> from random_address import real_random_address
>>> real_random_address()
{'address1': '210 Beachcomber Drive', 'address2': '', 'city': 'Pismo Beach', 'state': 'CA',
 'postal_code': '93449', 'coordinates': {'lat': 35.169193, 'lng': -120.694434}}
```

Filters combine, so you can narrow by any mix of state, city and postal code. State codes and
city names are matched case-insensitively.

```python
>>> real_random_address(state='CA')
>>> real_random_address(city='Newark')
>>> real_random_address(postal_code='32409')
>>> real_random_address(state='CA', city='Newark')
```

If nothing matches, a `NoMatchingAddressError` is raised rather than an empty dictionary being
returned, so a typo in a filter fails loudly:

```python
>>> real_random_address(state='ZZ')
NoMatchingAddressError: No address matches state='ZZ'
```

### Reproducible fixtures

Pass a `seed` to get the same address every time. The seed drives a private generator, so it
never disturbs the global `random` stream the rest of your process draws from.

```python
>>> real_random_address(seed=42) == real_random_address(seed=42)
True
```

### Several addresses at once

```python
>>> from random_address import real_random_addresses
>>> real_random_addresses(5, state='FL', seed=42)
[{...}, {...}, {...}, {...}, {...}]
```

Results are distinct by default. Pass `unique=False` to sample with replacement when you want
more addresses than the filters can supply.

### Inspecting the dataset

```python
>>> import random_address
>>> random_address.list_states()
['AK', 'AL', 'AR', 'AZ', 'CA', ...]
>>> random_address.state_counts()
{'AK': 174, 'AL': 193, 'AR': 190, 'AZ': 199, 'CA': 331, ...}
>>> random_address.summary()
{'total_addresses': 3400, 'unique_states': 20, 'unique_cities': 437, 'unique_postal_codes': 746}
```

`list_cities()`, `list_postal_codes()`, `city_counts()` and `postal_code_counts()` work the
same way.

### Counting matches

`count()` answers how many addresses match, without drawing one. It takes the same `state`,
`city` and `postal_code` filters as `real_random_address()`, and they combine the same way.

```python
>>> import random_address

>>> random_address.count()
3400
>>> random_address.count(state='CA')
331
>>> random_address.count(city='Arlington')
52
>>> random_address.count(postal_code='22204')
13
>>> random_address.count(state='TX', city='Houston')
10
```

Filters combine, which is how you tell two places of the same name apart. Fifty of those
Arlingtons are in Virginia and two are in Massachusetts:

```python
>>> random_address.count(state='VA', city='Arlington')
50
>>> random_address.count(state='MA', city='Arlington')
2
```

Where the lookup functions raise `NoMatchingAddressError`, `count()` returns `0` — asking how
many there are is a question that a zero answers:

```python
>>> random_address.count(state='ZZ')
0
```

It is the honest way to size a fixture before asking for one, since
`real_random_addresses(n, unique=True)` raises when `n` exceeds the number of matches:

```python
>>> total = random_address.count(state='OR')
>>> len(random_address.real_random_addresses(total, state='OR'))
50
```

## Command line

```bash
$ random-address
1233 Paradise Lane, Fayetteville, AR 72701

$ random-address --state CA --count 2 --format json
$ random-address --state FL --count 50 --format csv > fixtures.csv
$ random-address states
$ random-address summary
```

## Functions Overview

- `real_random_address(*, state=None, city=None, postal_code=None, seed=None)`: one address, optionally filtered.
- `real_random_addresses(count=1, *, state=None, city=None, postal_code=None, seed=None, unique=True)`: several addresses.
- `count(*, state=None, city=None, postal_code=None)`: how many addresses match, `0` if none do.
- `list_states()`, `list_cities()`, `list_postal_codes()`: the values present in the dataset.
- `state_counts()`, `city_counts()`, `postal_code_counts()`: how many addresses each value has.
- `summary()`: dataset-wide totals.

The package ships type information (`py.typed`), so `Address` and `Coordinates` are available
to type checkers and editors.

## Upgrading from 1.x

Version 2.0 replaced the four `real_random_address_by_*` functions with filter arguments and
renamed the `postalCode` key to `postal_code`.

| 1.x | 2.0 |
| --- | --- |
| `real_random_address_by_state('CA')` | `real_random_address(state='CA')` |
| `real_random_address_by_city('Newark')` | `real_random_address(city='Newark')` |
| `real_random_address_by_postal_code('32409')` | `real_random_address(postal_code='32409')` |
| `list_available_states()` | `list_states()` |
| `list_available_cities()` | `list_cities()` |
| `list_available_postal_codes()` | `list_postal_codes()` |
| `list_states_with_counts()` | `state_counts()` |
| `list_cities_with_counts()` | `city_counts()` |
| `list_postal_codes_with_counts()` | `postal_code_counts()` |
| `get_summary()` | `summary()` |
| `address['postalCode']` | `address['postal_code']` |
| an empty `{}` when nothing matched | `NoMatchingAddressError` |

## Attribution

All data collected from the [OpenAddresses](https://openaddresses.io/) project, and is in the public domain.  Original sources:

* City of Haddam (CT)
* Ciy of Hartford (CT)
* City of Lyme (CT)
* City of Manchester (CT)
* City of Watertown (CT)
* City of Avon (CT)
* Town of Fairfield (CT)
* City of Groton (CT)
* Office of Geographic Information (MassGIS), Commonwealth of Massachusetts, MassIT (MA)
* VT Enhanced 911 Board, VCGI (VT)
* City of Huntsville (AL)
* City of Montgomery (AL)
* Shelby County (AL)
* Talladega County (AL)
* City of Fayetteville (AR)
* Arkansas Geographic Information Office (AR)
* City of Washington (DC)
* Bay County (FL)
* Brevard County (FL)
* Charlotte County (FL)
* Citrus County (FL)
* Clay County (FL)
* Highlands County, FL (FL)
* Hillsborough County (FL)
* City of Savannah (GA)
* Gordon County (GA)
* Muscogee County (GA)
* Sumter County (GA)
* Metro Louisville,  LOJIC partners (KY)
* Anne Arundel County (MD)
* City of Baltimore (MD)
* Frederick County (MD)
* Oklahoma and Logan Counties - Association of Central Oklahoma Governments (OK)
* Kern, Cleveland, Canadian, Logan Counties (OK)
* City of Nashville (TN)
* Cooke,Fannin,Grayson Counties - Texoma Council of Governments (TX)
* Municipality of Anchorage (AK)
* Copyright © 2015 Kenai Peninsula Borough (AK)
* Matanuska-Susitna Borough (AK)
* City of Glendale (AZ)
* City of Mesa (AZ)
* Alameda County (CA)
* Amador County (CA)
* City of Berkeley (CA)
* Butte County (CA)
* City of Bakersfield (CA)
* City of Carson (CA)
* City of Cupertino (CA)
* City of Hayward and Fairview. Licensed for Public Use (CA)
* City of Mountain View (CA)
* City of Orange (CA)
* Contra Costa County (CA)
* El Dorando County (CA)
* Fresno County (CA)
* Humboldt County (CA)
* Kern County (CA)
* Kings County (CA)
* Lake County (CA)
* Lassen County (CA)
* Los Angeles County (CA)
* Madera County (CA)
* Marin County (CA)
* Merced County (CA)
* Mono County (CA)
* Monterey County (CA)
* Napa County (CA)
* County of Nevada, California (CA)
* Orange County (CA)
* City of Palo Alto (CA)
* County of Placer (CA)
* Secramento County (CA)
* San Bernardino County (CA)
* San Diego Geographic Information Source - JPA (CA)
* San Joaquin County (CA)
* San Luis Obispo County (CA)
* San Mateo County (CA)
* Santa Barbara County (CA)
* Santa Clara County (CA)
* Santa Cruz County (CA)
* Shasta County (CA)
* Solano County (CA)
* Sonoma County (CA)
* Stanislaus County (CA)
* Tuolumne County (CA)
* Yolo County (CA)
* Yuba County (CA)
* Arapahoe County (CO)
* Archuleta County (CO)
* City of Arvada (CO)
* City of Aurora (CO)
* City of Boulder (CO)
* City of Fort Collins (CO)
* City of Greeley (CO)
* City of Loveland (CO)
* City of Westminster (CO)
* Gilpin County (CO)
* Gunnison County (CO)
* Jefferson County (CO)
* Larimer County (CO)
* Mesa County (CO)
* Pitkin County (CO)
* Pubelo County (CO)
* San Miguel County (CO)
* City of Honolulu (HI)
* Arlington County (VA)
* Durham County (NC)
* City of Portland (OR)
* Texas Natural Resources Information System, StratMap Address Points (TX)

## Requesting New Location Data

If you need addresses for a specific **city**, **state**, or **postal code** that is not yet included in the dataset, please open a new [GitHub Issue](https://github.com/neosergio/random-address/issues) describing your request.

Requests will be evaluated and added **gradually**, in order to:

- Keep the library size small and lightweight.
- Ensure quality and functionality remain stable across versions.

We appreciate your suggestions and contributions!

### Can you add addresses for my country?

**If [OpenAddresses](https://openaddresses.io/) covers it, it can be considered. If it does not,
the answer is no**, and the reason is worth explaining.

Every address here is real, published by a government, and in the public domain. That is the only
thing this library promises, and it is what makes the addresses geocode. OpenAddresses is the
project that collects that data, so its coverage is the ceiling on what can be added here. You can
check a country yourself by looking for its two-letter code under
[`sources/`](https://github.com/openaddresses/openaddresses/tree/master/sources) — 67 countries are
covered, including `us`, `jp`, `de` and `br`. Much of Southeast Asia, Africa and South Asia is not,
because those governments do not publish open address data.

OpenStreetMap is not an alternative. It is licensed under ODbL, which is share-alike, and mixing it
in would break the public-domain guarantee for everyone downstream.

Note that the dataset is US-only today: `state` is a two-letter code and coordinates are validated
against a US bounding box. Adding the first non-US country therefore means a schema change, with a
`country` field and a region concept that is not a US state. That is a real conversation to have,
but it needs the data to exist first.

**If you need addresses that merely look plausible rather than addresses that are real**, use
[Faker](https://faker.readthedocs.io/) instead — `Faker("id_ID").address()` and its many other
locales generate correctly formatted addresses for most countries. Faker's addresses are invented;
this library's are not. Pick whichever your test actually needs.

### Adding the addresses

Maintainers fulfil a request by sampling from the matching [OpenAddresses](https://openaddresses.io/)
GeoJSON file:

```bash
$ python data/add_addresses.py nc.geojson --state NC --count 50 --seed 7 \
    --cities "Charlotte,Raleigh,Durham,Asheville,Wilmington"
Selected 50 addresses for NC
  Asheville   3
  Charlotte   12
  Durham      12
  Raleigh     12
  Wilmington  11

Wrote 3300 addresses to src/random_address/data/addresses-us.jsonl
```

`--cities` splits the count evenly between the cities you name, which is how a statewide source
is turned into a handful of recognizable cities rather than fifty scattered rural rows. A city
that cannot supply its share does not shrink the sample: above, Asheville only had three usable
addresses, and the other four cities absorbed the shortfall. Without `--cities`, the sample is
drawn from the whole file.

Records are validated before being sampled, so a run yields the number of usable addresses you
asked for. A record is rejected when it has no street number or street, no city (pass `--city`
to supply one for sources that omit it, as some do), a malformed postal code, coordinates
outside the US, or a `region` that disagrees with `--state`. Records already in the dataset are
skipped as duplicates, so re-running a source is safe.

Sources vary. Many publish ALL CAPS, abbreviated data, so `212 HERON CT SW` in `BOLIVIA` is
normalized to `212 Heron Court Southwest` in `Bolivia` on the way in. Many publish no postal
code at all, in which case every record is rejected and you need a different source; the
`statewide` source for a state usually carries one.

Use `--dry-run` to preview, and `--replace-state` to re-import a state from a better source.

Because the dataset is one address per line, sorted, a request like this lands as a reviewable
diff of 50 added lines. Please credit the source under Attribution when you add data.


## Contributing

Contributions are welcome! Feel free to submit pull requests, report issues, or suggest improvements.

# Developing Random Address

To install random-address along with the tools needed to develop and run tests, run the
following in your virtualenv:

```bash
$ pip install -e ".[dev]"
```

Then:

```bash
$ pytest              # run the tests
$ ruff check .        # lint
$ ruff format .       # format
```
