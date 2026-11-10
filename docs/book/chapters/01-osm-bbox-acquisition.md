# OSM Bounding-Box Acquisition and Layer Results

## Metadata

- ID: `chapter:osm-bbox-acquisition`
- `inventory_status`: `inventoried`
- `analysis_status`: `static_analyzed`
- `documentation_status`: `draft`
- `execution_status`: `not_verified`
- Inspected revision/date: `f34a086350934258a73214441bce7020b1b38921`; 2026-11-09 working tree
- Author: Copilot
- Reviewer: pending
- Related inventory scope:
  - `file:osm2terrn/cli/commands.py`
  - `py:osm2terrn/cli/commands.py::dlcity`
  - `file:osm2terrn/cli/menu.py`
  - `file:osm2terrn/data/download_menu.py`
  - `py:osm2terrn/data/osm_data_handler.py::download_menu`
  - `py:osm2terrn/domain/value_objects/__init__.py::BoundingBox`
  - `py:osm2terrn/domain/adapters/bounds.py::require_domain_bounding_box`
  - `file:osm2terrn/data/osm_data_handler.py`
  - `py:osm2terrn/data/osm_data_handler.py::_bbox_to_osmnx_tuple`
  - `py:osm2terrn/data/osm_data_handler.py::_layer_cache_key`
  - `py:osm2terrn/data/osm_data_handler.py::_get_cached_layer`
  - `py:osm2terrn/data/osm_data_handler.py::_cache_layer`
  - `py:osm2terrn/data/osm_data_handler.py::download_data_from_bbox`
  - `py:osm2terrn/data/osm_data_handler.py::_layer_failure`
  - `py:osm2terrn/data/osm_data_handler.py::_query_osm_layer`
  - `file:osm2terrn/data/acquisition.py`
  - `py:osm2terrn/data/acquisition.py::LayerAcquisitionResult`
  - `file:osm2terrn/data/street_network.py`
  - `py:osm2terrn/data/street_network.py::StreetNetworkResult`
  - `file:osm2terrn/data/overpass.py`
  - `py:osm2terrn/data/overpass.py::call_with_retries`
  - `file:osm2terrn/adapters/coordinate_transform.py`
  - `py:osm2terrn/adapters/coordinate_transform.py::transform_gdf_to_ror`
  - `py:osm2terrn/adapters/coordinate_transform.py::transform_graph_to_ror`
  - `py:osm2terrn/utils/geometry/crs.py::local_crs_from_lonlat`

## Purpose and scope

This pilot follows the source-defined CLI route from a selected bounding box
through OSM layer queries, result states, per-layer caching, and the bounded
Overpass request wrapper. It is intentionally limited to acquisition: it does
not explain elevation, terrain generation, road geometry processing, or
export.

The topic is a useful first chapter because it has a concrete caller, explicit
result models, separate geometry/network loops, cache logic, and mock-based
test source. This document reports static source facts. The application, OSM
acquisition tests, and external services were not run for this chapter.

### Learning goals

After studying this chapter, a reader should be able to:

- Explain the bbox tuple order and the conversion to the coordinate order
  expected by OSMnx.
- Distinguish a layer that was not requested, one that returned no features,
  one that returned data, and one that failed.
- Trace why successful layers can be reused even when another layer failed.
- Describe the configured retry limits and the evidence boundary of the tests.

### Prerequisites

- Basic Python functions, exceptions, dictionaries, and dataclasses.
- A basic understanding of longitude/latitude coordinates and HTTP status codes.
- Familiarity with the difference between vector geometries and graph networks.

### Files to study

- [`osm2terrn/cli/commands.py`](../../../osm2terrn/cli/commands.py) —
  `dlcity()`, the download callback and current caller of the bbox downloader;
  it also stores the returned bundle and then attempts elevation preloading.
- [`osm2terrn/cli/menu.py`](../../../osm2terrn/cli/menu.py) —
  registers `dlcity()` as the download action.
- [`osm2terrn/data/download_menu.py`](../../../osm2terrn/data/download_menu.py) —
  produces the selected place and bbox; manual bbox selection has separate
  place-label semantics.
- [`osm2terrn/domain/value_objects/__init__.py`](../../../osm2terrn/domain/value_objects/__init__.py) —
  defines `BoundingBox` and its coordinate validation.
- [`osm2terrn/domain/adapters/bounds.py`](../../../osm2terrn/domain/adapters/bounds.py) —
  converts accepted input shapes to the domain bbox.
