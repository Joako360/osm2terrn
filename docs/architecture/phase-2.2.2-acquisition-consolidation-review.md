# Phase 2.2.2 — Acquisition Consolidation Design Review

## 1. Executive summary

**Verdict: REQUIRES CORRECTIONS.**

The proposal has a sound direction: keep providers independent, separate
acquisition from normalization and processing, preserve the graph and raster
as specialized artifacts, introduce a small handoff instead of a provider
framework, and defer `PipelineResult` until there is a concrete consumer. Its
OSM, Overture, raster, and CLI migration concerns are generally grounded in
the current code and in Phase 2.1.1.

Three issues must be corrected before approval:

1. Retaining original OSM payloads is incompatible with serving existing OSM
   cache hits unchanged: those entries contain already-projected outputs, not
   the original provider objects.
2. The raster adapter cannot meet the new raster contract from existing
   cached tuples, while the plan simultaneously prohibits changing cache
   formats and keys.
3. Overture's flow and provider section classify invalid CRS/schema as
   acquisition failure, contradicting the explicit separation of acquisition
   and normalization outcomes.

No critical finding was established. The design is implementable after these
conflicts and the diagram/contract ambiguities below are resolved. Overture's
Fused parameter and release behavior remain unverified; the proposal
appropriately makes a controlled test a gate and this review did not contact
any provider.

## 2. Scope and methodology

This was a static design and source review. It compared the proposal with
[Phase 2.1.1 — Fundamental Data Contract Specification](phase-2.1.1-data-contracts.md)
and [Phase 2.2 — Data Acquisition Flows Audit](phase-2.2-acquisition-audit.md),
then inspected the current interfaces and selected tests. The review did not
run tests, execute the application, perform cache migration, or make live
OSM, Fused/Overture, or OpenTopography requests. Mermaid diagrams were
checked by inspection, not by a Mermaid parser.

The source checkout already contained local work. No source or reference
document was edited; the only file created for this task is this review.

## 3. Documents and modules inspected

**Required documents and applicable documentation instructions**

- [Documentation instructions](../../.github/instructions/docs.instructions.md)
- [Phase 2.1.1 data contracts](phase-2.1.1-data-contracts.md)
- [Phase 2.2 acquisition audit](phase-2.2-acquisition-audit.md)
- [Phase 2.2.2 consolidation design](phase-2.2.2-acquisition-consolidation-design.md)

**Source modules**

- Acquisition and street contracts: [`acquisition.py`](../../osm2terrn/data/acquisition.py), [`street_network.py`](../../osm2terrn/data/street_network.py)
- OSM, Overture, and alternate graph paths: [`osm_data_handler.py`](../../osm2terrn/data/osm_data_handler.py), [`osm_loader.py`](../../osm2terrn/data/osm_loader.py)
- Coordinate and domain handoffs: [`coordinate_transform.py`](../../osm2terrn/adapters/coordinate_transform.py), [`osmnx_to_roads.py`](../../osm2terrn/domain/adapters/osmnx_to_roads.py), [`osmnx_to_map.py`](../../osm2terrn/domain/adapters/osmnx_to_map.py), [`map_data.py`](../../osm2terrn/domain/entities/map_data.py)
- Raster and road consumers: [`elevation_service.py`](../../osm2terrn/processing/terrain/elevation_service.py), [`heightmap_handler.py`](../../osm2terrn/processing/terrain/heightmap_handler.py), [`road_elevation.py`](../../osm2terrn/processing/roads/road_elevation.py)
- Coordination and cache: [`commands.py`](../../osm2terrn/cli/commands.py), [`app_state.py`](../../osm2terrn/app/app_state.py), [`orchestrator.py`](../../osm2terrn/processing/orchestrator.py), [`manager.py`](../../osm2terrn/cache/manager.py), [`keys.py`](../../osm2terrn/cache/keys.py)
- Selected test evidence: [`test_street_network_integration.py`](../../tests/test_street_network_integration.py), [`test_elevation_cache.py`](../../tests/test_elevation_cache.py), [`test_osm_data_handler_cache.py`](../../tests/test_osm_data_handler_cache.py). Test source was inspected; none was run.

## 4. Coherence with Phase 2.1.1

