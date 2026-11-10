# First controlled geographic validation — Telegraph Hill, San Francisco

Date: 2026-10-27. Status: **partial** (roads, elevation and exports measured; buildings not acquired; nothing loaded in Rigs of Rods).
Legend: **[M]** measured, **[I]** inferred, **[U]** not verified / manual.

## 1. Region and limits
- Requested bbox (EPSG:4326, west, south, east, north): `-122.4130, 37.8010, -122.4010, 37.8100` — about 1057 × 999 m **[M]**.
- Place label used by the driver: `Telegraph Hill SF validation`. Origin used by the pipeline: lon -122.4070, lat 37.8055 **[M]**.
- The region was chosen as small, dense in streets, hilly and next to water (a priori choice, approved by the user).

## 2. Sources and versions actually used
| Item | Evidence |
|---|---|
| Streets (and rails graph) | OSM via osmnx `graph_from_bbox` → `overpass-api.de` (log lines `Downloaded ... from 'overpass-api.de'`) **[M]** |
| Parks | OSM via `features_from_bbox`; 17 features in run 2 (earlier cache); `parks=None` in later bundles because of the failure in §6 **[M]** |
| Elevation | OpenTopography `globaldem`, `demtype=AW3D30`, GeoTIFF, pixel 0.000278° (~30 m) **[M]**; key present in `.env` (value not recorded) |
| Overture / `elevation_url_template` | Not used by this flow **[M]** (no log activity) |
| Libraries | osmnx 2.1.0, rasterio 1.5.0, geopandas 1.1.4, pyproj 3.7.2, numpy 2.5.1, networkx 3.6.1, Pillow 12.3.0, Python 3.12 |
| Repository | HEAD `f34a086` plus the uncommitted working tree (see `git status`) |

## 3. Files
- Driver: `docs/book/validation/run_validation.py` (only imports project code; patches `download_menu`, `clear` and records metadata). Measurement: `docs/book/validation/measure.py`.
- Everything produced is under `output/validation/sf_telegraph_hill/` (gitignored by `output/*`): `cache/` (reproducible inputs), `out/run1..run4/`, `console_run*.txt` (API key line redacted), `summary_run*.json`, `measure_run1.txt`, `cache_aside_502/` (v4 bundle set aside, not deleted).
- Outputs per run: `*.terrn2`, `*.otc`, `*-page-0-0.otc`, `*_heightmap.png`, `*_groundmap.png`, `*.tobj` (comment-only domain manifest). The procedural-roads `*_roads.tobj` is **not** in the run directory (see P-3).

## 4. Runs and commands
All commands: `.\.venv\Scripts\python.exe docs\book\validation\run_validation.py --run-id <id> [--block-network]` with `PYTHONUTF8=1`.
| Run | Purpose | Result |
|---|---|---|
| (aborted first attempt) | First real acquisition | Overpass roads + DEM downloaded; stopped by `UnicodeEncodeError` (cp1252 console vs `✓`) in the driver's piped console, not a data problem. Its console was discarded because the project log prints part of the API key (P-7). |
| run1 | Re-run with UTF-8; OSM bundle and preload DEM from cache | exit 0, "Export complete", roads `available`, `road_export_status=exported` |
| run2 | After fix P-1 (new cache key v4) | New Overpass queries; buildings got HTTP 502; export complete |
| run3 | Single retry of the same bbox | Buildings 502 again; export complete |
| run4 | `--block-network` (sockets blocked), cache only | exit 0, no network use, export complete |
Focused synthetic suite after the acquisition-call fix: **83 passed, 1 skipped**. After the credential-log fix, the expanded offline focused suite reported **86 passed, 1 skipped**; `git diff --check` exited 0 (only pre-existing LF/CRLF warnings).

