# CI, naming, and review checklist

## CI integration

Automate exporter validation in CI so regressions fail fast.

Typical CI steps:
1. Checkout repository.
2. Install tooling dependencies.
3. Run exporter validation scripts.
4. Fail on non-zero exit code.

## Naming and layout recommendations

- Use lowercase hyphen-separated filenames.
- Keep GUIDs stable when possible.
- Organize assets by geometry/pages/objects/resources folders.

## Review checklist

- Heightmap resolution verified.
- Required `.terrn2` keys present.
- No unintended object reordering.
- All referenced assets exist.
- Performance-sensitive changes documented.