The proposed hierarchy `AcquisitionBundle → providers → datasets → layers`
matches the contract specification and is a meaningful improvement over the
current flat OSM dictionary and separate Overture/raster returns. Keeping
provider, dataset, layer, method, outcome, and provenance distinct is
technically justified. Reusing `LayerAcquisitionResult` and
`StreetNetworkResult` avoids an unnecessary parallel status hierarchy.

The separation of raw provider payloads, normalized `MapData`, derived local
graph views, and processing results is also consistent with Phase 2.1.1.
`MapData` is vector-focused; the raster contract correctly carries CRS,
affine, dimensions, bounds, NoData, validity, and unknown vertical metadata
separately. The proposal correctly distinguishes acquisition status from
normalization/processing status and allows independent partial provider
results.

The street-network intent is sound: graph topology remains authoritative;
edge and domain `Road` identities are distinct; a geographic graph is the
target acquisition source; and local coordinates are derived for metric
consumers. This is a material migration, not a documentation-only renaming:
the current bbox path transforms the graph before returning it, and an
existing integration test asserts that its `StreetNetworkResult` is local.
The proposal recognizes the compatibility gate but should make the source
versus derived-result distinction explicit in the handoff contract.

**Raster contract:** the validity-mask and NoData rules align with Phase
2.1.1 and correctly prevent invalid samples from silently becoming valid
zero elevations. Current code returns a tuple and the convenience API drops
the affine; the raster metadata loss is confirmed. Sharing a raster only when
its extent and CRS are suitable is correct. The cache and peak-memory
constraints remain unresolved as described in findings H-02 and M-05.

**Provider-specific findings:** OSM's retries and current public facade can
remain behind an adapter; coordinate conversion must fail rather than
continue with projected values after a failed transform. Overture is rightly
independent and additive, but its `bbox`/`bounds` and mutable UDF/release
behavior are explicitly unverified and must remain a gate, not an accepted
behavior. The current Overture wrapper assigns EPSG:4326 without verifying
the returned source CRS and does not establish a stable source-ID contract;
the target must validate those facts rather than infer them from the wrapper.
OpenTopography acquisition, decoding, validation, and processing are
appropriately separated in the target design; vertical units and datum are
correctly left unknown absent evidence.

## 5. Architecture assessment

The application/CLI-level coordinator is justified: today OSM is acquired
through `dlcity`, elevation can be acquired by CLI and processing consumers,
and Overture has no common result handoff. The proposal appropriately avoids
a provider registry, keeps `data/acquisition.py` independent of providers,
and delays `PipelineResult` until a later stage needs a run ledger. This is
simpler and safer than either a plugin framework or replacing `current_map`
up front.

The module responsibilities are generally sound. Provider modules should
return acquisition facts and source data; adapters normalize; processing
consumes explicit artifacts; the existing exporter boundary remains stable
during early migration. The proposal also notes present import-time config,
OSMnx global state, Fused's module-level import, and the mutable CLI holder.
These are real coupling points, and the staged plan does not require solving
all of them before defining the acquisition contract.

The principal architectural risk is migration compatibility, not the target
shape itself. The current OSM caches contain transformed geometry/graphs;
the current raster cache contains a tuple that cannot satisfy the new
geospatial contract. Keeping those entries untouched is reasonable only if
the design defines how new consumers reject or bypass them. The current
proposal does not reconcile that requirement with source-payload preservation
and cache reuse.

## 6. Findings

### H-01 — Existing OSM cache hits cannot provide the promised original payload

- **Severity:** HIGH
- **Design sections:** §§4.1, 4.3, 5.1, 7, and 11 Stages B–C; decisions in §§13 and 15.
- **Evidence:** The contract says the layer payload references the exact
  acquired object and normalization must not mutate it. The current
  [`download_data_from_bbox`](../../osm2terrn/data/osm_data_handler.py)
  caches GeoDataFrames and street results after projecting them to local
  coordinates. The current cache-hit path returns those stored objects. The
  design simultaneously says to keep keys, namespaces, and formats unchanged.
- **Problem:** Stage B proposes wrapping existing OSM return objects by
  reference, but a legacy cache hit is already a derived local view. It is
  not the original provider payload. Reprojecting it back cannot recover the
  exact source object or necessarily its original CRS/precision.