## 5. Measurements
**Streets [M]**: status `available`, source `query`, CRS `+proj=aeqd` centred on the origin (metres), 641 nodes, 1079 edges; local extent x -527.4…527.0, y -498.3…371.2. Statuses: acquisition/MapData/processing `available`, export `exported`, `roads_exported=true`.
**Rails graph [M]**: 146 nodes, 288 edges in the same bundle.
**Elevation [M]**: two rasters were requested and cached:
- Preload (heightmap): 84 × 66 px, bounds -122.41889…-122.39556 / 37.79639…37.81472, ≈ 2055 × 2034 m, min -1 m, max 113 m.
- Export (road heights): 43 × 28 px, bounds -122.41306…-122.40111 / 37.80111…37.80889, ≈ 1052 × 864 m, min -1 m, max 92 m.
**Heightmap [M]**: `1025 × 1025`, 8-bit `L`, values 1…239, 239 distinct values, north rows mean 2.0 / south rows mean 91.0, west columns 82.1 / east 2.6. Row 0 of the source DEM is north (mean 0.0) and its last row (south) is higher (39.6), consistent with a north-up raster; whether the PNG matches Rigs of Rods' axis convention is **[U]**.
**Terrain files [M]**: `WorldSizeX/Z=4096`, `WorldSizeY=114`, `PageSize=1025`; paged `.otc` layer `worldSize=8192`; `.terrn2` `[Objects]` lists the domain `.tobj` and `..._roads.tobj`; water line -1.0.
**Roads `.tobj` [M]**: 4353 lines; 535 procedural road sections, 321 intersection objects; coordinates x -527.4…527.0, y (height) 0…76, z -371.2…498.3 (z = -local y).
**Reproducibility [M]**: run3 vs run4 (offline) → heightmap, groundmap, both `.otc` and the domain `.tobj` byte-identical; `.terrn2` differs only in the `GUID` line (it changes per run) **[M]**. The roads `.tobj` has size 176598 B in every run, but the file is overwritten in place, so run-to-run identity was only snapshotted for run4 (sha256 prefix `AA315B11A3C52D07`) **[M]**.

## 6. Problems by stage
**Acquisition**
- **P-1 (defect, fixed).** `osm_data_handler.py` called `ox.features_from_bbox(west, south, east, north, tags=...)`; osmnx 2.1.0's signature is `(bbox, tags)`, so the call raises `TypeError: got multiple values for argument 'tags'` (reproduced offline) and `download_data_from_bbox` swallowed it at INFO level. Consequence: buildings, parks and lakes were **always `None`** in run1's bundle although the same query with the correct form returned 1070 buildings and 17 parks for this bbox **[M]**. The existing test faked the old 4-argument signature, hiding it. Fix: pass the bbox as a tuple; `_OSM_BBOX_ALGORITHM_VERSION` `"3"`→`"4"` so bundles with silently-empty layers are not reused; the fake and the two literal-`"3"` assertions were adapted and a no-silently-skipped-layer assertion added.
- **P-2 (open).** Overpass answered 502 for the buildings query in run2 and run3. The project logs it as `Skipped geometry ... ` at INFO and **caches the bundle with `buildings=None`**, and the CLI still prints "Export complete" (`manifest: buildings=0`). Buildings, and street–building correspondence, were therefore **not validated**; the 502 is transient on the provider side (the diagnostic query had succeeded earlier) **[M]**. No further retries were made.
- **P-3 (observation).** Lakes returns "No matching features" (legitimate for this area, logged as skipped) **[M]**.
**Elevation / terrain consistency**
- **P-4 (open, needs decision).** The heightmap DEM covers ≈2055 × 2034 m but `WorldSizeX/Z=4096` **[M]**. Whether the heightmap is stretched ×2 (cause not determined) **[U]**.
- **P-5 (open).** Road heights come from a second DEM (≈1052 × 864 m, max 92 m) different from the heightmap DEM (max 113 m); its bounds are ≈11 m short of the southern road extent (y -498 vs DEM -487), so those nodes fall outside it. Behaviour outside the raster was not examined **[M]/[U]**.
**Export**
- **P-6 (defect, not fixed).** `roads.tobj` is written to `osm2terrn/output/` (package tree, now untracked) instead of the configured output dir, named with the place and not the export name; `.terrn2` references it, but it is not next to the `.terrn2` **[M]**. Cause: `tobj_exporter` log shows `.../processing/network/../../output`; not changed.
- **P-7 (credential exposure, mitigated in code).** The previous implementation logged the first and last 3 characters of the OpenTopography key at INFO; an unsuccessful HTTP response could also put the full request URL in a logged and propagated exception **[M]**. The logger now omits key fragments, and the HTTP path logs/raises only a safe status/type diagnostic. Automated tests use a sentinel key and assert that neither its full value nor its fragments appear in captured logs, terminal output, or the raised error; no actual key value is included. **Rotate the key as a precaution because previous logs may contain exposed material. Rotation has not been performed or verified.**
- **P-8 (environment).** `console.print("✓ ...")` raises `UnicodeEncodeError` when stdout is a cp1252 pipe **[M]**; the interactive terminal was not exercised.
**Coordinates**
- **P-9 (unverified).** All road/object coordinates are centred on (0,0) with negative values, while `WorldSize*=4096`. Whether Rigs of Rods centres the terrain on the origin, and the sign of z, require loading **[U]**.

