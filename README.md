# Random Address

This is a tool to retrieve a real address from a list of real of random addresses that geocode successfully (tested on Google's Geocoding API service). The address data comes from the OpenAddresses project, and all the addresses are in the public domain. The addresses are deliberately not linked to people or businesses; the only guarantee is that they are real addresses that geocode successfully.

The addresses were pulled from OpenAddress where the "Required attribute" field was present and not "Yes". See "Attribution" below for a list of sources (also included in each data file).

This project was inspired by [Real, Random Address Data (RRAD)](https://github.com/EthanRBrown/rrad) project.

![Travis (.com)](https://img.shields.io/travis/com/neosergio/random-address)
![PyPI](https://img.shields.io/pypi/v/random-address)
![PyPI - License](https://img.shields.io/pypi/l/random-address)
![PyPI - Downloads](https://img.shields.io/pypi/dm/random-address)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/random-address)
![PyPI - Status](https://img.shields.io/pypi/status/random-address)


## Installation

Run the following to install:

```bash
$ pip install random-address
```

## Usage

```python
from random_address import real_random_address

# Generate a dictionary with valid random address information
real_random_address()
```

There are other 3 functions that can be used:
```python
>>> import random_address
>>> random_address.real_random_address_by_state('CA')
{'address1': '37600 Sycamore Street', 'address2': '', 'city': 'Newark', 'state': 'CA', 'postalCode': '94560', 'coordinates': {'lat': 37.5261943, 'lng': -122.0304698}}
>>> random_address.real_random_address_by_postal_code('32409')
{'address1': '711 Tashanna Lane', 'address2': '', 'city': 'Southport', 'state': 'FL', 'postalCode': '32409', 'coordinates': {'lat': 30.41437699999999, 'lng': -85.676568}}
>>> random_address.real_random_address_by_city('Newark')
{'address1': '37600 Sycamore Street', 'address2': '', 'city': 'Newark', 'state': 'CA', 'postalCode': '94560', 'coordinates': {'lat': 37.5261943, 'lng': -122.0304698}}
```

These functions allow you to inspect the dataset contents:
```python
>>> random_address.list_available_states()
['AK', 'CA', 'FL', 'VA', ...]

>>> random_address.list_available_postal_codes()
['32409', '93546', '94560', '99577', ...]

>>> random_address.list_available_cities()
['Mammoth Lakes', 'Newark', 'Panama City Beach', 'Southport', ...]

>>> random_address.list_states_with_counts()
{'CA': 1234, 'FL': 900, 'VA': 200, ...}

>>> random_address.list_postal_codes_with_counts()
{'32409': 10, '99577': 15, ...}

>>> random_address.list_cities_with_counts()
{'Panama City Beach': 6, 'Newark': 12, ...}

>>> random_address.get_summary()
{
    'total_addresses': 43873,
    'unique_states': 47,
    'unique_cities': 1300,
    'unique_postal_codes': 950
}
```

**Expected value example:**

```
{'address1': '210 Beachcomber Drive', 'address2': '', 'city': 'Pismo Beach', 'state': 'CA', 'postalCode': '93449', 'coordinates': {'lat': 35.169193, 'lng': -120.694434}}
```

## Functions Overview

- `real_random_address()`: Retrieve a random valid US address.
- `real_random_address_by_state(state: str)`: Retrieve a random address filtered by US state code.
- `real_random_address_by_postal_code(postal_code: str)`: Retrieve a random address filtered by US postal code.
- `real_random_address_by_city(city: str)`: Retrieve a random address filtered by US city.

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

## Requesting New Location Data

If you need addresses for a specific **city**, **state**, or **postal code** that is not yet included in the dataset, please open a new [GitHub Issue](https://github.com/neosergio/random-address/issues) describing your request.

Requests will be evaluated and added **gradually**, in order to:

- Keep the library size small and lightweight.
- Ensure quality and functionality remain stable across versions.

We appreciate your suggestions and contributions!


## Contributing

Contributions are welcome! Feel free to submit pull requests, report issues, or suggest improvements.

# Developing Random Address

To install random-address, along the tools you need to develop and run tests, run the following in your virtualenv:

```bash
$ pip install -e .[dev]
```