- **Consequence:** A cache-hit bundle could claim source-payload preservation
  while carrying only a transformed artifact. That breaks provenance and
  makes query and cache paths semantically unequal.
- **Recommended correction:** Define an explicit legacy-cache policy before
  Stage B/C: either treat legacy transformed entries as compatibility views
  and mark raw source unavailable, bypass them and query when a source
  payload is required, or introduce a deliberately versioned cache
  representation. Specify how each choice preserves the no-silent-migration
  requirement and test cache-hit and fresh-query behavior separately.

### H-02 — Raster contract and “no cache migration” cannot both hold for legacy tuples

- **Severity:** HIGH
- **Design sections:** §§5.3 and 7; Stage D; contract tests in §12; decisions in §§13 and 15.
- **Evidence:** Current
  [`load_elevation_raster`](../../osm2terrn/processing/terrain/elevation_service.py)
  stores `(array, affine, max, min)`. The tuple omits CRS, bounds, source
  mask/NoData metadata, and units. The design correctly says a raster cache
  entry without trustworthy CRS and validity metadata cannot satisfy the new
  contract and should be treated as a miss, but Stage D also says not to
  change cache keys or formats.
- **Problem:** Repeatedly treating that old entry as a miss cannot produce a
  reusable `RasterArtifact` from cache. Writing the artifact into the same
  key/format changes the serialized contract; continuing to write the tuple
  leaves future consumers without the required metadata.
- **Consequence:** Implementers must either silently change a format, keep
  reacquiring the DEM, or weaken the raster contract for cached results.
  None is the documented plan.
- **Recommended correction:** Choose a bounded transition explicitly: a
  versioned/new cache artifact for the new raster contract, a separate
  compatible cache namespace, or a documented period in which the new
  artifact is not cached and legacy callers retain the tuple cache. State
  which paths are cache hits/misses and add tests for each; do not label a
  legacy tuple as a validated raster.

### H-03 — Overture CRS/schema failures conflate acquisition and normalization

- **Severity:** HIGH
- **Design sections:** §4.2, §5.2, diagram 10.4, and Stage D.
- **Evidence:** §4.2 says that a successfully acquired payload which fails
  geometry/CRS normalization remains acquisition-`available`; the failure
  belongs to a distinct normalization result. In contrast, §5.2 and diagram
  10.4 route an invalid CRS/schema to a typed failed acquisition outcome.
- **Problem:** The proposal applies two meanings to the same status transition.
  A response transport/provider failure is an acquisition failure; a
  returned source frame with a CRS or domain-geometry problem should be
  represented according to the agreed acquisition structural-validation
  boundary and, when it is a normalization defect, reported separately.
- **Consequence:** Consumers cannot tell whether Overture failed to return
  data or returned data that the adapter could not normalize. This can
  incorrectly mark the provider unavailable and obscure useful raw payloads.
- **Recommended correction:** Define the minimum acquisition-level response
  checks separately from normalization checks, then align §5.2, diagram 10.4,
  outcomes, and tests with §4.2. Preserve the raw response when it exists;
  record a normalization failure without rewriting successful acquisition.

### M-01 — `AcquisitionBundle.bounds` does not define its scope across different requests

- **Severity:** MEDIUM
- **Design sections:** §§4.1, 6, 8, and diagrams 10.1/10.7.
- **Evidence:** The bundle has one requested `bounds`, while the current CLI
  acquires OSM for the selected bbox, expands the map/heightmap to square
  bounds, and road sampling may request a DEM for a separate road extent.
  The design allows raster reuse only where extents are suitable and
  requests per-provider settings.
- **Problem:** It is not explicit whether bundle bounds mean user-selected
  area, run/terrain extent, or the bounds for every provider. Per-artifact
  bounds are distinguished from request bounds, but the per-layer request
  bounds invariant is not stated for all providers.
- **Consequence:** A layer can be associated with an ambiguous area, or a
  coordinator can incorrectly reuse a DEM whose coverage does not serve a
  consumer.
- **Recommended correction:** Define bundle bounds as one named run-level
  extent and require request bounds (with CRS) in each layer's provenance
  whenever different. Keep returned artifact bounds separate. Add tests for
  OSM-selected, terrain-square, and road-extent requests.

