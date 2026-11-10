"""Run one bounded geographic validation and record its evidence.

Usage:
    python docs/book/validation/run_validation.py --run-id fresh --validation-root PATH
    python docs/book/validation/run_validation.py --run-id offline --validation-root PATH --block-network
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[3]
BBOX = (-122.4130, 37.8010, -122.4010, 37.8100)
PLACE = "Telegraph Hill SF validation"
BASE = REPO / "output" / "validation" / "sf_telegraph_hill"
NETWORK_TIMEOUT_SECONDS = 30


def _request_target(url: Any) -> tuple[str, str]:
    parsed = urlparse(str(url))
    return parsed.netloc, parsed.path


def _file_manifest(directory: Path) -> list[dict[str, Any]]:
    files = []
    for path in sorted(directory.glob("*")):
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            files.append(
                {
                    "name": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": digest,
                }
            )
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--validation-root", type=Path, default=BASE)
    parser.add_argument("--block-network", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
        parser.error("--run-id may contain only ASCII letters, numbers, '_' and '-'.")

    sys.path.insert(0, str(REPO))
    load_dotenv(REPO / ".env")

    validation_root = args.validation_root
    if not validation_root.is_absolute():
        validation_root = REPO / validation_root
    validation_root = validation_root.resolve()
    output_dir = validation_root / "out" / args.run_id
    summary_path = validation_root / f"summary_{args.run_id}.json"
    if output_dir.exists() or summary_path.exists():
        parser.error(f"Run output already exists; refusing to overwrite: {args.run_id}")

    cache_dir = validation_root / "cache" / "osm2terrn"
    osmnx_cache_dir = validation_root / "cache" / "osmnx"
    logs_dir = validation_root / "logs"
    for directory in (output_dir, cache_dir, osmnx_cache_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)

    from osm2terrn.app.main import (
        _build_parser,
        _build_program_cli_overrides,
        _build_project_cli_overrides,
    )
    from osm2terrn.config.settings import configure, get_project_loader

    cli = _build_parser().parse_args(
        [
            "--cache-dir",
            str(cache_dir),
            "--output-dir",
            str(output_dir),
            "--logs-dir",
            str(logs_dir),
            "--export-output-name",
            "sf_telegraph_hill",
        ]
    )
    loader = get_project_loader()
    program_config = loader.load_program_config(
        cli_overrides=_build_program_cli_overrides(cli)
    )
    project_config = loader.load_project_config(
        project_root=None,
        config_file=None,
        cli_overrides=_build_project_cli_overrides(cli),
    )
    configure(program_config=program_config, project_config=project_config)

    import osmnx as ox
    import osmnx._overpass as overpass
    import requests
    import rasterio
    from rasterio.io import MemoryFile
    from rasterio.transform import rowcol

    from osm2terrn.cli import commands
    from osm2terrn.data import osm_data_handler
    from osm2terrn.processing import orchestrator
    from osm2terrn.processing.roads import road_elevation

    ox.settings.cache_folder = str(osmnx_cache_dir)
    ox.settings.requests_timeout = NETWORK_TIMEOUT_SECONDS
    ox.settings.doh_url_template = None

    request_log: list[dict[str, Any]] = []
    dem_responses: list[dict[str, Any]] = []
    invalid_road_samples: set[tuple[float, float]] = set()
    nodata_road_samples: set[tuple[float, float]] = set()
    blocked_network_calls = 0

    original_get = requests.get
    original_post = requests.post

    def _record_request(method: str, url: Any) -> dict[str, Any]:
        host, path = _request_target(url)
        record: dict[str, Any] = {
            "method": method,
            "host": host,
            "path": path,
            "status_code": None,
            "error_type": None,
            "redirect_count": 0,
            "final_host": None,
            "final_path": None,
        }
        request_log.append(record)
        return record

    def _record_response(
        record: dict[str, Any],
        response: requests.Response,
    ) -> None:
        final_host, final_path = _request_target(response.url)
        record.update(
            {
                "status_code": response.status_code,
                "redirect_count": len(response.history),
                "final_host": final_host,
                "final_path": final_path,
            }
        )

    def _inspect_dem_response(response: requests.Response) -> None:
        if response.status_code != 200:
            return
        measurement: dict[str, Any] = {
            "status_code": response.status_code,
        }
        try:
            with MemoryFile(response.content) as memory_file:
                with memory_file.open() as dataset:
                    measurement.update(
                        {
                            "crs": dataset.crs.to_string() if dataset.crs else None,
                            "width": dataset.width,
                            "height": dataset.height,
                            "bounds": [
                                float(value) for value in dataset.bounds
                            ],
                            "pixel_size": [
                                float(dataset.transform.a),
                                float(dataset.transform.e),
                            ],
                            "nodata": dataset.nodata,
                        }
                    )
        except Exception as exc:
            measurement["inspection_error_type"] = type(exc).__name__
        dem_responses.append(measurement)

    def _tracked_get(url: Any, *args: Any, **kwargs: Any) -> requests.Response:
        host, path = _request_target(url)
        if host == "portal.opentopography.org":
            kwargs.setdefault(
                "timeout",
                (5, NETWORK_TIMEOUT_SECONDS),
            )
        record = _record_request("GET", url)
        try:
            response = original_get(url, *args, **kwargs)
        except Exception as exc:
            record["error_type"] = type(exc).__name__
            raise
        _record_response(record, response)
        if host == "portal.opentopography.org" and path.endswith("/globaldem"):
            _inspect_dem_response(response)
        return response

    def _tracked_post(url: Any, *args: Any, **kwargs: Any) -> requests.Response:
        host, path = _request_target(url)
        record = _record_request("POST", url)
        try:
            response = original_post(url, *args, **kwargs)
        except Exception as exc:
            record["error_type"] = type(exc).__name__
            raise
        _record_response(record, response)
        if host == "overpass-api.de" and path.endswith("/interpreter"):
            if response.status_code in {429, 504}:
                record["retry_blocked"] = True
                raise requests.HTTPError(
                    f"Overpass returned HTTP {response.status_code}; validation stops this layer without retry.",
                    response=response,
                )
        return response

    requests.get = _tracked_get
    requests.post = _tracked_post

    original_pause = overpass._get_overpass_pause
    pause_state = {"inside_status_check": False}

    def _single_overpass_status_check(*args: Any, **kwargs: Any) -> float:
        if pause_state["inside_status_check"]:
            raise RuntimeError(
                "Overpass status polling exceeded the validation limit."
            )
        pause_state["inside_status_check"] = True
        try:
            return min(
                original_pause(*args, **kwargs),
                NETWORK_TIMEOUT_SECONDS,
            )
        finally:
            pause_state["inside_status_check"] = False

    overpass._get_overpass_pause = _single_overpass_status_check

    original_road_sample = road_elevation.sample_elevation_at_coords

    def _measure_road_sample(
        lon: Any,
        lat: Any,
        elevation: Any,
        transform: Any,
    ) -> Any:
        import numpy as np

        lon_array = np.asarray(lon, dtype=float)
        lat_array = np.asarray(lat, dtype=float)
        rows, cols = rowcol(transform, lon_array, lat_array, op=round, precision=0)
        rows = np.asarray(rows, dtype=int)
        cols = np.asarray(cols, dtype=int)
        inside = (
            (rows >= 0)
            & (rows < elevation.shape[0])
            & (cols >= 0)
            & (cols < elevation.shape[1])
        )
        for x, y in zip(lon_array[~inside], lat_array[~inside]):
            invalid_road_samples.add((round(float(x), 8), round(float(y), 8)))
        if np.any(inside):
            values = elevation[rows[inside], cols[inside]]
            valid_values = np.isfinite(values)
            for x, y in zip(
                lon_array[inside][~valid_values],
                lat_array[inside][~valid_values],
            ):
                nodata_road_samples.add((round(float(x), 8), round(float(y), 8)))
        return original_road_sample(lon_array, lat_array, elevation, transform)

    road_elevation.sample_elevation_at_coords = _measure_road_sample

    if args.block_network:
        def _blocked(*_args: Any, **_kwargs: Any) -> None:
            nonlocal blocked_network_calls
            blocked_network_calls += 1
            raise OSError("network blocked by validation driver")

        socket.socket.connect = _blocked  # type: ignore[assignment]
        socket.getaddrinfo = _blocked  # type: ignore[assignment]
        socket.create_connection = _blocked  # type: ignore[assignment]

    original_roads_outcome = getattr(orchestrator, "_roads_outcome")
    original_cli_export = commands.export_terrain_assets
    captured: dict[str, Any] = {}

    def _spy_roads_outcome(metadata: dict[str, Any]) -> str:
        captured["metadata"] = {
            key: (
                value
                if isinstance(value, (str, int, float, bool, type(None)))
                else str(value)
            )
            for key, value in metadata.items()
        }
        return original_roads_outcome(metadata)

    def _capture_export(**kwargs: Any) -> dict[str, Any]:
        result = original_cli_export(**kwargs)
        captured["export_result"] = {
            key: (str(value) if value is not None else None)
            for key, value in result.items()
        }
        return result

    setattr(orchestrator, "_roads_outcome", _spy_roads_outcome)
    commands.export_terrain_assets = _capture_export
    commands.download_menu = lambda: (PLACE, BBOX)
    commands.clear = lambda: None

    summary: dict[str, Any] = {
        "run_id": args.run_id,
        "block_network": args.block_network,
        "bbox_wsen": BBOX,
        "place": PLACE,
        "validation_root": str(validation_root),
        "output_dir": str(output_dir),
        "cache_dir": str(cache_dir),
        "osmnx_cache_dir": str(osmnx_cache_dir),
        "configured_layers": {
            "geometry": sorted(osm_data_handler.map_geometries),
            "networks": sorted(osm_data_handler.networks),
        },
        "versions": {
            "osm_algorithm": osm_data_handler._OSM_BBOX_ALGORITHM_VERSION,
            "osm_format": "3",
            "elevation_algorithm": "1",
            "elevation_format": "1",
        },
        "opentopo_credential_configured": bool(
            os.getenv(program_config.providers.opentopo_api_key_env_var)
        ),
    }

    result_code = 0
    try:
        commands.dlcity()
        data = commands.current_map.data
        roads = data.get("roads")
        roads_graph = getattr(roads, "graph", None)
        layer_results = data.get("acquisition_results", {})
        summary.update(
            {
                "data_keys": sorted(data),
                "layer_acquisition_results": {
                    name: {
                        "status": result.status,
                        "source": result.source,
                        "failure_category": result.failure_category,
                        "failure_stage": result.failure_stage,
                        "diagnostic": result.diagnostic,
                    }
                    for name, result in layer_results.items()
                },
                "roads": {
                    "status": getattr(roads, "status", None),
                    "source": getattr(roads, "source", None),
                    "graph_crs": getattr(roads, "graph_crs", None),
                    "nodes": (
                        roads_graph.number_of_nodes()
                        if roads_graph is not None
                        else None
                    ),
                    "edges": (
                        roads_graph.number_of_edges()
                        if roads_graph is not None
                        else None
                    ),
                },
                "bounds": str(data.get("bounds")),
                "terrain_world_size_m": getattr(
                    commands.current_map, "terrain_world_size", None
                ),
                "elevation_preload_loaded": bool(
                    commands.current_map.elevation_data
                ),
            }
        )
        commands.export()
    except Exception as exc:
        result_code = 1
        summary["driver_error_type"] = type(exc).__name__

    summary.update(
        {
            "road_export_metadata": captured.get("metadata"),
            "export_result": captured.get("export_result"),
            "requests": request_log,
            "request_count": len(request_log),
            "blocked_network_call_count": blocked_network_calls,
            "elevation_geotiff_responses": dem_responses,
            "road_dem_out_of_bounds_sample_count": len(invalid_road_samples),
            "road_dem_out_of_bounds_coordinates_lon_lat": sorted(
                [list(point) for point in invalid_road_samples]
            ),
            "road_dem_nodata_sample_count": len(nodata_road_samples),
            "road_dem_nodata_coordinates_lon_lat": sorted(
                [list(point) for point in nodata_road_samples]
            ),
            "output_files": _file_manifest(output_dir),
        }
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, default=str))
    return result_code


if __name__ == "__main__":
    raise SystemExit(main())
