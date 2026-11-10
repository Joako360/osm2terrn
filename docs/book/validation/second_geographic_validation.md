# Second integrated geographic validation — Telegraph Hill

Execution log timestamps: 2026-11-05 00:21–00:24 (machine-local log time).

Status: **partial**. Elevation and terrain assets were generated; OSM layers
were not acquired. The terrain was not loaded in Rigs of Rods.

This report records the approved single run in
`output/validation/sf_telegraph_hill/second_validation_20261104/`. It does not
replace the [first geographic validation](./first_geographic_validation.md).

## Region, sources, and versions

- Requested bbox, EPSG:4326, west/south/east/north:
  `-122.4130, 37.8010, -122.4010, 37.8100`.
- Horizontal target passed through the CLI: 2048 m.
- OSM provider: `https://overpass-api.de/api`.
- Elevation provider: OpenTopography `globaldem`, `demtype=AW3D30`, GeoTIFF.
- Python 3.12.10; OSMnx 2.1.0; GeoPandas 1.1.4; Rasterio 1.5.0;
  pyproj 3.7.2; NumPy 2.5.1; NetworkX 3.6.1; Pillow 12.3.0.
- The OpenTopography credential was configured. Its value is not recorded.
  The complete credential was not found in the 21 files created for this run.
  No credential value is included in this report.

## Commands and automated checks

The fresh validation command was run with UTF-8 output captured to
`logs/console_fresh.txt`:

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe docs\book\validation\run_validation.py --run-id fresh --validation-root output\validation\sf_telegraph_hill\second_validation_20261104
```

The driver used the isolated OSM2Terrn and OSMnx cache directories, a 30-second
request timeout, and a maximum 30-second Overpass status pause. It recorded
hosts, paths, response statuses, redirects, and exception types without query
parameters. OSMnx itself also wrote encoded Overpass query URLs to the console
log; the complete credential scan found no OpenTopography key in the captured
run files. No automatic retry of a failed layer was observed.

The measurement command completed without network access:

```powershell
.\.venv\Scripts\python.exe docs\book\validation\measure_second_validation.py --validation-root output\validation\sf_telegraph_hill\second_validation_20261104 --run-id fresh
```

Focused offline test command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_elevation_cache.py tests\test_heightmap_cache.py tests\test_osm_data_handler_cache.py tests\test_osm_loader_cache.py tests\test_domain_adapters_cache.py tests\test_domain_architecture.py tests\test_pipeline_domain_state.py tests\test_road_export.py tests\test_geometry_utils.py tests\test_street_cache_process.py tests\test_street_network_integration.py tests\test_street_network_handoff.py -q -p no:cacheprovider --tb=short -W ignore
```

Result: **106 passed, 1 skipped** in 44.28 seconds. The skipped case is the
legacy network smoke test. These tests use synthetic data and mocks.

The following checks also passed:

```powershell
.\.venv\Scripts\python.exe -m py_compile docs\book\validation\run_validation.py docs\book\validation\measure_second_validation.py
.\.venv\Scripts\python.exe docs\book\validation\run_validation.py --help
.\.venv\Scripts\python.exe docs\book\validation\measure_second_validation.py --help
git diff --check
```

`git diff --check` exited 0; Git emitted only existing LF/CRLF conversion
warnings. A separate whitespace check covered the untracked validation scripts
and Markdown reports. Ruff was unavailable (`.venv\Scripts\ruff.exe` was not
found), so no Ruff result is claimed.

## Acquisition results

The run recorded eight HTTP calls: seven to Overpass (status checks and two
interpreter requests) and one to OpenTopography. The OpenTopography request
returned HTTP 200. Overpass returned HTTP 502 for one interpreter request;
other status checks or an interpreter request ended in `ReadTimeout`. The
Overpass status response also produced an empty/unrecognized status warning.
No retry or broader-area query was attempted.

| Layer | Result | Recorded evidence |
|---|---|---|
| Buildings | `failed` | Query source; interpreter HTTP 502. The layer result classified the failure category as `unknown` despite the separately recorded 502. |
| Parks | `failed` | Query source; temporary `ReadTimeout`. |
| Lakes | `failed` | Query source; temporary `ReadTimeout`. |
| Roads | `failed` | Query source; road diagnostic `ReadTimeout`; no graph or road geometry. |
| Rails | `failed` | Query source; temporary `ReadTimeout`. |
| Elevation preload | `available` | OpenTopography response HTTP 200; DEM was cached and used for terrain export. |

No OSM bbox bundle was written because requested OSM layers failed. The
isolated OSMnx response cache is empty. The isolated elevation cache contains
one raster; export and domain-adapter caches were also written.

