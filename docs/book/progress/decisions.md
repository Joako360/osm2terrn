# Documentation Decisions

Record decisions that affect the book or inventory contracts. Do not use this
log to reinterpret application behavior.

| ID | Date | Decision | Rationale / evidence | Status |
|---|---|---|---|---|
| `decision:preserve-audit` | 2026-10-20 | Preserve the initial audit as a historical snapshot and add a dated review rather than rewriting its findings. | Required by the approved infrastructure specification; current cache-package presence differs from the audit snapshot. | Accepted |
| `decision:empty-inventories` | 2026-10-20 | Keep JSONL inventory files empty until records are generated from verified evidence. | No extractor has been implemented or run; empty files avoid implying completed analysis. | Accepted |
| `decision:per-record-schema` | 2026-10-20 | Define JSON Schema for each JSONL record and document cross-record integrity checks separately. | JSON Schema validates individual records; duplicate IDs and cross-file links require aggregate validation. | Accepted |
| `decision:inventory-sidecar-schema` | 2026-10-20 | Extend the schema contract to unresolved references, entry points, and external dependencies; validate each sidecar with the same record validator. | Regression reproductions showed missing fields and invalid enums in sidecars were accepted before the change. Contract ID advanced to v2. | Accepted |
| `decision:anchor-root-cache-ignore` | 2026-10-20 | Anchor the runtime cache ignore rule at repository root so `osm2terrn/cache/` is not accidentally ignored. | `git check-ignore` showed the former `cache/` rule matched package source; the inventory now detects it normally. | Accepted |
| `decision:independent-work-states` | 2026-10-20 | Separate inventory, analysis, documentation, and execution status fields on every record. | Contract v3 prevents AST generation from implying human review, editorial approval, or runtime success. | Accepted |
| `decision:bounded-control-flow-contract` | 2026-10-20 | Model located branch/exception syntax and class aggregation/composition relations without claiming a full CFG or runtime behavior. | Static AST can locate syntax; reachability, propagation and executed outcomes need semantic analysis or execution. | Accepted |
| `decision:claim-evidence-ids` | 2026-10-20 | Give significant claims and evidence stable IDs; store test/runtime context structurally. | Lines are locators; evidence type, path, description and execution metadata establish what supports a claim. | Accepted |
| `decision:unknown-xref-targets` | 2026-10-20 | Permit missing `target_path` for unknown, expected-missing, and unverifiable references while retaining original reference text. | Avoids fabricated paths and preserves the query for later resolution. | Accepted |

For future decisions, use a stable `decision:<slug>` identifier and record the
date, alternatives if relevant, evidence, consequences, and status. A decision
does not establish an implementation fact.