## 7. Reproduction
1. `git checkout f34a086` + working tree, `.\.venv\Scripts\Activate.ps1`; `.env` with `OPENTOPO_ELEVATION_API_KEY` (never commit it).
2. `$env:PYTHONUTF8='1'; python docs\book\validation\run_validation.py --run-id runN` (network once, populates `output/validation/sf_telegraph_hill/cache/`).
3. Offline repeat: add `--block-network`; compare hashes of the files in `out/runN` (ignore the `.terrn2` GUID).
4. `python docs\book\validation\measure.py runN` prints the measurements above.
Note: the roads `.tobj` is overwritten in `osm2terrn/output/`; snapshot it between runs.

## Offline code and test follow-up

The observations above describe the earlier geographic run; the following
code-level changes were verified later with synthetic data and mocked
providers. The cached 502 outcome is now represented as a failed acquisition
layer rather than a successful empty result. Failed bundles are not cached as
successful acquisitions, a later successful retry can be cached, and the
algorithm-5 lookup does not reuse the tested algorithm-4/format-2 key. The
historical run outputs and cache were not deleted or rewritten.

The procedural road writer now defaults to the configured output directory,
and `build_roads_from_place()` forwards an explicit output directory. Tests
cover the configured default from a different working directory. This does
not relocate the earlier `osm2terrn/output/` file or verify a newly generated
`.terrn2` reference set.

The focused offline suite most recently reported **105 passed, 1 skipped**;
the skipped test is a legacy network smoke test. The user selected an
approximately 2048 m target, and the subsequent focused suite reported
**106 passed, 1 skipped**. A mocked CLI integration test confirms the initial
2048 m value reaches both horizontal dimensions passed to the global OTC
exporter; this did not regenerate the geographic run outputs. No new provider
request, terrain generation, or simulator run was performed. The measured
scale facts in Sections 5 and 6 remain observations, not proof of a scale
defect. `WorldSize` runtime interpretation, road-DEM alignment and
out-of-raster behavior still require separate evidence. The terrain has not
been loaded in Rigs of Rods.

## 8. Still requiring manual inspection in Rigs of Rods
Load `out/run4/*.terrn2` (copy the roads `.tobj` next to it): terrain scale versus roads (P-4, P-9), axis orientation of heightmap and roads, road drape on terrain, texture/groundmap alignment, missing assets (`road-crossing`, `terrain_detail.dds`, `blank_NRM.dds`), and building placement once the buildings query succeeds. **The terrain has not been loaded in the simulator and no claim of working in-game is made.**

## Second integrated validation

The approved follow-up run, its partial provider results, measured 2048 m
horizontal export scale, generated files, and remaining limitations are
documented in [Second integrated geographic validation](./second_geographic_validation.md).

## 9. Files created or modified in this task
Created: `docs/book/validation/run_validation.py`, `measure.py`, this report; generated data under `output/validation/` and `osm2terrn/output/` (stray roads `.tobj`).
Modified: `osm2terrn/data/osm_data_handler.py`, `tests/test_osm_data_handler_cache.py`, `tests/test_street_network_integration.py`, `tests/test_street_cache_process.py`.
At the time of this original report, docs under `docs/book/execution/` and
`progress/` were not updated; the later offline follow-up is recorded below.
