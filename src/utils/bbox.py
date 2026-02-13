"""BBox utilities: BBox class to centralize bbox handling.

Provides a canonical object with attributes west/south/east/north and optional crs.
The constructor accepts the same inputs the previous helpers accepted: dicts with
multiple key variants, 4-item sequences, objects with `.total_bounds` or `.bounds`,
or another `BBox` instance.

Methods:
  - as_dict(): returns canonical dict {'west','south','east','north','crs'}
  - to_tuple(): (west, south, east, north)
  - to_geojson(): same as to_tuple()
  - to_shapely(): returns shapely.geometry.box (requires shapely)
  - reproject(to_crs): attempts to reproject bbox to another CRS (requires pyproj/geopandas)
"""
from typing import Any, Dict, Tuple, Optional
from numbers import Number

from utils.logger import get_logger, log_warning

logger = get_logger("bbox")


class BBox:
    """Bounding box helper class.

    Args:
        src: input bbox-like (dict, sequence of 4 numbers, object with .total_bounds/.bounds, or BBox)

    Raises:
        ValueError: for unsupported or invalid bbox inputs.
    """

    def __init__(self, src: Any) -> None:
        """
        Initialize a BBox instance from various bounding-box representations.
        Parameters
            Source used to construct the BBox. Supported input forms:
            - BBox instance: copies west, south, east, north and crs from the other instance.
            - dict: delegated to self._from_dict(data)-style construction.
            - list or tuple of 4 numbers: interpreted as (west, south, east, north).
            - GeoDataFrame-like object or any object with a `total_bounds` attribute
              (iterable of 4 elements): interpreted as (minx, miny, maxx, maxy).
              If the object has a `crs` attribute, its string representation is used for self.crs.
            - Object with a `bounds` attribute (list/tuple of 4 elements) or a shapely
              geometry exposing `bounds` as a 4-tuple: interpreted as (minx, miny, maxx, maxy).
              If the object has a `crs` attribute, its string representation is used for self.crs.
        Behavior
        --------
        - Coordinates are converted to float where applicable and assigned to self.west,
          self.south, self.east and self.north.
        - If a CRS is available from the source, self.crs is set to its string representation.
        - Validates the resulting box by calling self._validate() when appropriate.
        - For 4-element sequences, each element is checked to be numeric and convertible to float.
        Raises
        ------
            - If src is None.
            - If a 4-element sequence contains non-numeric values.
            - If the input format is not supported or cannot be parsed into a bounding box.
        """
        if src is None:
            raise ValueError("bbox is None")

        # If already a BBox, copy fields
        if isinstance(src, BBox):
            self.west = float(src.west)
            self.south = float(src.south)
            self.east = float(src.east)
            self.north = float(src.north)
            self.crs = src.crs
            # copy projected flag if available, otherwise determine
            self.is_projected = bool(getattr(src, "is_projected", False))
            return

        # dict-like
        if isinstance(src, dict):
            self._from_dict(src)
            return

        # sequence of 4 numbers
        if isinstance(src, (list, tuple)) and len(src) == 4:
            west, south, east, north = src
            if not all(isinstance(x, Number) for x in (west, south, east, north)):
                raise ValueError("BBox sequence elements must be numeric")
            self.west = float(west)
            self.south = float(south)
            self.east = float(east)
            self.north = float(north)
            self.crs = None
            self._validate()
            # no CRS -> assume geographic coordinates (degrees)
            self.is_projected = False
            return

        # GeoDataFrame-like: prefer total_bounds
        total_bounds = getattr(src, "total_bounds", None)
        if total_bounds is not None:
            try:
                minx, miny, maxx, maxy = total_bounds
                self.west = float(minx)
                self.south = float(miny)
                self.east = float(maxx)
                self.north = float(maxy)
                crs = getattr(src, "crs", None)
                self.crs = str(crs) if crs is not None else None
                self._validate()
                self.is_projected = self._determine_is_projected(self.crs)
                return
            except Exception:
                pass

        # object with .bounds
        bounds = getattr(src, "bounds", None)
        if bounds is not None and isinstance(bounds, (list, tuple)) and len(bounds) == 4:
            minx, miny, maxx, maxy = bounds
            self.west = float(minx)
            self.south = float(miny)
            self.east = float(maxx)
            self.north = float(maxy)
            crs = getattr(src, "crs", None)
            self.crs = str(crs) if crs is not None else None
            self._validate()
            self.is_projected = self._determine_is_projected(self.crs)
            return

        # shapely geometry may also expose .bounds (tuple)
        try:
            b = getattr(src, "bounds")
            if b and isinstance(b, tuple) and len(b) == 4:
                minx, miny, maxx, maxy = b
                self.west = float(minx)
                self.south = float(miny)
                self.east = float(maxx)
                self.north = float(maxy)
                crs = getattr(src, "crs", None)
                self.crs = str(crs) if crs is not None else None
                self._validate()
                self.is_projected = self._determine_is_projected(self.crs)
                return
        except Exception:
            pass

        raise ValueError("Unsupported bbox format. Provide dict, tuple/list (4), or object with .total_bounds/.bounds")

    def _from_dict(self, d: Dict[str, Any]) -> None:
        key_variants = [
            ("west", "south", "east", "north"),
            ("minx", "miny", "maxx", "maxy"),
            ("left", "bottom", "right", "top"),
        ]
        lower_keys = {str(k).lower(): v for k, v in d.items()}
        for keys in key_variants:
            if all(k in lower_keys for k in keys):
                self.west = float(lower_keys[keys[0]])
                self.south = float(lower_keys[keys[1]])
                self.east = float(lower_keys[keys[2]])
                self.north = float(lower_keys[keys[3]])
                self.crs = d.get("crs") if isinstance(d.get("crs"), str) else None
                self._validate()
                self.is_projected = self._determine_is_projected(self.crs)
                return
        raise ValueError("Dictionary bbox must contain keys like west/south/east/north or minx/miny/maxx/maxy")

    def _validate(self) -> None:
        if not all(isinstance(x, Number) for x in (self.west, self.south, self.east, self.north)):
            raise ValueError("BBox values must be numeric")
        if not (self.west < self.east and self.south < self.north):
            raise ValueError("Invalid bbox: require west < east and south < north")

    def _determine_is_projected(self, crs_input: Optional[str]) -> bool:
        """Determine whether the CRS indicates a projected (metric) CRS.

        Tries to use pyproj.CRS when available; otherwise falls back to simple
        heuristics (checks for EPSG:4326/WGS84/lonlat as geographic). If crs_input
        is None we assume geographic coordinates (not projected).
        """
        if crs_input is None:
            return False
        s = str(crs_input)
        try:
            from pyproj import CRS as _CRS  # type: ignore
            crs_obj = _CRS.from_user_input(s)
            # is_geographic == True means lon/lat
            return not bool(getattr(crs_obj, "is_geographic", False))
        except Exception:
            # fallback heuristics
            sl = s.lower()
            if "4326" in sl or "wgs84" in sl or "lonlat" in sl or "geog" in sl or "geographic" in sl:
                return False
            if "3857" in sl or "mercator" in sl or "meter" in sl or "metre" in sl:
                return True
            # if an EPSG code is present and not 4326, assume projected
            if "epsg" in sl:
                try:
                    num = int(''.join(ch for ch in sl if ch.isdigit()))
                    return num != 4326
                except Exception:
                    return True
            # conservative default: assume geographic
            return False

    def as_dict(self) -> Dict[str, Any]:
        return {"west": float(self.west), "south": float(self.south), "east": float(self.east), "north": float(self.north), "crs": self.crs, "is_projected": bool(getattr(self, "is_projected", False))}

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (float(self.west), float(self.south), float(self.east), float(self.north))

    def to_geojson(self) -> Tuple[float, float, float, float]:
        return self.to_tuple()

    def to_shapely(self):
        try:
            from shapely.geometry import box as shapely_box  # type: ignore
        except Exception:
            msg = "Shapely is required for to_shapely. Install shapely and try again."
            log_warning(logger, msg)
            raise RuntimeError(msg)
        return shapely_box(self.west, self.south, self.east, self.north)

    def reproject(self, to_crs: str) -> "BBox":
        """Return a new BBox reprojected to `to_crs` (e.g. 'EPSG:4326').

        Requires geopandas/pyproj; if not available raises RuntimeError with guidance.
        """
        try:
            import geopandas as gpd
            from shapely.geometry import box as shapely_box  # type: ignore
        except Exception:
            msg = "Reprojection requires geopandas and pyproj. Install them to enable reprojection."
            log_warning(logger, msg)
            raise RuntimeError(msg)

        geom = shapely_box(self.west, self.south, self.east, self.north)
        gdf = gpd.GeoDataFrame(index=[0], geometry=[geom])
        if self.crs is not None:
            try:
                gdf.set_crs(self.crs, inplace=True)
            except Exception:
                # try to interpret numeric EPSG
                try:
                    gdf.set_crs(int(str(self.crs).split(':')[-1]), inplace=True)
                except Exception:
                    pass
        # perform reprojection
        gdf = gdf.to_crs(to_crs)
        tb = gdf.total_bounds
        new = BBox((tb[0], tb[1], tb[2], tb[3]))
        # set CRS and projected flag on returned BBox
        new.crs = str(to_crs)
        new.is_projected = new._determine_is_projected(new.crs)
        return new

    # backward compatible helpers
    def bbox_tuple(self) -> Tuple[float, float, float, float]:
        return self.to_tuple()

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"BBox(west={self.west}, south={self.south}, east={self.east}, north={self.north}, crs={self.crs})"

