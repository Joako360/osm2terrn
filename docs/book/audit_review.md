# Initial Audit Review

## Review record

- Review date: 2026-10-20
- Reviewed artifact: `initial_repository_audit.md`
- Review type: static comparison with the currently visible repository tree
- Tests, application execution, and external services: not run
- Git tree: not clean at review time; do not attribute existing changes

This review supplements the original audit. It does not rewrite its snapshot
or claim to verify runtime behavior.

## Historical finding: cache package

The initial audit states that `osm2terrn/cache/` was absent from its inspected
tree. On 2026-10-20, direct filesystem inspection found the package and these
modules:

- `osm2terrn/cache/__init__.py`
- `osm2terrn/cache/backend.py`
- `osm2terrn/cache/file_cache.py`
- `osm2terrn/cache/keys.py`
- `osm2terrn/cache/manager.py`
- `osm2terrn/cache/metadata.py`
- `osm2terrn/cache/serializers.py`
- `osm2terrn/cache/version.py`

The discrepancy is temporal: retain the original statement as a historical
observation and use the current file tree for later inventory. Inspection of
the package listing does not prove import correctness, behavioral correctness,
or passing tests. The reason it was absent at the earlier inspection remains
unknown.

## Other dated state differences

- The initial audit reports that its requested report path did not exist when
  checked. The report now exists at `docs/book/initial_repository_audit.md`;
  both statements refer to different inspection times.
- The audit recorded 19 modified tracked paths and one untracked architecture
  file. The current status also contains untracked files under `docs/book/`.
  These observations do not establish who made the changes or why.
- Counts and approximate sizes in the initial audit describe its earlier
  filesystem snapshot and must not be reused as current totals.

## Findings retained for follow-up

The following are claims in the initial audit that require a separate,
line-by-line recheck before use as current book evidence:

| Finding | Existing evidence to recheck | Status |
|---|---|---|
| Declared Python floor differs from README and contributor guide | `pyproject.toml`, `README.md`, `CONTRIBUTING.md` | Open |
| README refers to `requirements.txt` and root `main.py` | `README.md` and current root listing | Open |
| Testing guide refers to `src/` | `docs/testing-validation/testing-baseline.md` and current root listing | Open |
| Architecture/function references may point at old module paths | `docs/architecture/`, `docs/function-reference/`, source tree | Open |
| CLI load action is a placeholder | `osm2terrn/cli/commands.py` and README wording | Open |
| Packaging license path may differ from the license filename | `pyproject.toml` and root listing | Open |
| Elevation configuration mentions OpenTopoData while a downloader calls OpenTopography | `osm2terrn/config/`, `osm2terrn/processing/terrain/elevation_service.py`, call sites | Open |
| CI workflow directory was not found in the earlier snapshot | Current `.github/` listing | Open |

These are review targets, not newly verified conclusions. Do not mark them
resolved solely because they appear in the initial audit.

## Limitations and pending work

- This review did not traverse all source files, symbols, documentation links,
  or dynamic execution paths.
- No tests, imports, builds, API requests, or data downloads were run.
- The current presence of the cache package was checked by listing its files;
  behavior was not checked.
- Recheck each discrepancy against the exact current source and record
  evidence paths (and useful line numbers) in the future inventory.
- Preserve the date/revision associated with each later inventory generation.
