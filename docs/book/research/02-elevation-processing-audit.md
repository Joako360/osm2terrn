# Independent Audit — Chapter 02 Elevation Research

## Audit record

- Target: [`02-elevation-processing-research.md`](02-elevation-processing-research.md)
- Audit date: 2026-11-09.
- Source revision: working tree at HEAD
  `f34a086350934258a73214441bce7020b1b38921`; the repository was already dirty,
  including relevant application files. Findings refer to the inspected
  working tree, not necessarily the committed HEAD snapshot.
- Method: independent static inspection of the preparation report, cited
  implementation, configuration, and test source. No tests, application,
  raster downloads, external services, or terrain generation were run.
- Decision: **REQUIRES CORRECTIONS before using the research report as the sole
  basis for drafting chapter 02.** It is a strong route map and enough to
  prepare a chapter outline, but several corrections and output-contract
  details below should be added first.

The report follows the book's evidence distinctions in many places. A source
path establishes implementation, a test definition establishes a represented
case, and neither alone establishes provider or simulator behavior. This audit
does not approve runtime behavior.

## 1. Executive assessment

The report correctly identifies two separate elevation routes and their main
shared service boundary:

- The heightmap route acquires or reuses a raster array, then normalizes,
  smooths, quantizes/resizes, and saves grayscale/RGB PNG files.
- The road route obtains a DEM for road geometry bounds, retains the affine,
  samples cells, and can fall back to graph-node elevation attributes.
- Both use `load_elevation_raster()` and therefore the same raster cache
  implementation. The heightmap caller goes through
  `fetch_elevation_from_api()` and loses the affine; the road path calls the
  raster loader directly and keeps it. Road heights also subtract the
  heightmap-derived minimum passed by the orchestrator.

The strongest part is the representation handoff analysis. The main weakness
is that the report stops short of some consequences needed to teach the actual
output contract: the precise image/output defaults and names, how the paged
OTC references the PNGs, integer conversion of vertical world size, and the
fact that the project does not define the simulator's pixel-to-height
interpretation. It also labels `nanmin`/`nanmax` extrema as “finite,” which is
incorrect for infinities.

## 2. Findings by severity