### M-02 — The same street result type has no explicit source/derived role at the handoff

- **Severity:** MEDIUM
- **Design sections:** §§4.1, 5.1, 8, and Stage C.
- **Evidence:** The proposed acquisition payload/outcome uses
  `StreetNetworkResult` for the geographic source graph, while the legacy
  `download_data_from_bbox()` facade must continue returning a local
  `StreetNetworkResult`. Existing consumers use that local result for metric
  road processing; the domain adapter can convert either declared CRS to
  EPSG:4326.
- **Problem:** CRS metadata identifies coordinates but not whether a result
  is the authoritative acquired graph or a derived compatibility view. The
  proposal names the views in prose but does not state how both appear in
  the transitional result or prevent a consumer from choosing the wrong one.
- **Consequence:** A consumer may perform metric operations on a geographic
  graph or treat a derived local graph as the provider source of truth.
- **Recommended correction:** Specify the bundle's `StreetNetworkResult` as
  the source result and the facade's local graph as a separately named
  derived/compatibility view. Define which downstream functions receive each
  and assert graph CRS plus coordinate behavior at those handoffs.

### M-03 — Several target diagrams blur acquisition payloads and derived views

- **Severity:** MEDIUM
- **Design sections:** §10, diagrams 10.1–10.8.
- **Problem and diagram-by-diagram review:**

  | Diagram | Review |
  |---|---|
  | 10.1 General architecture | Readable and broadly matches the prose, but it shows normalization producing both the geographic source graph and local graph. The source graph belongs to the acquisition bundle; normalization derives only the local view. |
  | 10.2 Contract relations | The hierarchy and specialized outcomes are consistent. Clarify that the raster artifact is a post-validation reference, not a replacement for the acquired raw raster payload. |
  | 10.3 OSM flow | Query and cache branches are clear, but both converge on “Raw.” Existing cached OSM entries are already projected, so they cannot enter that node as original source payloads without the policy in H-01. |
  | 10.4 Overture flow | The structure is clear, but its invalid-CRS/schema branch conflicts with §4.2 (H-03). “Dataset release” also risks conflating dataset identity with release provenance. |
  | 10.5 Raster flow | The request/decode/validate/mask sequence matches the contract. Show acquisition outcome separately from raster validation outcome, and resolve the legacy-cache path per H-02. |
  | 10.6 Cache sequence | Provider independence and method tracking are represented. It omits behavior when cache persistence fails after a successful provider response; see M-04. |
  | 10.7 CLI/processing | It correctly separates legacy projection and later `PipelineResult`, but again places the source graph as a normalization output. Show the bundle supplying the source graph directly and normalization supplying its derived local view. |
  | 10.8 Module architecture | The provider-to-normalizer arrows can be read as provider modules depending on or performing normalization, contrary to §9's dependency rule. Route normalized data flow through an explicit normalization boundary and distinguish data flow from module dependencies. |

- **Syntax:** No obvious Mermaid syntax error was found by inspection. A
  parser/renderer was not run, so syntax validity is not mechanically
  confirmed.
- **Consequence:** Readers may implement incompatible responsibilities even
  though the prose's intended separation is mostly correct.
- **Recommended correction:** Update the named diagrams to show source
  artifacts inside/flowing from the acquisition bundle, derived views from
  normalizers, separate stage outcomes, and the cache policy. Add a short
  note defining whether each architecture arrow means a dependency or data
  flow.

### M-04 — Cache-write failure semantics are not defined

- **Severity:** MEDIUM
- **Design sections:** §§4.2, 7, 10.6, and 13.
- **Evidence:** The cache is described as persistence rather than the
  in-memory contract, but `CacheManager.put()` can raise during serialization
  or backend writes. The Phase 2.2 audit records that write-failure behavior
  is not uniform across providers.
- **Problem:** The sequence diagram shows a successful query followed by a
  cache write, but does not say whether a failed write turns an otherwise
  successful acquisition into `failed`, remains `available` with a warning,
  or gets another distinct diagnostic.
- **Consequence:** Different providers may report different outcomes for the
  same successful query, and cache infrastructure can mask or misstate
  provider availability.
