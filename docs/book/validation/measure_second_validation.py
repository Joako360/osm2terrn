"""Measure outputs from the isolated second geographic validation."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from pyproj import CRS, Transformer
from rasterio.transform import array_bounds

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from osm2terrn.cache.serializers import PickleSerializer
from osm2terrn.domain.value_objects import BoundingBox
from osm2terrn.utils.geometry.bounds import (
    bbox_size_meters,
    compute_world_params,
    make_square_bounds_centered,
)

BBOX = (-122.4130, 37.8010, -122.4010, 37.8100)


def _read_cache_value(path: Path) -> tuple[Any, dict[str, Any]]:
    metadata_path = path.with_suffix(".meta.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    value = PickleSerializer[Any]().loads(path.read_bytes())
    return value, metadata


def _parse_sections(path: Path) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    section = ""
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith((";", "//")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            sections.setdefault(section, {})
        elif "=" in line:
            key, value = line.split("=", 1)
            sections.setdefault(section, {})[key.strip()] = value.strip()
    return sections


def _sha256(path: Path, normalize_guid: bool = False) -> str:
    content = path.read_bytes()
    if normalize_guid and path.suffix.lower() == ".terrn2":
        content = re.sub(
            rb"(?m)^GUID\s*=\s*.*$",
            b"GUID = <generated-guid>",
            content,
        )
    return hashlib.sha256(content).hexdigest()


def _measure_outputs(output_dir: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "output_dir": str(output_dir),
        "files": [
            {
                "path": str(path.relative_to(output_dir)),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in sorted(output_dir.glob("*"))
            if path.is_file()
        ],
        "references": {},
        "reference_checks": {},
    }

    terrn2_files = list(output_dir.glob("*.terrn2"))
    otc_files = list(output_dir.glob("*.otc"))
    if len(terrn2_files) != 1:
        result["artifact_error"] = f"Expected one .terrn2 file, found {len(terrn2_files)}"
        return result

    terrn2 = terrn2_files[0]
    sections = _parse_sections(terrn2)
    general = sections.get("General", {})
    object_refs = list(sections.get("Objects", {}))
    geometry_ref = general.get("GeometryConfig", "")
    page_ref = ""
    if geometry_ref:
        global_otc = output_dir / geometry_ref
        if global_otc.is_file():
            global_text = global_otc.read_text(encoding="utf-8", errors="replace")
            page_match = re.search(r"(?m)^PageFileFormat\s*=\s*(.+?)\s*$", global_text)
            if page_match:
                page_ref = page_match.group(1)

    paged_refs: list[str] = []
    heightmap_ref = ""
    if page_ref:
        paged_otc = output_dir / page_ref
        if paged_otc.is_file():
            lines = [
                line.strip()
                for line in paged_otc.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()
                if line.strip() and not line.lstrip().startswith(";")
            ]
            if lines:
                heightmap_ref = lines[0]
            for line in lines[3:]:
                for token in line.split(","):
                    candidate = token.strip()
                    if candidate.lower().endswith((".png", ".jpg", ".jpeg")):
                        paged_refs.append(candidate)

    local_refs = [geometry_ref, page_ref, heightmap_ref, *object_refs, *paged_refs]
    result["references"] = {
        "geometry_config": geometry_ref,
        "page_file": page_ref,
        "heightmap": heightmap_ref,
        "objects": object_refs,
        "paged_texture_files": paged_refs,
    }
    result["reference_checks"] = {
        ref: (output_dir / ref).is_file()
        for ref in dict.fromkeys(ref for ref in local_refs if ref)
    }

    world_sizes: dict[str, str] = {}
    if geometry_ref and (output_dir / geometry_ref).is_file():
        for line in (output_dir / geometry_ref).read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            if re.match(r"^WorldSize[XYZ]\s*=", line):
                key, value = line.split("=", 1)
                world_sizes[key.strip()] = value.strip()
    result["world_sizes"] = world_sizes
    result["terrn2_guid_normalized_sha256"] = _sha256(terrn2, normalize_guid=True)

    heightmap = output_dir / heightmap_ref if heightmap_ref else None
    if heightmap and heightmap.is_file():
        with Image.open(heightmap) as image:
            values = np.asarray(image)
            image_mode = image.mode
        gray = values if values.ndim == 2 else values[..., 0]
        result["heightmap"] = {
            "mode": image_mode,
            "dimensions": list(image.size),
            "dtype": str(values.dtype),
            "minimum": int(values.min()),
            "maximum": int(values.max()),
            "unique_values": int(np.unique(values).size),
            "top_rows_mean": float(gray[:8].mean()),
            "bottom_rows_mean": float(gray[-8:].mean()),
            "left_columns_mean": float(gray[:, :8].mean()),
            "right_columns_mean": float(gray[:, -8:].mean()),
        }
    return result


def _measure_inputs(validation_root: Path, summary: dict[str, Any]) -> dict[str, Any]:
    cache_dir = validation_root / "cache" / "osm2terrn"
    osm_entries: list[dict[str, Any]] = []
    for path in sorted(
        (cache_dir / "providers" / "osm" / "bbox-bundle").glob("*.bin")
    ):
        _, metadata = _read_cache_value(path)
        osm_entries.append(
            {
                "key": path.stem,
                "provider": metadata.get("provider"),
                "artifact_type": metadata.get("artifact_type"),
                "algorithm_version": metadata.get("algorithm_version"),
                "format_version": metadata.get("format_version"),
            }
        )

    cached_rasters: list[dict[str, Any]] = []
    for path in sorted(
        (cache_dir / "providers" / "elevation" / "raster").glob("*.bin")
    ):
        value, metadata = _read_cache_value(path)
        elevation, transform, maximum, minimum = value
        height, width = elevation.shape
        west, south, east, north = array_bounds(height, width, transform)
        cached_rasters.append(
            {
                "key": path.stem,
                "provider": metadata.get("provider"),
                "algorithm_version": metadata.get("algorithm_version"),
                "format_version": metadata.get("format_version"),
                "crs_in_cache_payload": None,
                "dimensions": [int(width), int(height)],
                "bounds_wsen": [
                    float(west),
                    float(south),
                    float(east),
                    float(north),
                ],
                "pixel_size": [float(transform.a), float(transform.e)],
                "minimum": float(minimum),
                "maximum": float(maximum),
                "nodata_cells": int(np.isnan(elevation).sum()),
            }
        )
    return {
        "osm_cache_entries": osm_entries,
        "elevation_cache_rasters": cached_rasters,
        "geotiff_crs_from_live_responses": summary.get(
            "elevation_geotiff_responses", []
        ),
    }


def _measure_bounds_and_streets(summary: dict[str, Any]) -> dict[str, Any]:
    bounds = BoundingBox(*BBOX, crs="EPSG:4326", is_projected=False)
    width_m, height_m = bbox_size_meters(bounds)
    world_size, _meters_per_pixel = compute_world_params(bounds)
    square_bounds = make_square_bounds_centered(bounds, world_size)
    square_width_m, square_height_m = bbox_size_meters(square_bounds)

    roads = summary.get("roads", {})
    graph_crs_text = roads.get("graph_crs")
    graph_extent = None
    graph_units = None
    if graph_crs_text and roads.get("nodes"):
        from osm2terrn.data.street_network import StreetNetworkResult

        cache_dir = Path(summary["cache_dir"])
        bundle_files = sorted(
            (cache_dir / "providers" / "osm" / "bbox-bundle").glob("*.bin")
        )
        for path in bundle_files:
            bundle, metadata = _read_cache_value(path)
            if (
                metadata.get("algorithm_version")
                != summary["versions"]["osm_algorithm"]
                or metadata.get("format_version")
                != summary["versions"]["osm_format"]
            ):
                continue
            road_result = bundle.get("roads")
            if not isinstance(road_result, StreetNetworkResult):
                continue
            graph = road_result.graph
            if graph is None:
                continue
            crs = CRS.from_user_input(graph_crs_text)
            graph_units = crs.axis_info[0].unit_name if crs.axis_info else None
            transformer = Transformer.from_crs(
                crs, "EPSG:4326", always_xy=True
            )
            points = [
                transformer.transform(float(data["x"]), float(data["y"]))
                for _, data in graph.nodes(data=True)
                if "x" in data and "y" in data
            ]
            if points:
                graph_extent = {
                    "crs": crs.to_string(),
                    "coordinate_units": graph_units,
                    "bounds_lon_lat": [
                        min(point[0] for point in points),
                        min(point[1] for point in points),
                        max(point[0] for point in points),
                        max(point[1] for point in points),
                    ],
                    "node_count": len(points),
                    "edge_count": graph.number_of_edges(),
                }
            break
    return {
        "requested_bbox_crs": "EPSG:4326",
        "requested_bbox_wsen": BBOX,
        "requested_bbox_dimensions_m": [width_m, height_m],
        "initial_world_size_m": world_size,
        "expanded_bbox_bounds_dimensions_m": [square_width_m, square_height_m],
        "world_size_from_cli_summary_m": summary.get("terrain_world_size_m"),
        "street_graph_extent": graph_extent,
        "road_dem_out_of_bounds_sample_count": summary.get(
            "road_dem_out_of_bounds_sample_count"
        ),
        "road_dem_out_of_bounds_coordinates_lon_lat": summary.get(
            "road_dem_out_of_bounds_coordinates_lon_lat", []
        ),
        "road_dem_nodata_sample_count": summary.get(
            "road_dem_nodata_sample_count"
        ),
        "road_dem_nodata_coordinates_lon_lat": summary.get(
            "road_dem_nodata_coordinates_lon_lat", []
        ),
    }


def _compare_runs(validation_root: Path, first_run: str, second_run: str) -> dict[str, Any]:
    first_dir = validation_root / "out" / first_run
    second_dir = validation_root / "out" / second_run
    first_files = {
        path.name: path
        for path in first_dir.glob("*")
        if path.is_file()
    }
    second_files = {
        path.name: path
        for path in second_dir.glob("*")
        if path.is_file()
    }
    common = sorted(first_files.keys() & second_files.keys())
    differences = []
    for name in common:
        normalize_guid = name.lower().endswith(".terrn2")
        if _sha256(first_files[name], normalize_guid) != _sha256(
            second_files[name], normalize_guid
        ):
            differences.append(name)
    return {
        "first_run": first_run,
        "second_run": second_run,
        "first_only_files": sorted(first_files.keys() - second_files.keys()),
        "second_only_files": sorted(second_files.keys() - first_files.keys()),
        "different_common_files": differences,
        "guid_normalized_for_terrn2": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--compare-run-id")
    args = parser.parse_args()

    validation_root = args.validation_root
    if not validation_root.is_absolute():
        validation_root = REPO / validation_root
    validation_root = validation_root.resolve()
    summary_path = validation_root / f"summary_{args.run_id}.json"
    if not summary_path.is_file():
        parser.error(f"Run summary not found: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    measurements = {
        "run_id": args.run_id,
        "artifacts": _measure_outputs(validation_root / "out" / args.run_id),
        "inputs_and_cache": _measure_inputs(validation_root, summary),
        "spatial_measurements": _measure_bounds_and_streets(summary),
    }
    if args.compare_run_id:
        measurements["reproducibility"] = _compare_runs(
            validation_root,
            args.compare_run_id,
            args.run_id,
        )

    output_path = validation_root / f"measure_{args.run_id}.json"
    output_path.write_text(
        json.dumps(measurements, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(measurements, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
