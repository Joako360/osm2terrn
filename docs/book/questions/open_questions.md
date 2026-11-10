# Open Questions

Use stable `question:<slug>` IDs. Each question records evidence already
consulted, an owner, a state, and a concrete closure condition. Do not close a
question because a plausible explanation exists.

## Questions carried forward from the initial audit

### `question:cache-historical-absence`

- **Question:** Why was `osm2terrn/cache/` absent during the initial audit but
  present in the tree inspected on 2026-10-20?
- **Status:** Open; current presence confirmed, historical cause unknown.
- **Evidence consulted:** `initial_repository_audit.md`;
  `audit_review.md`; current package listing.
- **Owner:** Project maintainer.
- **Closure condition:** Establish the relevant repository revisions or
  workspace history and explain the temporal difference without attributing
  intent unsupported by evidence.

### `question:elevation-provider-path`

- **Question:** Which elevation-provider path is intended as the standard
  user workflow: the configured OpenTopoData URL template or the direct
  OpenTopography GlobalDEM request?
- **Status:** Open.
- **Evidence consulted:** Initial audit references to
  `osm2terrn/config/models.py` and
  `osm2terrn/processing/terrain/elevation_service.py`.
- **Owner:** Project maintainer.
- **Closure condition:** Trace current call sites and configuration behavior;
  obtain maintainer confirmation if intent remains ambiguous.

### `question:load-action-intent`

- **Question:** Is the CLI `load()` placeholder intended to load project/cache
  data, or is documented loading behavior obsolete/planned?
- **Status:** Open.
- **Evidence consulted:** Initial audit references to
  `osm2terrn/cli/commands.py` and `README.md`.
- **Owner:** Project maintainer.
- **Closure condition:** Confirm intended behavior or reconcile the future
  documentation against the maintained product scope in a later task.

### `question:maintained-test-command`

- **Question:** Which test command is the maintained baseline: pytest
  discovery, `tests/run_bbox_tests.py`, or another workflow?
- **Status:** Open.
- **Evidence consulted:** Initial audit references to
  `docs/testing-validation/testing-baseline.md`, `tests/`, and `pyproject.toml`.
- **Owner:** Project maintainer.
- **Closure condition:** Identify the documented/CI-supported command and
  record an actual result when execution is authorized.

### `question:supported-execution-surfaces`

- **Question:** Which scripts, notebooks, and direct-run test files are
  supported user interfaces versus developer experiments?
- **Status:** Open.
- **Evidence consulted:** Initial audit's entry-point inventory.
- **Owner:** Project maintainer.
- **Closure condition:** Confirm support status from maintained documentation
  or maintainer guidance; do not infer it from a `main()` guard.

### `question:local-example-data`

- **Question:** Which local `.examples/`, `.docs/`, and `output/` contents are
  reusable fixtures versus generated results?
- **Status:** Open.
- **Evidence consulted:** Initial audit's ignored-directory summary; contents
  were intentionally not inspected.
- **Owner:** Project maintainer.
- **Closure condition:** Identify safe, shareable fixtures and their provenance
  without copying private or generated material into the book.

### `question:worktree-change-context`

- **Question:** What repository revision/history explains the pre-existing
  modified and untracked files observed during the audits?
- **Status:** Open; attribution intentionally not inferred.
- **Evidence consulted:** Git-status snapshots recorded in the audit and its
  review.
- **Owner:** Project maintainer.
- **Closure condition:** Compare against an identified base revision or
  maintainer-provided change context.

### question:cache-package-gitignored

- **Question:** Is `osm2terrn/cache/` intentionally untracked? The former
  unanchored `.gitignore` pattern `cache/` also matched this source package.
- **Status:** Resolved on 2026-10-20 by anchoring the runtime-data rule to
  `/cache/`; package source is now discovered as ordinary untracked/tracked
  code rather than relying on a special ignored-directory exception.
- **Evidence consulted:** `.gitignore`; `inventory/inventory_tool.py` path
  collection; regenerated `inventory/files.jsonl`.
- **Owner:** Project maintainer.
- **Resolution:** The root runtime cache remains ignored; `osm2terrn/cache/`
  is no longer matched by that rule. Its contents remain source inventory.

### `question:legacy-import-roots`

- **Question:** Are imports rooted at `data`, `processing`, and `src` in the
  remaining scripts/tests legacy paths, intentionally supplied by a developer
  environment, or expected to resolve from another source?
- **Status:** Open; the generated dependency inventory classifies these roots
  as `undeclared_or_unresolved`. No root-level packages named `data`,
  `processing`, or `src` were found during the static audit.
- **Evidence consulted:** `inventory/external_dependencies.jsonl`;
  `tests/test_offset_fix.py`; `tests/test_roads.py`;
  `tests/run_bbox_tests.py`; `scripts/` import sites.
- **Owner:** Project maintainer.
- **Closure condition:** Confirm intended execution context or update stale
  references in a separately scoped application change. Do not treat the
  inventory classification alone as proof that a workflow fails.

### `question:yaml-dependency-declaration`

- **Question:** Should YAML configuration support declare PyYAML directly or
  as an optional dependency group?
- **Status:** Open; the tool reports `yaml` as `undeclared_or_unresolved`.
  `pyproject.toml` does not declare PyYAML directly, though `uv.lock` contains
  a PyYAML package entry. Static inspection does not establish whether the
  transitive installation is intentional.
- **Evidence consulted:** `osm2terrn/config/loader.py::_read_yaml`;
  `pyproject.toml`; `uv.lock`; generated external dependency inventory.
- **Owner:** Project maintainer.
- **Closure condition:** Confirm YAML support's intended install contract;
  update packaging metadata in a separate application/dependency task if
  required.

## Stage 3 execution-flow follow-up

