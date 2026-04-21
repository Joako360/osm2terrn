# Contributor onboarding guide (English)

This document proposes the **minimum learning path** for new contributors to understand the project quickly and start contributing without getting lost.

## Recommended reading order

1. **README.md**
   - What the project does (goal and outputs).
   - End-to-end CLI workflow.
   - High-level folder structure.

2. **CONTRIBUTING.md**
   - Contribution conventions, branches, commit style, and code expectations.
   - Quality bar expected for pull requests.

3. **`src/main.py` (main flow)**
   - Application entry point.
   - Sequence: download data â†’ process/export.
   - Session state (`MapData`) and interactive menu behavior.

4. **Exporter docs (`docs/exporters-docs.md`)**
   - Explains generated file contracts (`.terrn2`, `.otc`, `.tobj`).

5. **Function reference (`docs/function-reference.md`)**
   - Module-by-module summary of key functions/classes.
   - Inputs/outputs and responsibilities across the pipeline.

---

## Fundamental documentation articles contributors should have

If documentation should be effective for first-time contributors, these are the most important articles.

### 1) Architecture and pipeline overview
**Goal:** explain how data flows from OSM input to RoR terrain outputs.

It should answer:
- Which modules participate and in what order?
- What shared data structures move across modules?
- Where is temporary state stored?

Implemented: [Contributor architecture guide](architecture.md).

### 2) CLI execution flow guide
**Goal:** describe exactly what each main menu option does.

Implemented: [Contributor CLI flow guide](cli-flow.md).

### 3) Module and function reference
**Goal:** provide a navigable map of â€œwhat each function doesâ€ so contributors do not need to inspect the whole repo first.

It should include:
- `src/data/*`: OSM download and parsing.
- `src/processing/*`: elevation, roads, and exporters.
- `src/utils/*`: BBox, geometry, logging, constants.
- Short signature summary + purpose + side effects for each public function.

### 4) Output formats (contracts)
**Goal:** document generated formats and semantics to avoid regressions.

It should cover:
- `.terrn2`: sections and required fields.
- Global and paged `.otc`: key parameters.
- `.tobj`: objects and procedural roads.
- Output filename conventions in `output/`.

### 5) Common errors and troubleshooting
**Goal:** reduce debugging time for first-time contributors.

Implemented: [Contributor troubleshooting guide](troubleshooting.md).

### 6) Testing and validation guide
**Goal:** define how to verify changes before opening a PR.

Implemented: [Contributor testing and validation guide](testing-validation.md).

---


## Detailed contributor docs (split by topic)

- [Contributor docs index](README.md)
- [Architecture index](architecture/architecture-index.md)
- [CLI flow index](cli-flow/cli-index.md)
- [Function reference index](function-reference/function-reference-index.md)
- [Troubleshooting index](troubleshooting/troubleshooting-index.md)
- [Testing index](testing-validation/testing-index.md)
- [OpenTopography API key setup (English)](opentopography-api/opentopography-api-key-en.md)
- [OpenTopography API key setup (Spanish)](opentopography-api/opentopography-api-key-es.md)
- [Exporter docs index](exporters/README.md)

---
## Practical way to start contributing

1. Run the full workflow with a small bbox.
2. Open generated files in `output/` and confirm all expected outputs are created.
3. Use `.docs/function-reference.md` to identify which module to modify for your issue.
4. Keep changes small (ideally one module per PR) and attach output evidence.

---

## Scope of `.docs/function-reference.md`

The function reference is designed as a navigation index:
- It does **not** replace detailed docstrings.
- It **does** accelerate onboarding by showing dependencies and module responsibilities.