- **Recommended correction:** Define the status rule and diagnostic/method
  semantics for cache-write failure. Prefer treating provider success as
  acquisition success with an observable cache warning unless product policy
  explicitly requires persistence; test the rule across provider adapters.

### M-05 — Peak raster memory is acknowledged but not bounded by an acceptance criterion

- **Severity:** MEDIUM
- **Design sections:** §§4.3 and 5.3; Stage D and its acceptance tests.
- **Evidence:** The design identifies raw-response retention, arrays, masks,
  and memory growth as risks, but leaves whether response bytes remain
  resident to Stage D and gives no peak-memory or maximum-artifact criterion.
  Current elevation code materializes response content and reads a full band;
  a validity mask adds another array.
- **Problem:** “Do not duplicate arrays” does not alone bound the peak working
  set when source bytes, decoded values, mask, and derived heightmap/local
  views coexist.
- **Consequence:** Large extents can exhaust memory despite the contract
  avoiding unnecessary copies.
- **Recommended correction:** At Stage D, document whether raw bytes are
  retained or cache-backed/released, identify expected array/mask copies, and
  add a representative peak-memory or size-bound acceptance check. Keep this
  a resource decision; no arbitrary threshold is inferred by this review.

### L-01 — Provider/dataset/layer example identifiers are not fully canonicalized

- **Severity:** LOW
- **Design sections:** §§4.1, 5.2, diagram 10.4, and Appendix A.
- **Evidence:** Examples use Overture dataset names such as
  `overture-buildings` and `Overture Maps`, layer labels `building` and
  `buildings`, and a diagram label of “dataset release,” while the contract
  requires stable identities and places release details in provenance.
- **Problem:** The examples are illustrative, but do not consistently
  distinguish stable dataset identity from mutable release or choose one
  layer spelling.
- **Consequence:** Implementations may use display names or release values as
  cache/lookup identity and drift between provider results.
- **Recommended correction:** Select stable machine identifiers for each
  provider/dataset/layer, keep release/version in provenance, and use those
  identifiers consistently in examples and diagrams before Stage B/D.

## 7. Review of migration stages A–E

| Stage | Assessment |
|---|---|
| **A — Characterization baseline** | Correct first step, appropriately independent. The tests and call-count checks can be deterministic without live providers. Keep current lossy behavior explicitly labeled as legacy rather than target behavior. |
| **B — Contracts and compatibility adapters** | Objective and testable, but its claim to assemble current payload references is not enough for the source-payload contract: current OSM results/cache entries are already transformed. Resolve H-01 and define how a transitional bundle labels legacy data before Stage B acceptance. |
| **C — Preserve OSM source payloads and derive views** | Correctly follows B and identifies CRS, topology, mutation, and memory risks. It needs the explicit source-versus-local result contract in M-02 and a decision for legacy cache hits in H-01. Its tests should verify both source identity and current local consumer parity. |
| **D — Overture and raster adapters** | Responsibilities and proposed modules are broadly appropriate; external Fused verification is properly gated. Resolve H-02/H-03 before implementation. Its dependency on C is justified for Overture domain mapping, but raster/OpenTopography work is independent after B; consider splitting these workstreams so one does not unnecessarily block the other. Add the memory criterion in M-05. |
| **E — Coordinator and CLI transition** | Correctly late in the sequence. Tests cover cancel/reset, preload policy, partial failure, and output parity. Keep `PipelineResult` conditional on actual stage-ledger need; do not make `current_map` the new acquisition contract. |

**Order:** A → B → C → D → E is a safe, conservative order and should remain
the default dependency order. It is not a strict requirement that all of D
wait for C: independent raster work can proceed after B, while Overture
normalization depends on the geometry/identity decisions from C. The most
important missing gates are cache compatibility in B–D and consistent
acquisition-versus-normalization status semantics in D.

Acceptance criteria are mostly objective (payload identity, status parity,
CRS agreement, cache hit/query behavior, no second request, output
regression). The design should add the explicit cache-write behavior and
resource criterion above; it should also avoid calling a legacy transformed
cache payload an original source object.

## 8. Decisions in §§13 and 15

### Blockers before approval

- Reconcile raw OSM source preservation with legacy cache hits and the
  no-migration boundary (H-01).