| ID | Severity | Target | Finding and source evidence | Required correction to the research report |
|---|---|---|---|---|
| ELEV-AUD-01 | **High** | §5, lines 318–320 | The report calls `np.nanmin`/`np.nanmax` “finite extrema.” Those operations ignore NaN values, but they do not exclude positive or negative infinity. The implementation is at [`terrain_colormap_ops.py::normalize01()`](../../../osm2terrn/processing/terrain/terrain_colormap_ops.py#L11). | Replace “finite extrema” with “NaN-ignoring extrema”; explicitly state that infinities are not filtered and add them to invalid-input test questions. |
| ELEV-AUD-02 | **High** | §§3.2–3.3, lines 120–127, 157–166, 471–474 | The report notes all-nodata and malformed arrays as questions but does not trace the consequence through normalization and output stats. The downloader computes `nanmax`/`nanmin` without an all-invalid guard; normalization then compares `max-min`, divides, and calls `np.nan_to_num`, while the original stats are returned. The exact NumPy warning/error and downstream serialization behavior should not be asserted without a bounded synthetic check. | State the source-level propagation explicitly: there is no all-invalid/finite validation; non-finite stats can remain in the returned stats even if NaN normalized cells become zero. Mark downstream OTC/TERRN2 effects as requiring a synthetic test. Cover empty arrays, all-NaN, infinities, and inconsistent supplied stats. |
| ELEV-AUD-03 | **Medium** | §§3.3–3.4, §§4–5 | The report does not fully specify the emitted output contract. It gives generic “heightmap” and “groundmap” names and 8-bit modes, but omits the actual filename patterns, default dimensions/config values, the paged OTC's exact image/layer references, and that global OTC serializes `WorldSizeY` through `int()`. Source: [`orchestrator.py::_export_heightmap_textures()`](../../../osm2terrn/processing/orchestrator.py#L129), [`otc_paged.py::_render_paged_otc_content()`](../../../osm2terrn/processing/otc/otc_paged.py#L15), [`otc_global.py::_render_global_otc_content()`](../../../osm2terrn/processing/otc/otc_global.py#L14). | Add an output table with exact path patterns, PNG mode/bit depth, default and effective dimensions, `.otc` fields/references, integer `WorldSizeY`, and explicit “simulator interpretation not verified.” |
| ELEV-AUD-04 | **Medium** | §3.5, lines 262–280 | Configuration findings are mostly sound but incomplete for a reader trying to reproduce the effective dimensions and terrain scale. `terrain.page_size` is described as used in orchestrator size calculation without saying that `export_terrain_assets()` only uses that calculation when `terrain_world_size is None`; the normal `dlcity()` route may pass a previously calculated value. The report also lacks the actual default values and does not distinguish image-size defaults from project-config fields. | Add declared defaults and exact consumer/conditional-use columns. Separate `TerrainRuntimeConfig` defaults used by the heightmap function from `TerrainProjectConfig` fields parsed by the CLI but not passed by `_export_heightmap_textures()`. Include the OTC page-size default and water settings. |
| ELEV-AUD-05 | **Medium** | §6 diagram, lines 351–388 | The diagram's provider-failure edge is drawn from the HTTP/decode box only. `load_elevation_raster()` can also raise from cache read/deserialization or cache write; those exceptions are caught by `dlcity()` during preload and by `_prepare_elevation_data()` during its fetch fallback, but the diagram does not show these boundaries. | Add an acquisition/service error edge that includes request, cache, and decode failures and labels the caller-specific handling. Keep the “flat fallback” limited to the later heightmap preparation route. |
| ELEV-AUD-06 | **Medium** | §§3.2, 3.4, 8 | The report correctly says the service does not inspect `dataset.crs`, but the learning consequence should be more explicit: `sample_elevation_at_coords()` takes lon/lat and applies the raster affine without receiving or checking a CRS. The road sampler transforms queries to EPSG:4326. Correct sampling therefore depends on an unverified raster-grid coordinate assumption. | State that the road route can compute plausible-looking but spatially wrong cell indices if raster CRS/affine coordinates are not geographic; confirm the actual provider grid contract with a synthetic raster fixture and, only if authorized, provider evidence. Do not claim the provider's actual CRS from code. |
| ELEV-AUD-07 | **Low** | §3.4 and §4 | The report says the final heightmap image has no pixel-to-coordinate metadata, correctly, but does not show the concrete difference between image resolution and physical world dimensions. The project computes world size in meters from bounds/page size, while image dimensions come from `terrain_runtime.output_size`; these can diverge under configuration. | Add a side-by-side explanation that raster/image dimensions, project page size, OTC page size, and world meters are separate values; do not infer a physical pixel spacing until the active configuration and simulator interpretation are verified. |
| ELEV-AUD-08 | **Low** | §1 and §3.4 | The shared dependency between routes is present but could be easy to miss: route B uses its own road-extent raster, yet its sampled heights subtract the heightmap route's `min_elevation`. A failed heightmap fetch supplies zero stats, which changes the offset used by road processing. | State this shared scalar dependency explicitly, while emphasizing that the road sampler does not reuse the heightmap array or affine. |

## 3. Verification of the two paths

### Route A — heightmap and groundmap

| Stage | Independently verified current source path | Assessment of the research report |
|---|---|---|
| Preload | `cli/commands.py::dlcity()` stores `data["bounds"]`, then calls the imported `fetch_elevation_from_api` wrapper and stores `elevation`, `maxh`, `minh`; caught exception stores `{}`. | Confirmed. The report correctly says preload is unconditional in this function. |
| Raster acquisition | `elevation_service.py::load_elevation_raster()` normalizes bbox, builds AW3D30/GTiff params, checks raster cache, and otherwise calls `requests.get()` at the fixed OpenTopography URL. | Confirmed. No timeout/retry is passed at this request call. The actual remote contract was not checked. |
| Raster reading | `_download_elevation_raster()` reads band 1, compares against `dataset.nodata`, substitutes NaN, computes extrema, and returns array, affine, max, min. | Confirmed. CRS, bounds, mask, pixel size, vertical CRS, and validity are not checked or retained. |
| Loss at preload boundary | `fetch_elevation_from_api()` destructures the raster tuple and discards `_transform`; `MapData.elevation_data` has only the three dictionary values. | Confirmed and pedagogically central. |
| Export re-use/fallback | `orchestrator.py::_export_heightmap_textures()` passes the session dictionary to the heightmap handler. A complete-key dictionary is accepted; otherwise the handler fetches again. A fetch exception creates a zero matrix and status `failed`. | Confirmed, with a caveat: key presence is not data validation. Non-numeric or structurally malformed values can fail outside the fetch-exception handler. |
| Numeric/image work | `_normalize_elevation()` casts to float, min-max normalizes unless range `<= 0`, and maps NaN results to zero. Gaussian filtering precedes output. Grayscale is scaled by 255 and cast to uint8; RGB uses `render_heightmap_rgb()`. Pillow resizes each image with LANCZOS. | Confirmed. No explicit shape/finite/range check or geospatial warp is done. The report should not characterize NaN-ignoring extrema as finite. |
| Statistics/terrain config | Raw `minh`/`maxh`/range/status are returned. The orchestrator uses the raw range for `WorldSizeY`, forwards `min_elevation` to road processing, and forwards stats to TERRN2 water configuration. | Confirmed. The code does not define an inverse pixel-to-meter mapping or prove simulator interpretation. `WorldSizeY` is converted to integer when the global OTC text is rendered. |

### Route B — road elevation sampling

1. `build_roads_from_graph()` converts graph edges to lines, selects a local
   CRS from the origin, transforms geometries, and asks for a road-extent DEM
   sampler plus a graph-node sampler
   ([`road_network_export.py`](../../../osm2terrn/processing/network/road_network_export.py#L91)).
2. `build_dem_sampler()` transforms road geometries to EPSG:4326, takes
   `total_bounds`, calls `load_elevation_raster()`, and retains the returned
   `(array, affine)` pair. It catches any exception and returns `None`
   ([`road_elevation.py`](../../../osm2terrn/processing/roads/road_elevation.py#L15)).
3. `build_node_elevation_sampler()` uses the supplied graph when present,
   requires graph CRS, transforms eligible node coordinates to EPSG:4326, and
   builds a SciPy `cKDTree` from lon/lat pairs when available. The source of
   `elevation`/`elev` attributes is not established by this function
   ([`road_elevation.py`](../../../osm2terrn/processing/roads/road_elevation.py#L37)).
4. `sample_segment_elevation()` converts local XZ road points back to
   EPSG:4326. If a DEM sampler exists, it uses `sample_elevation_at_coords()`;
   an exception returns zero heights immediately. It does **not** then try the
   node sampler. Node fallback is used only when no DEM sampler was built. If
   no node sampler exists or its query raises, zeros are returned
   ([`road_elevation.py`](../../../osm2terrn/processing/roads/road_elevation.py#L86)).
5. Raster samples are selected by `rowcol(..., op=round)` and direct array
   indexing. This is nearest-index/cell sampling; there is no bilinear
   interpolation. Out-of-bounds positions remain NaN in the temporary output
   and are converted to zero. Sampled DEM NaNs also become zero. Infinities are
   not explicitly mapped to zero by the call's `np.nan_to_num()` defaults
   ([`elevation_service.py::sample_elevation_at_coords()`](../../../osm2terrn/processing/terrain/elevation_service.py#L133)).
6. Sampled elevations are offset by the heightmap statistic
   `min_elevation` before road point construction. The DEM sampler uses its
   own road bbox and raster, but the offset comes from route A via the
   orchestrator ([`orchestrator.py::_export_roads()`](../../../osm2terrn/processing/orchestrator.py#L155)).

**Shared state and divergence:** both routes call the same raster loading
service and can reuse the same cache only when their key inputs match. Route A
gets `array + affine + stats` internally, then its convenience wrapper drops
the affine and session metadata does not retain CRS. Route B uses a road-extent
DEM and keeps its affine, but it does not receive route A's array. Its actual
data dependency on route A is the scalar `min_elevation` offset. There is no
evidence that both routes have the same raster extent, resolution, CRS, vertical
datum, or pixel grid.

## 4. Reconstructed equations and units

The project code treats elevation values as meters in log messages, config
names, and downstream calculations, but it does not inspect a vertical CRS or
convert vertical units. Treat “meters” as the code's assumption until dataset
metadata/provider behavior is independently confirmed.

| Operation | Source-level expression | Variables and units | Audit qualification |
|---|---|---|---|
| Bounds to local world size | For geographic bbox, transform four corners to a UTM CRS chosen from center; `side=max(width_m,height_m)`. Optional snap is next power of two with helper bounds. `meters_per_pixel = world_size / max(page_size-1,1)`. | bbox coordinates in geographic degrees; transformed width/height and world size in meters; `page_size` in pixels. | `dlcity()` retains `world_size` and discards the returned meters-per-pixel value. This is not a mapping from DEM pixels to output pixels. |
| Raster sampling | `(row, col)=rowcol(T, lon, lat, op=round)`; `v=elevation[row,col]` if indices are inside array bounds, else initialized NaN then converted to 0. | `lon,lat` are treated as coordinates compatible with affine `T`; row/col are pixel indices; `v` is a raster value treated as meters. | The affine's CRS is absent from this function's inputs. There is no interpolation-weight equation. |
| Height normalization | `n=(h-h_min)/(h_max-h_min)` if range `>0`, else an all-zero array. Then NaNs are mapped to zero by `np.nan_to_num`. | `h`, min and max are raw raster values; `n` is dimensionless. | No clipping to [0,1], no finite check, no consistency check for supplied min/max. |
| Gaussian filtering | `n_s = scipy.ndimage.gaussian_filter(n, sigma)` | `sigma` is in array-index/pixel units, not meters. | Kernel and boundary mode are delegated to SciPy; the project call does not specify additional parameters. |
| Grayscale quantization | `p = (255*n_s).astype(np.uint8)` then Pillow `resize((width,height), LANCZOS)`. | `n_s` dimensionless; `p` nominally 0..255, 8-bit grayscale. | No explicit clamp precedes cast. Pixel values do not carry an elevation unit. LANCZOS operates on image samples after quantization. |
| RGB ground texture | `q=clip((n_s-min(n_s))/(max(n_s)-min(n_s)),0,1)` for nonconstant arrays, then `(cmap(q)[:,:,:3]*255).astype(uint8)`. | normalized color index dimensionless; RGB channels 8-bit. | Code uses `nanmin/nanmax`, which ignore NaN but are not finite-only extrema. Flat arrays map to zero. |
| Vertical world size | If enabled and stats exist: `Y=float(min(max(maxh-minh,Y_min),Y_max))`; OTC text serializes `int(Y)`. Otherwise default Y is used. | Elevation range and limits are treated as meters; emitted `WorldSizeY` is integer. | This is separate from grayscale normalization. No project code defines or verifies the simulator's conversion from PNG pixel to vertical meters. |
| Road relative height | `z_road = sampled_elevation - heightmap_min_elevation`. | Both operands assumed compatible elevation units/datums; output is a relative value used in road geometry. | No vertical-datum compatibility or source equality is checked. |

Do not teach an inverse such as `height = min + pixel/255 * range` as an
implemented equation. It is a possible interpretation of normalized pixels
and world metadata, but this project code does not perform that conversion and
the simulator behavior has not been observed.

## 5. Configuration audit

| Option / declaration | Default and loading/override | Actual inspected consumer | Status |
|---|---|---|---|
| `providers.opentopo_api_key_env_var` | `OPENTOPO_ELEVATION_API_KEY`; `ProjectLoader` loads provider config. | `load_elevation_raster()` reads the named environment variable and passes the value to request params; no presence check before request. | Effective for credential lookup; actual request not run. |
| `providers.elevation_url_template` | Default is an OpenTopoData test-dataset URL; loader supports provider config. | Assigned to `ox.settings.elevation_url_template` in `osm_data_handler.py`. Direct DEM loading instead uses the literal OpenTopography `globaldem` URL. No project call to OSMnx elevation-download helpers was found. | Configured on OSMnx, but no in-project elevation use established; library semantics unverified. |
| `pipeline.preload_elevation` | Default `True`; CLI supports `--pipeline-preload-elevation` and `--pipeline-no-preload-elevation`; project config loader stores it. | `dlcity()` calls its elevation fetcher unconditionally and does not read this value. | Parsed but not effective in the inspected download route. |
| `terrain_runtime.output_size` | Program default `(1025,1025)`, loaded in program config. | Function default argument of `generate_heightmap_n_texture()`; `_export_heightmap_textures()` leaves it implicit. | Effective default for current orchestrator call. |
| `terrain_runtime.default_colormap` | Program default `gist_earth`. | Function default passed to groundmap renderer. | Effective default. |
| `terrain_runtime.smoothing_sigma` | Program default `1.0`. | Function default passed to Gaussian filter. | Effective default. |
| Project `terrain.output_size` | Project default `(1025,1025)`; loader/validator and CLI width/height flags support it. | Not passed by `_export_heightmap_textures()` to heightmap generation. | Parsed/validated but no use found in inspected export route. |
| Project `terrain.colormap` / `terrain.smoothing_sigma` | Defaults `gist_earth` / `1.0`; loader and CLI overrides exist. | Not passed by the orchestrator call to heightmap generation. | Parsed but not effective in inspected route. |
| Project `terrain.page_size` | Default `1025`; loader and CLI override exist. | Used by `dlcity()` to calculate world bounds; orchestrator uses it if no `terrain_world_size` was passed. | Effective conditionally; this is not the PNG output size. |
| `elevation_runtime.enable_realistic_elevation` | Default `True`. | `calculate_world_size_y()` only. Does not gate DEM acquisition or image normalization in inspected route. | Effective only for vertical world-size metadata. |
| `elevation_runtime.default_world_size_y`, `min_world_size_y`, `max_world_size_y` | Defaults 300, 50, and 10000 (code labels meters); min/max validated positive and ordered. | `calculate_world_size_y()`. Its float result is serialized as integer by global OTC renderer. | Effective for Y metadata. |
| `elevation_runtime.normalization_tolerance` | Default `0.1`; loader and validator accept it. | No processing consumer found in source search. | Parsed/validated, apparently unused in this route. |
| `otc_runtime.default_page_size` | Default `1025`. | Default argument of `export_global_otc()`; orchestrator does not pass `page_size`. | Effective OTC page size, separate from `terrain.page_size` and `output_size`. |
| `water_runtime.enable_realistic_water`, depth/default lines | Default realistic water enabled; default water depth 150, configured defaults also present. | `prepare_water_config()` derives water line from `min_elevation` and bottom line by subtracting depth when stats exist. | Effective for TERRN2 metadata; no simulator interpretation verified. |
| Cache enabled/root/size | Program cache settings; `get_cache_manager()` supplies file cache. | DEM cache and smoothed-array cache. | Effective cache infrastructure; failure and invalidation behavior requires targeted verification. |

The project and program configs must not be conflated: the current orchestrator
call uses the `terrain_runtime` defaults for image generation, while several
project `terrain.*` settings are only loaded/validated and are not forwarded
to that call. Relevant declarations/consumers are in
[`config/models.py`](../../../osm2terrn/config/models.py#L40),
[`config/defaults.py`](../../../osm2terrn/config/defaults.py#L97),
[`config/loader.py`](../../../osm2terrn/config/loader.py#L448),
[`app/main.py::_build_project_cli_overrides()`](../../../osm2terrn/app/main.py#L73),
[`heightmap_handler.py::generate_heightmap_n_texture()`](../../../osm2terrn/processing/terrain/heightmap_handler.py#L112),
[`orchestrator.py::_export_heightmap_textures()`](../../../osm2terrn/processing/orchestrator.py#L129), and
[`elevation_scaling.py::calculate_world_size_y()`](../../../osm2terrn/processing/terrain/elevation_scaling.py#L14).

## 6. Inputs, transformations, and outputs

| Artifact/stage | Type, format, dimensions | Values/units and retained metadata | Source and audit note |
|---|---|---|---|
| Provider response | In-memory response body opened by Rasterio as GeoTIFF; no `.tif` saved by this service. | Band 1 dtype comes from provider dataset; `dataset.transform` retained in loader result; dataset CRS, bounds, masks, vertical CRS are discarded. | [`elevation_service.py::_download_elevation_raster()`](../../../osm2terrn/processing/terrain/elevation_service.py#L53). Provider response details not observed. |
| DEM array/cache object | NumPy 2D array, one band; tuple includes affine and scalar stats. | Nodata equality becomes NaN if metadata supplied; extrema are floats; units/datum are assumed rather than checked. | `load_elevation_raster()`, Pickle cache namespace `providers/elevation/raster`. |
| Session handoff | Python dictionary `{elevation, maxh, minh}` or `{}`. | No CRS/affine/source identifier; successful preload drops affine. | [`cli/commands.py::dlcity()`](../../../osm2terrn/cli/commands.py#L70). |
| Heightmap | `<prefix>_heightmap.png`, Pillow `L` mode, 8 bits per pixel, final dimensions from `terrain_runtime.output_size` (default 1025×1025). | Nominal grayscale 0–255 from normalized/smoothed data; no meter units or georeferencing in PNG creation code. | [`orchestrator.py::_export_heightmap_textures()`](../../../osm2terrn/processing/orchestrator.py#L129), [`heightmap_handler.py::_save_map_image()`](../../../osm2terrn/processing/terrain/heightmap_handler.py#L69). |
| Ground texture | `<prefix>_groundmap.png`, Pillow `RGB`, 8 bits/channel, same configured final dimensions. | Colormap display only; color values are not raw elevations. No CRS/georeferencing written. | `render_heightmap_rgb()`; paged OTC references it as diffuse/base and blend imagery. |
| Paged OTC | `<prefix>-page-0-0.otc`, text. | First line is heightmap PNG basename; following records describe groundmap/detail layers using configured texture scales. | [`otc_paged.py::_render_paged_otc_content()`](../../../osm2terrn/processing/otc/otc_paged.py#L15). The simulator's interpretation is not established by source inspection. |
| Global OTC | `<prefix>.otc`, text. | Emits integer `WorldSizeX`, `WorldSizeZ`, `WorldSizeY`, `PageSize`, `PageFileFormat`; no raw heightmap descriptor is passed by current orchestrator. | [`orchestrator.py::export_terrain_assets()`](../../../osm2terrn/processing/orchestrator.py#L356), [`otc_global.py::_render_global_otc_content()`](../../../osm2terrn/processing/otc/otc_global.py#L14). |
| TERRN2 | `<prefix>.terrn2`, text. | Receives elevation stats to derive water metadata; no raster data embedded. | [`terrn2_entrypoint.py::export_terrn2_entrypoint()`](../../../osm2terrn/processing/terrain/terrn2_entrypoint.py#L102), [`terrn2_water.py::prepare_water_config()`](../../../osm2terrn/processing/terrain/terrn2_water.py#L15). |
| Road TOBJ | `<prefix>_roads.tobj` naming is selected by road exporter configuration; text/object records contain oriented points. | Road point elevations are sampled minus heightmap minimum; exact vertical datum and RoR interpretation are not validated. | [`road_network_export.py::build_roads_from_graph()`](../../../osm2terrn/processing/network/road_network_export.py#L71), [`road_model.py::Road.to_tobj_string()`](../../../osm2terrn/processing/roads/road_model.py#L64). |

`WorldSizeY` is not identical to the matrix's meter range: a raw float range is
clamped, then converted to integer text. The code emits 8-bit image samples
and terrain metadata, but no project function converts each grayscale pixel
back to a physical elevation. Do not assert that Rigs of Rods applies a
specific linear mapping unless a separately recorded simulator check proves
it. The `WorldSizeY`, `PageSize`, image dimensions, selected geographic bounds,
and `meters_per_pixel` estimate are different values and are not reconciled in
the current output path.

## 7. Assertion-by-assertion disposition

| Preparation report area | Disposition | Independent evidence / caveat |
|---|---|---|
| §1 two-route scope | **Confirmed** | CLI heightmap path and road graph path are distinct; both use the raster service/cache, with only the road path consuming affine for coordinate sampling. |
| §2 module map | **Mostly confirmed** | Listed modules/symbols exist and participate as described. Add `road_model.py`, exact output path naming, and page OTC rendering when drafting the final chapter. |
| §3.1 CLI/session route | **Confirmed** | `dlcity()` preloads after storing session state. `pipeline.preload_elevation` is not read by that function. |
| §3.2 service/cache | **Confirmed with limits** | Request, returned tuple, key inputs and dropped metadata match code. Provider response contract and raster CRS remain unknown. Diagram/report should include cache failures in the caller error boundary. |
| §3.3 heightmap path | **Partially confirmed** | Transform loss, normalization, smoothing, image conversion and fallback are correctly described. “Available” does not imply shape/finite/stat validation; the report needs a clearer invalid-data consequence. |
| §3.4 outputs and road sampler | **Partially confirmed** | Flow is substantially correct. Exact output links, integer `WorldSizeY`, sampler priority, no node retry after DEM-sampling exception, and simulator contract need clearer treatment. |
| §3.5 configuration | **Mostly confirmed** | Disconnected project settings and preload flag are identified. Qualify `terrain.page_size` use as conditional; include values and water/OTC settings. |
| §4 structures | **Confirmed but incomplete** | Representations/loss points are accurately identified; output dimensions, defaults, exact serialized fields, raster dtype and unit assumptions are missing. |
| §5 formulas | **One inaccurate phrase; otherwise mostly confirmed** | `nanmin`/`nanmax` are not finite-only. Need explicit no-clip/no-finite-validation note and integer cast for `WorldSizeY`. |
| §6 diagram | **Partially confirmed** | Main order and separate road path match. Cache-operation errors and the projection/service call's broader exception boundary are omitted. It remains unparsed/unrendered, as disclosed. |
| §7 tests | **Confirmed as test-source descriptions** | The named tests contain the described mocks/assertions. None was executed during this audit. |
| §8 questions | **Confirmed and useful** | CRS, configuration, data validity, cache, road datum and simulator questions are well chosen; several should be elevated into the final chapter's explicit evidence limits. |
| §§9–10 outline/handoff | **Suitable with changes** | Good teaching sequence, but add output/config tables and a clear separation of pixel visualization from simulator height interpretation. |

## 8. Proposed static route maps

### Heightmap/groundmap path

```text
CLI dlcity
  -> OSM bundle bounds
  -> world-size estimate and optional square bounds
  -> current_map state
  -> unconditional fetch_elevation_from_api
  -> load_elevation_raster
       -> bbox normalize/reproject attempt
       -> raster cache lookup OR HTTP GET + GeoTIFF band read + cache write
       -> array + affine + raw min/max
  -> fetch wrapper discards affine
  -> session dict (array, maxh, minh) OR empty dict on caught preload exception
  -> CLI export -> orchestrator -> generate_heightmap_n_texture
       -> use dict if keys present OR fetch again
       -> fetch failure -> flat zero array/status failed
       -> min/max normalize -> Gaussian filter
       -> cache smoothed matrix only if original elevation_data is None
       -> grayscale uint8 + RGB colormap -> Pillow LANCZOS resize -> PNGs
       -> return raw stats/status -> WorldSizeY, roads offset, TERRN2 water
```

### Road sampling path

```text
orchestrator heightmap stats (min_elevation)
  -> road export only when enabled and street status available
  -> graph edges -> local projected road geometries
  -> separate road-bounds DEM load -> array + affine, or None on setup/load error
  -> also try node sampler from graph attributes (CRS -> EPSG:4326)
  -> local XZ points -> EPSG:4326
       -> if DEM sampler exists: affine row/col round -> array cell -> subtract heightmap min
             sampling exception -> zeros (does not then try node sampler)
       -> else node sampler exists: nearest lon/lat node -> subtract heightmap min
             exception/no sampler -> zeros
  -> oriented road points -> road object -> TOBJ output
```

The two routes share a loader/cache implementation, not necessarily a raster
instance or bbox. Only the scalar heightmap minimum is handed from route A to
route B. These are static call/data paths, not observed execution.

## 9. Questions requiring execution or external evidence

- What CRS, affine coordinate space, resolution, nodata mask, dimensions, and
  vertical units does the configured provider actually return for representative
  areas? Code does not record these facts.
- Do request failures, missing keys, cache corruption, and all-nodata responses
  produce the exact caller outcomes predicted by static exception paths?
- How do Pillow/SciPy versions encode invalid/infinite/empty arrays in PNGs?
  Use synthetic local arrays and temporary files; do not use a live provider.
- Does an 8-bit grayscale PNG in the emitted paged/global OTC configuration
  produce the expected vertical terrain in the target Rigs of Rods version?
  This requires an authorized local simulator integration check.
- Do real road graph node `elevation`/`elev` fields exist and represent units
  and datums compatible with the separate DEM and heightmap minimum?
- Does a project config/CLI override for `terrain.output_size`, `colormap`,
  `smoothing_sigma`, or `pipeline.preload_elevation` affect the application
  route? Static inspection shows they are not passed/read at the described
  consumer; a focused mocked integration check can confirm user-facing effect.

No such check was run for this audit. Existing test source can guide synthetic
cases, but test references are not results.

## 10. Final chapter scope and section plan

The scope should cover both elevation consumers and their shared service, but
not claim to document OSMnx's internal elevation service or Rigs of Rods' image
decoding without separate evidence. Recommended sections:

1. Scope, learning goals, and two-route overview.
2. Concepts: raster band, affine transform, CRS, nodata, pixel indices,
   vertical units/datum, and distinction between a DEM and an image texture.
3. CLI bounds preparation, preload state, and service/cache contract.
4. Raster reading, metadata discarded, nodata/extrema behavior, and exception
   boundaries.
5. Heightmap array normalization, flat fallback, Gaussian filtering, uint8
   encoding, and image-space LANCZOS resize.
6. Separate road sampling branch: road bbox, affine cell selection, node
   fallback priority, zero behavior, and the shared minimum-elevation offset.
7. Configuration table with effective versus parsed-but-unused fields.
8. Output contract table and handoff to OTC/TERRN2/road TOBJ; explicitly mark
   simulator interpretation as unverified.
9. Source-backed diagram, synthetic numeric examples, exercises/answer
   guides, claims/evidence, and open questions.

Suggested files/symbols for the author to study:

- `osm2terrn/cli/commands.py::dlcity()` and `::export()`.
- `osm2terrn/app/app_state.py::MapData`.
- `osm2terrn/processing/terrain/elevation_service.py::_normalize_bbox_for_api()`,
  `_build_elevation_api_params()`, `_download_elevation_raster()`,
  `load_elevation_raster()`, `fetch_elevation_from_api()`,
  `sample_elevation_at_coords()`.
- `osm2terrn/processing/terrain/heightmap_handler.py::_normalize_elevation()`,
  `_build_flat_elevation()`, `_prepare_elevation_data()`, `_save_map_image()`,
  `generate_heightmap_n_texture()`.
- `osm2terrn/processing/terrain/terrain_colormap_ops.py::normalize01()`,
  `render_heightmap_rgb()`, `resolve_ground_colormap()`.
- `osm2terrn/processing/roads/road_elevation.py::build_dem_sampler()`,
  `build_node_elevation_sampler()`, `sample_segment_elevation()`.
- `osm2terrn/processing/network/road_network_export.py::build_roads_from_graph()`;
  `osm2terrn/processing/roads/road_model.py::Road.to_tobj_string()`.
- `osm2terrn/processing/orchestrator.py::_export_heightmap_textures()`,
  `_export_roads()`, `export_terrain_assets()`.
- `osm2terrn/processing/terrain/elevation_scaling.py::calculate_world_size_y()`;
  `processing/otc/otc_paged.py::_render_paged_otc_content()`;
  `processing/otc/otc_global.py::_render_global_otc_content()`;
  `processing/terrain/terrn2_water.py::prepare_water_config()`;
  `processing/terrain/terrn2_entrypoint.py::export_terrn2_entrypoint()`.
- `osm2terrn/config/models.py`, `defaults.py`, `loader.py`, `validator.py`,
  `app/main.py::_build_project_cli_overrides()`.
- Test-source references only: `tests/test_elevation_cache.py`,
  `tests/test_heightmap_cache.py`, `tests/test_pipeline_domain_state.py`, and
  `tests/test_street_network_handoff.py`.

## 11. Audit verification and limitations

- Source paths, symbols, and cited line locators were checked against the
  inspected working tree while preparing this audit.
- No application or test command was run; no provider or simulator behavior is
  asserted as verified.
- Mermaid syntax was reviewed by inspection only; no parser/renderer was run.
- The target report and relevant application files were already untracked or
  locally modified at audit start. No pre-existing files were overwritten;
  this audit adds only this audit report.