The buildings result is a confirmed reporting inconsistency: the request log
records HTTP 502, but the layer's `failure_category` is `unknown`. This run
does not change acquisition classification logic; a follow-up should verify
status extraction from OSMnx `ResponseStatusCodeError` instances.

## Terrain, scale, and spatial measurements

| Measurement | Observed value |
|---|---|
| Requested bbox dimensions, project helper | 1062.69 × 1005.25 m |
| Expanded geographic bounds dimensions, project helper | 2073.82 × 2048.00 m |
| Exported `WorldSizeX` / `WorldSizeZ` | 2048 / 2048 m |
| Exported `WorldSizeY` | 114 m |
| Heightmap | 1025 × 1025 pixels, 8-bit grayscale (`L`), values 1–239, 239 distinct values |
| Heightmap edge means | top 2.00; bottom 91.02; left 82.08; right 2.59 |

The live DEM response and its isolated cache entry agree:

- CRS: EPSG:4326.
- Dimensions: 84 × 66 pixels.
- Bounds: west `-122.4188889`, south `37.7963889`, east `-122.3955556`,
  north `37.8147222`.
- Pixel size: approximately `+0.0002777778°` east-west and
  `-0.0002777778°` north-south.
- Geodesic extent at the raster midpoint: approximately 2054.82 × 2034.87 m.
- Elevation minimum/maximum: -1 m / 113 m; the response had no declared
  NoData value, and the cached array contained zero NaN cells.
- The DEM bounds contain the requested bbox.

The exported horizontal `WorldSize` is 2048 m in both axes. The helper's
expanded geographic bounds are not numerically identical in both dimensions;
this alone does not establish a terrain-scale defect because projected bounds
and Rigs of Rods `WorldSize` are not proven to use directly comparable
coordinates here. The runtime interpretation still needs simulator
verification.

Street CRS, extent, street/building correspondence, road DEM coverage, and
out-of-bounds road samples could not be measured because no street graph was
acquired. The driver's zero invalid-sample counters mean the road sampling
hook was not reached; they do **not** show that all roads are covered.

## Export and generated files

The CLI reported a partial export: roads were not exported; building export is
not implemented. Independent terrain stages continued, and the validation
driver exited with code 0 because the pipeline completed without an uncaught
exception. No road `.tobj` was generated.

All references measured in the `.terrn2` and page `.otc` resolve to files in
the configured `out/fresh/` directory:

| File | Bytes |
|---|---:|
| `Telegraph Hill SF validation.terrn2` | 502 |
| `Telegraph Hill SF validation.otc` | 235 |
| `Telegraph Hill SF validation-page-0-0.otc` | 279 |
| `Telegraph Hill SF validation_heightmap.png` | 68,890 |
| `Telegraph Hill SF validation_groundmap.png` | 269,757 |
| `Telegraph Hill SF validation.tobj` | 63 |

SHA-256 hashes, parsed references, and the complete measured output manifest
are recorded in `output/validation/sf_telegraph_hill/second_validation_20261104/measure_fresh.json`.
The acquisition and export metadata are in
`output/validation/sf_telegraph_hill/second_validation_20261104/summary_fresh.json`;
the console log is in `output/validation/sf_telegraph_hill/second_validation_20261104/logs/console_fresh.txt`.

## Reproducibility and comparison with the first validation

An offline repeat was **not run**: the isolated OSM2Terrn and OSMnx caches
contain no OSM bundle or successful OSM response cache, so the complete
pipeline could not be replayed with network access blocked. The fresh terrain
files and hashes are preserved for a later comparison.

Compared with the first validation report, this run measured `WorldSizeX/Z`
at 2048 m rather than 4096 m, matching the selected target. The preload DEM
has the same reported CRS, pixel dimensions, bounds, and elevation range as
the earlier measurement. The earlier run acquired streets; this run did not,
so road output and road/DEM consistency are not comparable.

## Reproduction and limitations

Use the same driver with the same bbox and a **new, empty validation root**
and unique run ID to avoid overwriting this evidence. Do not use
`--block-network` unless the required OSM and elevation data are present in
that isolated cache. This run made no expanded-area request and did not retry
failed layers.

Still unverified:

- Street and building acquisition, graph CRS/extent, and correspondence with
  the DEM.
- Road-elevation sampling and road coordinates outside the DEM or on NoData.
- Offline output reproducibility.
- Rigs of Rods interpretation of `WorldSize`, heightmap orientation, asset
  placement, and successful simulator loading.

The generated terrain has **not** been loaded or visually checked in Rigs of
Rods.
