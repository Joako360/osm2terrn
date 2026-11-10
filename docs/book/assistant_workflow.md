# Assistant Workflow

## Roles

### GitHub Copilot

- Implements the approved documentary infrastructure and maintains inventory
  contracts and generated artifacts.
- Bases implementation statements on the current tree and cites paths/symbols.
- Labels static relations, inferences, runtime observations, uncertainties, and
  limitations distinctly.
- Does not infer successful tests from test names or documentation.
- Does not include secret values, local private data, or generated output in
  inventory records.

### ChatGPT/Codex

- Performs an independent review of audits, inventories, and proposed claims.
- Checks that cited evidence supports each claim and that historical/current
  states are not conflated.
- Reports unresolved questions and methodological limits.
- Does not claim a command or test passed without an execution result.

## Work cycle

1. Identify the repository revision/tree being examined and the task scope.
2. Read the applicable project instructions and existing documents.
3. Inspect evidence before drafting or editing; distinguish existing local
   changes from changes made in the current task.
4. Make only the approved documentation or inventory-contract changes.
5. Validate document links, schema shape, IDs, paths, and cross-record
   references to the extent supported by available tooling.
6. Record exact commands and outcomes. If a check was not run, say so.
7. Prepare a handoff with `templates/handoff.md`.
8. Request an independent review using `templates/review.md`.
9. Resolve or explicitly track findings before marking claims reviewed.

## Evidence rules

- Cite repository-relative paths, stable symbol IDs where available, and
  optional line numbers.
- Label syntactic relationships as static; label semantic guesses as inferred.
- Runtime observations must identify command, environment, and result.
- Keep `inventory_status`, `analysis_status`, `documentation_status`, and
  `execution_status` independent. Static extraction never advances execution
  status or editorial review.
- Assign stable `claim_id` values and cite stable `evidence_id` values for
  significant chapter claims. Evidence records for tests/runtime include
  command, test ID where applicable, environment, result, repository revision,
  and observation date.
- Keep `control_flow.jsonl` limited to located static syntax unless actual
  execution evidence supports a runtime observation; it is not a full CFG.
- A `references_test` relationship records a possible test association, not a
  passing test or complete coverage.
- Preserve historical snapshots and add dated reviews rather than silently
  updating old findings.

## Ownership and generated artifacts

Assign one owner per file within each work batch. Copilot owns schema/generator
maintenance; Codex supplies independent review. Do not edit generated inventory
records manually unless the exception is documented and regeneration will not
silently discard it. The static generator does not populate claim or
control-flow records and does not execute the application.

## Safe handling

Do not inspect or copy `.env` values, credentials, tokens, or private local
datasets. Inventory only safe names or categories when needed. Exclude virtual
environments, caches, logs, compiled artifacts, and generated terrain from
ordinary source inventory.