- [`osm2terrn/data/osm_data_handler.py`](../../../osm2terrn/data/osm_data_handler.py) —
  bbox normalization, per-layer acquisition, and cache read/write decisions.
- [`osm2terrn/adapters/coordinate_transform.py`](../../../osm2terrn/adapters/coordinate_transform.py) —
  projects acquired GeoDataFrames and graphs to the local Rigs of Rods CRS.
- [`osm2terrn/data/acquisition.py`](../../../osm2terrn/data/acquisition.py) —
  status model for configured geometry and non-road network layers.
- [`osm2terrn/data/street_network.py`](../../../osm2terrn/data/street_network.py) —
  separate status contract for roads.
- [`osm2terrn/data/overpass.py`](../../../osm2terrn/data/overpass.py) —
  HTTP scoping and retry policy.
- [`osm2terrn/config/models.py`](../../../osm2terrn/config/models.py),
  [`osm2terrn/config/loader.py`](../../../osm2terrn/config/loader.py), and
  [`osm2terrn/config/defaults.py`](../../../osm2terrn/config/defaults.py) —
  retry and layer defaults.
- [`tests/test_osm_data_handler_cache.py`](../../../tests/test_osm_data_handler_cache.py)
  and [`tests/test_overpass_retry.py`](../../../tests/test_overpass_retry.py) —
  synthetic test cases. They were inspected but not run here.

## Evidence-based explanation

### Concepts used in this chapter

A **bounding box (bbox)** describes a rectangular area with west, south, east,
and north edges. In this code path, geographic coordinates are longitude and
latitude in EPSG:4326. OSMnx's bbox functions receive the order
`(west, south, east, north)`.

`BoundingBox` stores the limits as `min_x`, `min_y`, `max_x`, and `max_y`;
its `west`, `south`, `east`, and `north` properties are aliases. Construction
checks that all values are finite and each minimum is smaller than its
maximum. It does not check geographic longitude/latitude ranges or parse the
CRS string at construction. `crs` is optional metadata; `is_projected` does
not transform coordinates or validate the CRS.

The bounds adapter accepts several input shapes. A four-item tuple/list
becomes a `BoundingBox` without a CRS. `reproject()` treats a missing CRS as
EPSG:4326, but `_bbox_to_osmnx_tuple()` skips reprojection when `crs` is
missing. Thus tuple coordinates pass through unchanged under the handler's
geographic-input convention. That convention does not mean the CRS was
discovered from the numbers.

A **layer** is one configured query result, such as a geometry collection or a
network graph. A **cache hit** reuses a prior successful layer result instead
of querying the provider. An **empty result** is a successful query with no
features; it is not the same state as a failed request.

**CRS** means coordinate reference system: it identifies how coordinate
numbers map to a position on Earth. `transform_gdf_to_ror()` and
`transform_graph_to_ror()` call `local_crs_from_lonlat()`, which builds an
azimuthal equidistant CRS centered at the bbox origin, using the WGS84
ellipsoid and metres. The project then transforms coordinate values into that
CRS; it does not merely relabel the source coordinates.

