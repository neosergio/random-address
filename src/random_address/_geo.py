"""Distance between points on the Earth, for the ``near`` and ``within_km`` filters.

The dataset is small enough that a radius filter is a scan over the candidates
the other filters left, measured with the haversine formula. There is no spatial
index to keep in sync with the data, and nothing is precomputed at build time.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from .types import Location

# The mean radius of the Earth (IUGG). Haversine treats the Earth as a sphere,
# which is off by at most about half a percent: plenty for "within 2 km".
EARTH_RADIUS_KM = 6371.0088

Point = tuple[float, float]


def point(location: Location) -> Point:
    """Reduce a location to a validated ``(lat, lng)`` pair.

    Accepts a ``(lat, lng)`` tuple, a :class:`~random_address.types.Coordinates`
    dictionary, or a whole :class:`~random_address.types.Address`, so the address
    returned by one call can be handed straight to the next as ``near``.

    Raises:
        ValueError: If the location has no usable latitude and longitude.
    """
    lat: object
    lng: object
    if isinstance(location, Mapping):
        coordinates = location.get("coordinates", location)
        if not isinstance(coordinates, Mapping):
            raise ValueError("near must have 'lat' and 'lng'")
        lat, lng = coordinates.get("lat"), coordinates.get("lng")
    elif isinstance(location, (tuple, list)) and len(location) == 2:
        lat, lng = location
    else:
        raise ValueError("near must be a (lat, lng) pair, a coordinates dict or an address")

    if isinstance(lat, bool) or isinstance(lng, bool):
        # bool is an int, so True would otherwise be accepted as latitude 1.
        raise ValueError("near must have numeric 'lat' and 'lng'")
    try:
        lat_value, lng_value = float(lat), float(lng)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise ValueError("near must have numeric 'lat' and 'lng'") from None

    if not -90.0 <= lat_value <= 90.0:
        raise ValueError(f"near latitude must be between -90 and 90, got {lat_value}")
    if not -180.0 <= lng_value <= 180.0:
        raise ValueError(f"near longitude must be between -180 and 180, got {lng_value}")
    return lat_value, lng_value


def distance_km(first: Point, second: Point) -> float:
    """Return the great-circle distance between two ``(lat, lng)`` points."""
    lat1, lng1 = map(math.radians, first)
    lat2, lng2 = map(math.radians, second)
    haversine = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    )
    # min() guards asin against a rounding error nudging the argument past 1.
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(haversine)))
