"""Generic coordinate reference system utilities."""

from __future__ import annotations

from numbers import Number
from typing import Iterable, Optional

import numpy as np
from pyproj import CRS, Transformer


def determine_is_projected(crs_input: Optional[str]) -> bool:
    """Return True when the CRS input appears to represent projected coordinates."""
    if crs_input is None:
        return False

    text = str(crs_input)
    try:
        crs_obj = CRS.from_user_input(text)
        return not bool(getattr(crs_obj, "is_geographic", False))
    except Exception:
        lower_text = text.lower()
        if any(token in lower_text for token in ("4326", "wgs84", "lonlat", "geog", "geographic")):
            return False
        if any(token in lower_text for token in ("3857", "mercator", "meter", "metre")):
            return True
        if "epsg" in lower_text:
            digits = "".join(character for character in lower_text if character.isdigit())
            if digits:
                try:
                    return int(digits) != 4326
                except Exception:
                    return True
        return False


def utm_crs_from_lonlat(lon: float, lat: float) -> CRS:
    """Build a UTM CRS from geographic coordinates."""
    zone = int((lon + 180.0) // 6.0) + 1
    epsg = (32600 if lat >= 0.0 else 32700) + zone
    return CRS.from_epsg(epsg)


def local_crs_from_lonlat(lon: float, lat: float) -> CRS:
    """Build a local azimuthal equidistant CRS centered at lon/lat."""
    return CRS.from_proj4(
        f"+proj=aeqd +lat_0={lat:.8f} +lon_0={lon:.8f} +x_0=0 +y_0=0 +units=m +no_defs"
    )


def to_local_coords(
    xs: Iterable[float] | np.ndarray,
    ys: Iterable[float] | np.ndarray,
    lon0: float,
    lat0: float,
) -> list[tuple[float, float]]:
    """Project lon/lat sequences to local metric coordinates relative to lon0/lat0."""
    if not isinstance(lon0, Number) or not isinstance(lat0, Number):
        raise ValueError("Origin coordinates must be numeric")

    utm = utm_crs_from_lonlat(float(lon0), float(lat0))
    to_utm = Transformer.from_crs("EPSG:4326", utm, always_xy=True)
    x0, y0 = to_utm.transform(float(lon0), float(lat0))
    x_values, y_values = to_utm.transform(xs, ys)
    return list(zip(np.asarray(x_values) - x0, np.asarray(y_values) - y0))