The default configuration defines geometry queries for buildings, parks, and
lakes, and network queries for roads and rails in
[`build_default_program_config()`](../../../osm2terrn/config/defaults.py#L46).
The handler iterates the configured mappings; it does not hard-code those five
names in the acquisition loops.

## Route from the CLI to acquisition

The menu registers `dlcity()` as its download callback. `dlcity()` calls
`download_menu()`, which delegates to `DownloadMenu.show_main_menu()` and
receives `(place, bbox)`. If either value is falsy, the callback returns
before calling the downloader. Otherwise it invokes
`download_data_from_bbox(bbox)`.

The two menu modes do not currently reach that callback guard in the same way.
Place search returns a non-empty city name with its bbox. The manual mode calls
[`get_custom_bbox()`](../../../osm2terrn/data/download_menu.py#L56) and returns
`("", bbox)`; because the place is empty, the
[`dlcity()` guard](../../../osm2terrn/cli/commands.py#L27) returns without
calling the downloader. This is the behavior established by the current
source, not an execution uncertainty. The separate design question is whether
rejecting a manually entered bbox is intentional or a defect.

The downloader's return is not the end of `dlcity()`. The callback checks the
returned bounds, stores the bundle and session metadata in `current_map`,
computes square terrain bounds, and then attempts elevation preloading. That
elevation step is outside this acquisition chapter; it is shown to mark the
handoff boundary. If preloading raises, `dlcity()` catches the exception and
leaves the elevation state empty. Whether the current manual-bbox rejection is
intentional, how the preload setting should behave, and what state should
remain after cancellation are still open design questions; this source trace
establishes no product intent or interactive execution.

### Claim: The CLI passes a selected bbox to the OSM downloader

- Claim ID: `claim:osm-bbox-acquisition:bbox-and-query-route`
- Classification: `fact`
- Evidence IDs: `ev:osm-acquisition-cli-route`, `ev:osm-acquisition-bbox-normalization`
- Code locator: `osm2terrn/cli/commands.py::dlcity()` and `osm2terrn/data/osm_data_handler.py::download_data_from_bbox()` (lines 21, 259)
- Limits or uncertainty: This describes the current source route, not a recorded interactive execution.

In the current CLI source, [`dlcity()`](../../../osm2terrn/cli/commands.py#L21)
returns early unless both a place value and bbox are present. Otherwise it calls
[`download_data_from_bbox()`](../../../osm2terrn/data/osm_data_handler.py#L259).
That function adapts the input to the domain `BoundingBox`, attempts to
reproject explicitly labelled non-EPSG:4326 bounds, and uses
[`_bbox_to_osmnx_tuple()`](../../../osm2terrn/data/osm_data_handler.py#L69) to
produce the `(west, south, east, north)` tuple. The returned bundle also
contains bounds and origin coordinates.

The current manual route does not proceed: its empty place label fails the
`dlcity()` guard. The product decision about whether that rejection is
intentional remains open. Keep
`question:stage3-bbox-place-semantics` open in
[`open_questions.md`](../questions/open_questions.md).

### Bbox validation, CRS, and request coordinates

Keep these operations distinct:

1. `require_domain_bounding_box()` converts supported tuple/list, mapping,
   bounds-like, and domain-object inputs. `BoundingBox._validate()` checks
   finite numbers and strictly increasing x/y limits. It does not check that
   geographic coordinates are within longitude/latitude ranges.
   If the input is already a `BoundingBox`, the adapter returns that object
   directly; it does not rerun `_validate()`. A copied `BoundingBox` also
   returns from its copy constructor before validation. The validation claim
   therefore applies to newly constructed/coerced values, not to every
   possible existing mutable instance.
2. A supplied CRS is metadata. Tuple/list input creates a bbox with no CRS;
   the acquisition handler assumes those coordinates are geographic. Missing
   CRS is not evidence that the values are EPSG:4326.
3. If `bbox_obj.crs` is present and differs from the literal
   `"EPSG:4326"`, `download_data_from_bbox()` tries
   `reproject("EPSG:4326")`. If it raises, the handler logs a warning that it
   will try the original bounds and keeps `use_bbox` pointing to that input.
4. The bundle-cache key and cache lookup occur before the later call to
   `_bbox_to_osmnx_tuple()`. On a cache miss, that helper tries reprojection
   again for a non-EPSG:4326 CRS. If it also raises, the exception occurs
   before either per-layer loop and is not converted into a
   `LayerAcquisitionResult(status="failed")`. A valid bundle-cache hit may
   return before this second attempt. The warning fallback therefore does not
   establish successful recovery, and CRS errors do not all become a
   controlled failed layer.
5. After successful conversion, OSMnx receives the tuple
   `(west, south, east, north)`. This reorders names into the called API's
   contract; it is not itself a coordinate transformation.

[`BoundingBox.reproject()`](../../../osm2terrn/domain/value_objects/__init__.py#L192)
transforms only the four corner coordinates. It then uses the smallest and
largest transformed x/y values to construct a new axis-aligned rectangle. It
does not densify the edges or transform points between the corners. For a
nonlinear CRS transformation, the returned rectangle therefore is not
guaranteed to enclose the exact transformed boundary at every point; the
implementation is a four-corner envelope, not a complete transformation of
the bbox boundary.

For a synthetic geographic example,
`BoundingBox(-58.40, -34.62, -58.35, -34.58, crs="EPSG:4326")` stores
`min_x=-58.40`, `min_y=-34.62`, `max_x=-58.35`, and `max_y=-34.58`. Both
`to_tuple()` and the OSMnx request tuple are
`(-58.40, -34.62, -58.35, -34.58)`. Without a CRS, the same numbers pass
through `_bbox_to_osmnx_tuple()` unchanged, under the caller's geographic
convention. If projected values such as
`(350000, 6150000, 355000, 6155000)` are labelled `EPSG:32721`, the handler
must transform them before they can be used as an OSMnx geographic bbox. This
chapter makes no claim about the transformed numeric result.

### Claim: Geometry, non-road network, and road results have explicit states

- Claim ID: `claim:osm-bbox-acquisition:layer-outcome-contract`
- Classification: `fact`
- Evidence IDs: `ev:osm-acquisition-layer-results`, `ev:osm-acquisition-query-loops`
- Code locator: `osm2terrn/data/acquisition.py::LayerAcquisitionResult`, `osm2terrn/data/street_network.py::StreetNetworkResult`, and `osm2terrn/data/osm_data_handler.py::download_data_from_bbox()` (lines 15, 23, 259)
- Limits or uncertainty: A configured status contract does not prove how a live provider will respond.

The handler processes configured geometry and network mappings in separate
loops. Each query is wrapped in its own exception handling, so one layer's
failure does not immediately stop the next loop iteration. Geometry and
non-road network results are recorded in `acquisition_results`.

The geometry loop uses `ox.features_from_bbox()` with each configured tag
mapping. The network loop uses `ox.graph_from_bbox()` with
`network_type="drive"`, `simplify=False`, `retain_all=True`, and the configured
custom filter. In the defaults, the rails filter selects rail and tram
features; this describes the arguments passed by the current code, not a
judgment about whether they are the intended product settings.

[`LayerAcquisitionResult`](../../../osm2terrn/data/acquisition.py#L15)
distinguishes `not_requested`, `empty`, `available`, and `failed`; a failure
also records a category, stage, and diagnostic. Roads use the separate
[`StreetNetworkResult`](../../../osm2terrn/data/street_network.py#L23), whose
contract additionally has a `missing` state. In this bbox handler, an
unconfigured road layer is returned as `not_requested`
([default branch](../../../osm2terrn/data/osm_data_handler.py#L559)); a graph with no nodes
is `empty` without a graph. A nodes-only graph becomes `empty` and is retained
only if graph transformation and final CRS validation succeed
([handler branch](../../../osm2terrn/data/osm_data_handler.py#L481)). A
transformed graph with at least one edge is `available`; query or graph-
transformation failures are `failed`
([outer handler](../../../osm2terrn/data/osm_data_handler.py#L536)).

For geometry queries, `None` or an empty GeoDataFrame is an `empty` result.
OSMnx's specific “no matching features” error is also treated as empty.
Other acquisition exceptions become `failed`, with an HTTP status used to
classify temporary versus permanent HTTP failures where available. A geometry
or non-road network transformation exception is recorded as a
transformation-stage failure, not as a successful empty result. Road query
and graph-transformation exceptions reach the same outer handler and are
classified with stage `acquisition`; the road diagnostic groups both causes.
The classifier is
[`_layer_failure()`](../../../osm2terrn/data/osm_data_handler.py#L91).

### What is stored for each acquired layer

The value returned by OSMnx is not always the value stored in the bundle:

| Configured layer | OSMnx result | Project transformation | Bundle value/status |
|---|---|---|---|
| Geometry (`buildings`, `parks`, `lakes` by default) | GeoDataFrame | `transform_gdf_to_ror()` requires a source CRS and calls `to_crs()` to the origin-centred local Rigs of Rods CRS. | Transformed GeoDataFrame, or `None` for empty/failed. Status is recorded in `acquisition_results`; the transformed value is what the per-layer cache stores. |
| Non-road network (`rails` by default) | NetworkX `MultiDiGraph` | `transform_graph_to_ror()` copies the graph, transforms node coordinates and edge geometries when present, then sets the target CRS metadata. | Transformed graph, or `None` for empty/failed. Status is in `acquisition_results`. |
| Roads | NetworkX `MultiDiGraph` | The same graph transformation is applied. A graph with at least one edge is `available`; a nodes-only graph becomes `empty` and may be retained only after transformation and CRS validation succeed. | `StreetNetworkResult` under `bundle["roads"]`, with graph, CRS, source, status and diagnostic as applicable. Roads are not stored in `acquisition_results`. |

`transform_graph()` raises if the graph has no nodes or no source graph CRS,
and checks that every node has x/y coordinates. Geometry transformation
raises when the GeoDataFrame has no CRS. Geometry and non-road network
transformation exceptions are recorded with stage `transformation`. Road
query and graph-transformation exceptions share an outer handler and are
recorded as stage `acquisition`; its diagnostic groups acquisition and CRS
transformation. These are code-level classifications, not observed provider
failures.

The return dictionary also carries geographic `bounds`, center
`origin_lon`/`origin_lat`, and `x_0`/`y_0` set to `0.0`. The function
docstring describes x/y as the centroid of projected bounds, but the
implementation sets them to zero; the geographic center is stored in
`origin_lon`/`origin_lat`.

### Following one geometry-layer branch

The following is a brief verbatim excerpt from
[`download_data_from_bbox()`](../../../osm2terrn/data/osm_data_handler.py#L412):

```python
if gdf is None or gdf.empty:
    d[typ] = None
    acquisition_results[typ] = LayerAcquisitionResult(status="empty")
    _cache_layer(
        cache_manager,
        key=layer_key,
        layer=typ,
        layer_type="geometry",
        data=None,
        result=acquisition_results[typ],
    )
else:
    try:
        d[typ] = transform_gdf_to_ror(gdf, origin_lon, origin_lat)
        acquisition_results[typ] = LayerAcquisitionResult(status="available")
        _cache_layer(
            cache_manager,
            key=layer_key,
            layer=typ,
            layer_type="geometry",
            data=d[typ],
            result=acquisition_results[typ],
        )
    except Exception as exc:
        result = _layer_failure(exc, stage="transformation")
        acquisition_results[typ] = result
        d[typ] = None
        log_warning(
            logger,
            f"Could not transform geometry layer {typ}: {result.diagnostic}.",
        )
```

Here `gdf` is the value returned by the OSMnx geometry query, and `typ` is the
configured layer name. If the query returned no frame or an empty frame, the
bundle stores `None`, records an `empty` result, and attempts to cache that
successful empty outcome. Otherwise, the GeoDataFrame is projected around the
selected origin and stored under `d[typ]`; its status becomes `available`.
The following code caches the transformed frame. If transformation raises,
the surrounding handler records a transformation-stage `failed` result and
continues to the next configured layer. This is source code, not pseudocode or
a captured run.

### A synthetic acquisition bundle

The structure below is conceptual. It illustrates source-defined keys and
object types; it was not captured from an application run. The configured
layer names and combination of outcomes are illustrative.

```text
{
    "bounds": BoundingBox(
        -58.40, -34.62, -58.35, -34.58,
        crs="EPSG:4326",
        is_projected=False,
    ),
    "origin_lon": -58.375,
    "origin_lat": -34.60,
    "x_0": 0.0,
    "y_0": 0.0,
    "buildings": GeoDataFrame(...),
    "parks": None,
    "rails": None,
    "roads": StreetNetworkResult(
        status="available",
        graph=MultiDiGraph(...),
        graph_crs="<normalized local CRS string>",
        source="query",
        diagnostic=None,
    ),
    "acquisition_results": {
        "buildings": LayerAcquisitionResult(status="available", source="query"),
        "parks": LayerAcquisitionResult(status="empty", source="query"),
        "rails": LayerAcquisitionResult(
            status="failed",
            source="query",
            failure_category="unknown",
            failure_stage="transformation",
            diagnostic="ValueError",
        ),
    },
}
```

`bounds` is the geographic domain `BoundingBox`; the origin values are its
geographic center, while `x_0` and `y_0` are currently zero. Geometry entries
hold transformed GeoDataFrames or `None`; their states are recorded separately
in `acquisition_results`. These layer states may be `not_requested`, `empty`,
`available`, or `failed`. Non-road network entries hold transformed graphs or
`None` and use the same result map. Roads are different: `bundle["roads"]` is a
`StreetNetworkResult`, not a bare graph, and roads are excluded from
`acquisition_results`. The wrapper carries status and source, and, when a
graph is present, its graph CRS; a failed result carries a diagnostic. Its
contract permits `not_requested`, `missing`, `available`, `empty`, and `failed`;
an `available` graph has at least one edge (the graph placeholder here
represents such a graph). This example does not claim that these outcomes
occurred together.

### Claim: Successful layer cache entries survive a different layer's failure

- Claim ID: `claim:osm-bbox-acquisition:partial-layer-cache`
- Classification: `fact`
- Evidence IDs: `ev:osm-acquisition-cache-logic`, `ev:osm-acquisition-cache-tests`
- Code locator: `osm2terrn/data/osm_data_handler.py::_layer_cache_key()`, `::_get_cached_layer()`, `::_cache_layer()`, and `::download_data_from_bbox()` (lines 130, 156, 216, 259)
- Limits or uncertainty: The cited tests are source evidence only; they were not executed for this draft.

The per-layer cache key includes bbox coordinates and CRS, layer name and type,
query/filter values, custom tags, and algorithm/format versions.
[`_get_cached_layer()`](../../../osm2terrn/data/osm_data_handler.py#L156)
accepts only a well-formed `available` or `empty` result. Invalid entries are
ignored so the provider can be queried again. The cache writer
[`_cache_layer()`](../../../osm2terrn/data/osm_data_handler.py#L216) refuses
statuses other than `available` and `empty`.

After processing all configured layers, the handler writes a whole-bundle
cache entry only when no requested layer failed. If one fails, the whole
bundle write is skipped, but already successful or empty layers have their own
cache entries. A later call can therefore reuse those layers and retry the
failed one. The mock-based test
[`test_partial_successful_layers_are_cached_and_reused_offline()`](../../../tests/test_osm_data_handler_cache.py#L280)
describes this case. Separate tests describe legitimate empty caching and
retry after failure at lines 116 and 156 of the same file.

The bundle algorithm/format and per-layer cache use distinct version fields;
the handler currently declares bundle algorithm version `5` and per-layer
algorithm version `1`. The version-specific test at
[`test_version_five_does_not_reuse_legacy_bundle()`](../../../tests/test_osm_data_handler_cache.py#L239)
is test source, not a result produced in this task.

Both caches use the project `CacheManager` and `PickleSerializer`. A bundle
hit is checked for a dictionary, a valid road result and an acquisition-results
mapping, then returned with cached source markers. An unreadable or invalid
bundle logs a warning and continues to per-layer processing. Invalid
per-layer entries are warned about and treated as misses. Exceptions from the
[`per-layer cache writer`](../../../osm2terrn/data/osm_data_handler.py#L216)
are caught, logged as warnings, and do not change the successful layer status.
The final [whole-bundle write](../../../osm2terrn/data/osm_data_handler.py#L569)
has no equivalent local exception handler: a failure there can propagate out
of `download_data_from_bbox()` before its normal return. These are distinct
error paths. An invalid/read-failed bundle also sets a recovery marker that is
reflected in a newly acquired road result. These static paths do not establish
persistence across machines or processes.

### Claim: Overpass retries are bounded and configurable

- Claim ID: `claim:osm-bbox-acquisition:bounded-overpass-retries`
- Classification: `fact`
- Evidence IDs: `ev:osm-acquisition-retry-policy`, `ev:osm-acquisition-retry-config`, `ev:osm-acquisition-retry-loader`, `ev:osm-acquisition-retry-tests`
- Code locator: `osm2terrn/data/overpass.py::call_with_retries()` and `osm2terrn/data/osm_data_handler.py::_query_osm_layer()` (lines 181, 248)
- Limits or uncertainty: The configured outer attempt limit is not, by itself, proof of an exact total HTTP request count inside every OSMnx version.

Each geometry or network provider call goes through
[`_query_osm_layer()`](../../../osm2terrn/data/osm_data_handler.py#L248), which
passes the configured endpoints, maximum attempts, and elapsed-time budget to
[`call_with_retries()`](../../../osm2terrn/data/overpass.py#L181). The default
configuration sets three attempts and a 120-second elapsed limit. The loader
can override the primary endpoint, alternate endpoints, and both limits using
the corresponding OSM settings and provider environment-variable names in
[`ProviderConfig`](../../../osm2terrn/config/models.py#L42) and
[`ProjectLoader`](../../../osm2terrn/config/loader.py#L453).

The wrapper retries HTTP 408, 425, 429, and 5xx statuses, plus Requests
timeouts and connection errors. Other HTTP 4xx statuses are not retryable.
When present, `Retry-After` is used; otherwise the delay is randomized under
an exponentially increasing cap of 1, 2, 4, 8, 16, then 30 seconds. The
remaining time budget caps each request timeout and prevents another retry
when the next delay would exhaust the budget.

For each outer attempt, the wrapper selects the next configured endpoint. It
temporarily scopes OSMnx's endpoint, request object, pause callback, and
logging flags, then restores them in a `finally` block. The test source
[`test_osmnx_builtin_retries_are_intercepted()`](../../../tests/test_overpass_retry.py#L252)
simulates an OSMnx 429/504 retry path. Because OSMnx can handle some response
statuses within its own query call, the configured `max_attempts` should not
be described as a proven exact cap on all underlying HTTP posts without
checking the installed OSMnx implementation and execution.

### Claim: The cited tests are synthetic and do not establish live-provider behavior

- Claim ID: `claim:osm-bbox-acquisition:mock-test-boundary`
- Classification: `fact`
- Evidence IDs: `ev:osm-acquisition-cache-tests`, `ev:osm-acquisition-retry-tests`
- Code locator: `tests/test_osm_data_handler_cache.py` and `tests/test_overpass_retry.py`
- Limits or uncertainty: This chapter did not execute those tests or contact Overpass.

The cited test source replaces provider calls and uses in-memory responses and
temporary cache directories. The cases cover empty results, failed acquisition,
cache reuse, HTTP statuses, transport exceptions, retry timing, and endpoint
rotation. These definitions are evidence that such cases are represented in
tests; they are not evidence that the suite passed in this task.

## Execution branches and alternatives

The static source path has these alternatives:

1. A valid whole-bundle cache entry is validated and returned before layer
   queries begin.
2. If there is no usable bundle, a valid per-layer cache entry returns data
   with `source="cache"` and skips that provider call.
3. A per-layer cache miss or rejected cache entry invokes the OSMnx query
   through the retry wrapper. An empty response is cached as an empty result;
   a failure is recorded and not cached as success.
4. After the layer loops, a complete bundle is cached only if no requested
   layer failed. Otherwise the handler returns the partial in-memory bundle
   and leaves successful per-layer cache entries available.
5. A caught layer failure does not stop the next configured layer. A geometry
   “no matching features” response is specifically mapped to successful
   `empty` and cached; other query errors become failed and are not cached as
   successful data. Geometry and non-road network transformation failures
   are likewise not converted to empty.

When the downloader returns, `dlcity()` continues by updating the session and
attempting elevation preloading. This chapter stops at that handoff; it does
not claim that terrain generation or export was run.

The diagram below is a static/inferred flow assembled from these source paths.
It is not a recorded execution.

## Diagram references

- [`diagram:osm-bbox-acquisition`](diagrams/osm-bbox-acquisition.mmd) —
  inferred flow across `dlcity()`, `download_data_from_bbox()`, and the
  per-layer retry/cache helpers. Source and claim evidence are listed in the
  diagram header. No runtime execution is represented.

## Open questions and limitations

- `question:stage3-bbox-place-semantics`: whether an unnamed manual bbox
  should proceed remains a product decision.
- `question:stage3-preload-elevation-scope`: this chapter does not resolve
  whether `pipeline.preload_elevation` controls one or more elevation paths.
- `question:stage3-state-after-cancel`: `dlcity()` returns before changing
  the current map on its early selection guard; whether retaining that state
  is intended remains open.
- The observed source and mock test definitions do not verify a live Overpass
  response, provider availability, cache persistence across real processes,
  or exact HTTP request counts through OSMnx internals.
- No OSM acquisition tests, application commands, downloads, or external
  requests were run for this chapter. Documentation-tool checks are recorded
  in [`coverage.md`](../progress/coverage.md).

## Study exercises

1. For bbox `(-58.40, -34.62, -58.35, -34.58)` with no CRS, write the four
   `BoundingBox` fields and explain why the handler passes the tuple unchanged.
   Then explain what changes when those values are labelled `EPSG:32721`.
2. Draw the return dictionary for one available geometry, an empty road graph,
   and a failed non-road network. Which values appear in `acquisition_results`?
3. Trace one geometry through OSMnx, `transform_gdf_to_ror()`, the layer cache,
   and the return dictionary. Repeat for roads and identify their different
   result wrapper.
4. Using only source, compare: empty GeoDataFrame; “no matching features”;
   HTTP 502; geometry transform error; road graph transform error; invalid
   layer cache; invalid bundle cache. Which paths continue to another layer,
   and which can fail before per-layer handling?
5. Read the cache tests and identify assertions for partial-cache reuse. They
   are test-source evidence here; do not report them as passing unless run
   separately.
6. Explain how `Retry-After`, attempt count and deadline affect another retry.
   Why does this not prove an exact count of HTTP posts inside OSMnx?

### Expected checks

These guides describe results deducible from source inspection. They are not
observations from running the application or tests.

1. `min_x=-58.40`, `min_y=-34.62`, `max_x=-58.35`, and `max_y=-34.58`.
   With no CRS, [`_bbox_to_osmnx_tuple()`](../../../osm2terrn/data/osm_data_handler.py#L69) skips reprojection and returns the
   west/south/east/north values under the handler's geographic-input
   convention. With `crs="EPSG:32721"`, [`download_data_from_bbox()`](../../../osm2terrn/data/osm_data_handler.py#L259) first
   attempts [`BoundingBox.reproject("EPSG:4326")`](../../../osm2terrn/domain/value_objects/__init__.py#L192); on a cache miss the tuple
   adapter may attempt reprojection again. The chapter intentionally gives no
   transformed numeric bbox.
2. The available geometry value is stored under its layer key, and its
   `LayerAcquisitionResult(status="available")` appears in
   `acquisition_results`. A road query returning no nodes yields
   `StreetNetworkResult(status="empty", graph=None)`; a nodes-only graph is
   retained as empty only after transformation and CRS validation succeed
   ([road branch](../../../osm2terrn/data/osm_data_handler.py#L481)). A
   failed non-road network has `None` under its layer key and a failed
   `LayerAcquisitionResult` with failure details in `acquisition_results`.
   Roads use `bundle["roads"]` and are excluded from that map.
3. For geometry, follow `ox.features_from_bbox()` to
   `transform_gdf_to_ror()`, then `d[typ]`, the corresponding
   `acquisition_results[typ]`, `_cache_layer()`, and the final dictionary.
   For roads, follow `ox.graph_from_bbox()` through `transform_graph_to_ror()`;
   the result is wrapped in `StreetNetworkResult` with status, source, and CRS
   when a graph is present. The wrapper is the result stored under `roads`.
   These are source paths, not evidence that a provider returned those values.
4. An empty GeoDataFrame and OSMnx's recognized no-matching-features exception
   both become successful `empty` geometry results and are eligible for layer
   caching. A query HTTP 502 is classified as a temporary acquisition failure;
   the loop continues to other configured layers. Geometry and non-road graph
   transformation exceptions become `failed` at stage `transformation`. Road
   query and graph-transformation exceptions share the road handler and are
   recorded as failed with stage `acquisition`. An invalid layer cache is
   treated as a miss; an invalid bundle cache falls back to per-layer work.
   Separately, a CRS conversion failure in `_bbox_to_osmnx_tuple()` can escape
   before per-layer handlers. These paths are statically described, not
   executed outcomes.
5. In [`test_partial_successful_layers_are_cached_and_reused_offline()`](../../../tests/test_osm_data_handler_cache.py#L280), inspect
   the assertions that buildings and parks become available/empty, then are
   read from cache while the failed lakes layer is queried again. Later
   assertions check that successful layers are not queried again and that a
   subsequent complete cache is reused. This describes the test's intended
   assertions only; it does not mean the test passed.
6. [`call_with_retries()`](../../../osm2terrn/data/overpass.py#L181) honors a response's `Retry-After` when available;
   otherwise it selects a randomized delay under the configured backoff cap.
   The attempt limit bounds wrapper iterations and the deadline caps request
   timeouts and may prevent another retry. This does not establish a precise
   count of HTTP posts made within OSMnx's own handling.

### Self-check

- Why is a CRS string different from transforming coordinates?
- Does a valid empty geometry result mean acquisition failed?
- Which road value is stored in `bundle["roads"]`, and why is its contract
  separate from `LayerAcquisitionResult`?
- Which CRS reprojection error may occur outside the per-layer exception
  handlers?
- Which statements in this chapter require a test run or provider observation
  before they can be described as execution facts?

### Self-check guide

- A CRS label describes coordinates; `to_crs()` and the graph transformer
  change coordinate values.
- An empty result is a valid acquisition outcome. `failed` is a distinct state
  with failure details.
- `bundle["roads"]` is a `StreetNetworkResult`, which carries the acquisition
  status/source and, when a graph is present, its graph CRS.
- On a bundle-cache miss, a second reprojection in
  `_bbox_to_osmnx_tuple()` can raise before either layer loop.
- Live provider responses, exact OSMnx-internal HTTP counts, cache persistence
  across processes, and the application's interactive outcome require
  execution or environment-specific evidence. They are not established by the
  static flow or test source alone.

## Review record

- Review ID: pending
- Verdict: `pending`
- Date: pending