- Reconcile the `RasterArtifact` contract with legacy tuple cache behavior
  (H-02).
- Make Overture's source/normalization failure boundary consistent (H-03).
- Define bundle-level versus provider/layer request bounds (M-01), so the
  common contract cannot ambiguously describe distinct extents.

### Must be resolved before a named implementation stage

- **Before Stage B:** stable provider/dataset/layer identity fields and how a
  legacy OSM payload is represented; method/source mapping for generic
  `cache_recovered`; the cache policy in H-01.
- **Before Stage C:** canonical geographic `StreetNetworkResult` versus
  named local compatibility view (M-02), and legacy graph-cache handling.
- **Before Stage D:** controlled evidence for Fused's accepted bounds
  parameter and actual queried extent; how to pin or record UDF/dataset
  release; Overture source CRS/ID behavior; raster cache strategy (H-02);
  raw response-byte retention and resource acceptance; extent/CRS rules for
  sharing one raster.
- **Before Stage E:** explicit behavior for cancel/reset and preload
  enabled/disabled, and the concrete criterion for introducing
  `PipelineResult`.
- **Before any provider cache write implementation:** cache-write failure
  outcome and diagnostic policy (M-04).

### Safe to defer without changing the initial acquisition envelope

- Exact deterministic fallback-ID canonicalization and persistent `Road.id`
  policy, provided provider IDs and source-to-edge-to-road associations are
  retained in the interim.
- Enabling additional multipart/polygon geometry mappings; preserve source
  geometry and reject lossy normalization meanwhile.
- Vertical unit/datum inference; use `unknown` until verified.
- Per-consumer invalid-sample fill/interpolation behavior and OSM/Overture
  deduplication/precedence; initial behavior remains explicit and additive.
- Long-term cache adapter removal date, cache eviction/expiry policy, and
  durable cross-version serialization, once the immediate cache transition
  is specified.
- Broader building export and exporter interface changes.

## 9. Recommendations and exact corrections

Before approval, update the original design in these locations:

1. **§§4.1, 4.3, 5.1, 7, Stage B/C, §13, and §15:** state how source payload
   requirements interact with already-projected OSM cache entries and define
   the legacy-cache transition (H-01).
2. **§§5.3, 7, Stage D, §12, §13, and §15:** define a feasible raster cache
   transition without silently changing old formats or claiming an
   under-specified tuple is a valid raster (H-02).
3. **§§4.2 and 5.2 and diagram 10.4:** align Overture acquisition and
   normalization outcomes (H-03).
4. **§§4.1, 6, 8, and diagrams 10.1/10.7:** define run bounds versus
   per-layer query bounds (M-01).
5. **§§4.1, 5.1, 8, Stage C, and diagrams 10.1/10.3/10.7:** distinguish
   authoritative source graph from the local compatibility view (M-02).
6. **§10 diagrams 10.1–10.8:** make each diagram agree with the corrected
   contract and show whether arrows indicate module dependency or data flow
   (M-03).
7. **§§7, 10.6, and 13:** specify observable behavior for cache-write failure
   after a successful query (M-04).
8. **§§4.3 and 5.3, Stage D:** add a measured or bounded peak-memory
   acceptance criterion (M-05).
9. **§§4.1, 5.2, diagram 10.4, and Appendix A:** settle and consistently use
   stable provider/dataset/layer identifiers (L-01).

The provider parameter/release, unknown vertical metadata, geometry support,
IDs, and per-consumer raster fill remain decisions rather than verified
facts. Do not remove the UDF integration gate or imply its behavior has been
tested.

## 10. Verifications and Git state

