"""BBox utilities for geometry handling."""
from typing import Any, Dict, Optional, Tuple
from numbers import Number

from osm2terrn.utils.logger import get_logger, log_warning
from osm2terrn.utils.geometry.crs import determine_is_projected

logger = get_logger("bbox")


class BBox:
    def __init__(self, src: Any) -> None:
        if src is None:
            raise ValueError("bbox is None")

        if isinstance(src, BBox):
            self.west = float(src.west)
            self.south = float(src.south)
            self.east = float(src.east)
            self.north = float(src.north)
            self.crs = src.crs
            self.is_projected = bool(getattr(src, "is_projected", False))
            return

        if isinstance(src, dict):
            self._from_dict(src)
            return

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
            self.is_projected = False
            return

        total_bounds = getattr(src, "total_bounds", None)
        if total_bounds is not None:
            minx, miny, maxx, maxy = total_bounds
            self.west = float(minx)
            self.south = float(miny)
            self.east = float(maxx)
            self.north = float(maxy)
            self.crs = str(getattr(src, "crs", None)) if getattr(src, "crs", None) is not None else None
            self._validate()
            self.is_projected = determine_is_projected(self.crs)
            return

        bounds = getattr(src, "bounds", None)
        if bounds is not None and isinstance(bounds, (list, tuple)) and len(bounds) == 4:
            minx, miny, maxx, maxy = bounds
            self.west = float(minx)
            self.south = float(miny)
            self.east = float(maxx)
            self.north = float(maxy)
            self.crs = str(getattr(src, "crs", None)) if getattr(src, "crs", None) is not None else None
            self._validate()
            self.is_projected = determine_is_projected(self.crs)
            return

        try:
            b = getattr(src, "bounds")
            if b and isinstance(b, tuple) and len(b) == 4:
                minx, miny, maxx, maxy = b
                self.west = float(minx)
                self.south = float(miny)
                self.east = float(maxx)
                self.north = float(maxy)
                self.crs = str(getattr(src, "crs", None)) if getattr(src, "crs", None) is not None else None
                self._validate()
                self.is_projected = determine_is_projected(self.crs)
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
                self.is_projected = determine_is_projected(self.crs)
                return
        raise ValueError("Dictionary bbox must contain keys like west/south/east/north or minx/miny/maxx/maxy")

    def _validate(self) -> None:
        if not all(isinstance(x, Number) for x in (self.west, self.south, self.east, self.north)):
            raise ValueError("BBox values must be numeric")
        if not (self.west < self.east and self.south < self.north):
            raise ValueError("Invalid bbox: require west < east and south < north")

    def as_dict(self) -> Dict[str, Any]:
        return {
            "west": float(self.west),
            "south": float(self.south),
            "east": float(self.east),
            "north": float(self.north),
            "crs": self.crs,
            "is_projected": bool(getattr(self, "is_projected", False)),
        }

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
                try:
                    gdf.set_crs(int(str(self.crs).split(':')[-1]), inplace=True)
                except Exception:
                    pass
        gdf = gdf.to_crs(to_crs)
        tb = gdf.total_bounds
        new = BBox((tb[0], tb[1], tb[2], tb[3]))
        new.crs = str(to_crs)
        new.is_projected = determine_is_projected(new.crs)
        return new

    def bbox_tuple(self) -> Tuple[float, float, float, float]:
        return self.to_tuple()

    def __repr__(self) -> str:
        return f"BBox(west={self.west}, south={self.south}, east={self.east}, north={self.north}, crs={self.crs})"