The source-derived findings and runtime limits are tracked with stable IDs in
`../execution/uncertainties.md`. The following questions remain open and are
not closed by the static map:

### `question:stage3-supported-launchers`

- **Question:** Which declared launch surfaces are supported user workflows,
  including the package command, module invocation, Windows batch launcher,
  direct-file invocation, scripts, and notebook?
- **Status:** Open; source declares candidates but does not establish product
  support or successful startup.
- **Evidence consulted:** `../execution/README.md`;
  `../execution/evidence_register.md` (`P3-E001`–`P3-E004`, `P3-E015`).
- **Owner:** Project maintainer.
- **Closure condition:** Confirm intended surfaces from maintained docs or
  maintainer guidance, then verify only the selected launch commands in a
  controlled environment.

### `question:stage3-download-export-handoff`

- **Question:** What are the intended CLI semantics for (a) a manually selected
  bbox without a place label, (b) `pipeline.preload_elevation`, and (c) whether
  `current_map` is preserved or cleared after cancellation or a rejected
  selection?
- **Status:** Open. The current source returns an empty place label for manual
  bounds and `dlcity()` returns before acquisition when either place or bbox is
  false; the callback also preloads elevation without reading
  `pipeline.preload_elevation`. The early return does not clear prior session
  data. Product intent and all user-session outcomes remain unverified.
  The road graph handoff itself is tracked separately by
  `question:stage3-road-source-and-crs`; this question no longer states that
  the export callback omits the OSM bundle.
- **Evidence consulted:** `../execution/evidence_register.md`
  (`P3-E017`–`P3-E021`, `P3-E027`); `../execution/uncertainties.md`
  (`P3-F001`, `P3-F002`, `P3-F006`); `osm2terrn/data/download_menu.py`,
  `osm2terrn/cli/commands.py`, and `osm2terrn/config/models.py`.
- **Owner:** Project maintainer.
- **Closure condition:** Decide the three semantics above, preserve the
  resolved road-handoff record independently, then test cancellation/manual
  bbox, both preload settings, and subsequent export using a fake renderer and
  mocked providers. Do not infer a live integration result from those tests.

The detailed Stage 3.2 trace is in `../execution/data-handoff-analysis.md`.
The questions below track distinct decisions; resolving one does not resolve
the others.

### `question:stage3-state-after-cancel`

- **Question:** When a user cancels or submits a selection that the current
  guard rejects, should the last successfully downloaded map remain available
  for export or should the session state be cleared?
- **Status:** Open; the current early return leaves existing state untouched,
  while export accepts any nonempty prior `current_map.data`.
- **Evidence consulted:** `../execution/data-handoff-analysis.md`,
  Investigation A; `P3-E027` and `P3-F006`.
- **Owner:** Project maintainer.
- **Closure condition:** Specify preserve-or-clear behavior, then test after a
  successful mocked download followed by cancel, invalid selection, and a
  subsequent export callback.

### `question:stage3-bbox-place-semantics`

- **Question:** May a manually selected bbox proceed without a place label, and
  how must an unnamed area be represented in state, output naming, TERRN2
  metadata, and road lookup?
- **Status:** Open; the bbox downloader needs coordinates only, while the CLI
  gate requires a truthy label and downstream road lookup is place-based.
- **Evidence consulted:** `../execution/data-handoff-analysis.md`,
  Investigation A; `P3-E017` and `P3-E018`.
- **Owner:** Project maintainer.
- **Closure condition:** Choose and document the area identity/label contract;
  then cover selected bbox, cancellation, export naming, and road behavior with
  fake-renderer and temporary-output tests.

### `question:stage3-preload-elevation-scope`

- **Question:** Does `pipeline.preload_elevation` control eager terrain DEM
  acquisition only, all terrain DEM acquisition, or road DEM sampling too?
- **Status:** Open; the setting is parsed but not read by the current callback;
  heightmap export can fetch independently and road sampling has another path.
- **Evidence consulted:** `../execution/data-handoff-analysis.md`,
  Investigation B; `P3-E020` and `P3-E021`.
- **Owner:** Project maintainer.
- **Closure condition:** Define the setting's scope and fallback semantics;
  assert call counts and state with mocked provider/cache for true/false,
  valid/empty/incomplete elevation data, and road sampling if in scope.

### `question:stage3-road-source-and-crs`

- **Question:** Should export consume the initially downloaded bbox graph or
  issue a separate place-based query, and what type/CRS/origin contract should
  feed domain roads? If bbox loading is selected, which tuple order is the
  lower-level loader meant to accept? What should `export.include_roads` control?
- **Status:** Resolved for the implemented handoff; real provider and complete
  application behavior remain unverified. The stored graph is canonical, an
  EPSG:4326 GeoDataFrame view feeds `MapData`, and processing consumes the
  same graph without place reload when supplied. `export.include_roads` gates
  conversion/output. Synthetic tests cover these boundaries. This does not
  resolve bbox tuple/API semantics, elevation-preload scope, stale session
  state, or live-provider/final-output behavior. See the dated record in
  `../execution/data-handoff-analysis.md`.
- **Evidence consulted:** `../execution/data-handoff-analysis.md`,
  Investigation C; `P3-E022`–`P3-E026`, `P3-E028`–`P3-E029`, and
  `P3-F004`–`P3-F007`.
- **Owner:** Project maintainer.
- **Closure condition:** The design and implemented handoff are closed by the
  cited code and synthetic checks. Keep real-provider CRS metadata,
  interactive flow, and final output `not_verified` until separately checked.
  Track bbox tuple semantics and elevation policy under their own question
  IDs.

## Question maintenance

When resolving an item, preserve its ID and record the evidence, date, and
resolution. If the evidence only narrows the possibilities, leave it open and
update the closure condition.