- Static review only; no tests/builds were run.
- No OSM, Overture/Fused, or OpenTopography requests were made.
- No cache migration or source edits were performed.
- Initial `git status --short` contained **62 modified paths** and **15
  untracked entries**. These pre-existing changes were preserved:
  - Modified paths:
    `.env.example`, `.github/copilot-instructions.md`, `.gitignore`,
    `.vscode/settings.json`, `CONTRIBUTING.md`, `README.md`,
    `docs/ELEVATION_REALISM_QUICK_START_EN.md`,
    `docs/ELEVATION_REALISM_QUICK_START_ES.md`, `docs/README.md`,
    `docs/architecture/architecture-change-map.md`,
    `docs/architecture/architecture-data-contracts.md`,
    `docs/architecture/architecture-modules.md`,
    `docs/architecture/architecture-pipeline.md`,
    `docs/cli-flow/cli-download.md`, `docs/cli-flow/cli-export.md`,
    `docs/contributor-onboarding-en.md`, `docs/contributor-onboarding-es.md`,
    `docs/dependencies.md`,
    `docs/elevation-realism/elevation_realism_improvements-en.md`,
    `docs/elevation-realism/elevation_realism_improvements-es.md`,
    `docs/exporters/tobj.md`,
    `docs/function-reference/function-reference-data.md`,
    `docs/function-reference/function-reference-entrypoint.md`,
    `docs/function-reference/function-reference-index.md`,
    `docs/function-reference/function-reference-processing.md`,
    `docs/function-reference/function-reference-utils.md`,
    `docs/opentopography-api/opentopography-api-key-en.md`,
    `docs/opentopography-api/opentopography-api-key-es.md`,
    `docs/testing-validation/testing-functional-workflow.md`,
    `docs/troubleshooting/opentopography-api-key-en.md`,
    `docs/troubleshooting/troubleshooting-download.md`,
    `osm2terrn/adapters/coordinate_transform.py`,
    `osm2terrn/app/app_state.py`, `osm2terrn/cli/commands.py`,
    `osm2terrn/config/loader.py`, `osm2terrn/config/models.py`,
    `osm2terrn/config/validator.py`, `osm2terrn/data/osm_data_handler.py`,
    `osm2terrn/data/osm_loader.py`, `osm2terrn/domain/adapters/bounds.py`,
    `osm2terrn/domain/adapters/osmnx_to_map.py`,
    `osm2terrn/domain/adapters/osmnx_to_roads.py`,
    `osm2terrn/domain/entities/bbox.py`,
    `osm2terrn/domain/entities/features.py`,
    `osm2terrn/domain/value_objects/__init__.py`,
    `osm2terrn/processing/network/road_network_export.py`,
    `osm2terrn/processing/network/road_network_graph_build.py`,
    `osm2terrn/processing/orchestrator.py`,
    `osm2terrn/processing/roads/road_elevation.py`,
    `osm2terrn/processing/terrain/elevation_service.py`,
    `osm2terrn/processing/terrain/heightmap_handler.py`,
    `osm2terrn/utils/geometry/__init__.py`,
    `osm2terrn/utils/geometry/bounds.py`, `osm2terrn/utils/geometry/crs.py`,
    `tests/test_config_precedence.py`, `tests/test_domain_adapters_cache.py`,
    `tests/test_domain_architecture.py`, `tests/test_elevation_cache.py`,
    `tests/test_geometry_utils.py`, `tests/test_heightmap_cache.py`,
    `tests/test_osm_data_handler_cache.py`,
    `tests/test_pipeline_domain_state.py`.
  - Untracked entries:
    `docs/architecture/PHASE-1-COMPLETION.md`,
    `docs/architecture/phase-2.1.1-data-contracts.md`,
    `docs/architecture/phase-2.2-acquisition-audit.md`,
    `docs/architecture/phase-2.2.2-acquisition-consolidation-design.md`,
    `docs/book/`, `osm2terrn/cache/`, `osm2terrn/data/acquisition.py`,
    `osm2terrn/data/overpass.py`, `osm2terrn/data/street_network.py`,
    `osm2terrn/output/`, `tests/test_inventory_tool.py`,
    `tests/test_overpass_retry.py`, `tests/test_street_cache_process.py`,
    `tests/test_street_network_handoff.py`,
    `tests/test_street_network_integration.py`.
- The final status check confirmed the same 62 modified paths and 15
  pre-existing untracked entries, plus only this new review file. No
  pre-existing path was changed by this task.

## 11. Final verdict

**REQUIRES CORRECTIONS.**

The proposed architecture is viable and does not need a fundamental
replanning. Approval should wait until H-01, H-02, and H-03 are corrected and
the bounds, graph-view, diagram, cache-write, and memory details are made
consistent and testable. The implementation sequence can then proceed from
Stage A, with provider-specific verification gates preserved. Approval and
any change to the original design remain for the developer to decide.
