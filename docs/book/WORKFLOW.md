# Chapter Authoring Workflow

Use this workflow with `STYLE_GUIDE.md`, `templates/chapter.md`,
`assistant_workflow.md`, and the inventory contracts. It describes work
controls, not an assertion that any unrecorded analysis or verification has
occurred.

## 1. Select and bound a process

- Choose a real route, algorithm, data contract, or output boundary visible in
  the current repository.
- State its starting event/caller and stopping point/consumer.
- Use inventory and execution maps as discovery aids only; check candidate
  boundaries against current source.
- Record scope, exclusions, likely dependencies, and open questions before
  drafting. Split broad topics only when source boundaries and learning goals
  support it.

**Gate:** no chapter begins with an assumed architecture or an unbounded
"whole subsystem" scope.

## 2. Identify source, tests, and revision

- Record the current Git revision when available, working-tree state, and
  inspection date. Do not attribute pre-existing edits to the current work.
- Locate entry points/callers, definitions, consumers, configuration, data
  types, serializers/cache, and relevant tests using repository search and
  inventory IDs where available.
- Read the source for each key path. Confirm that generated locators match the
  current tree; discover tests separately from test results.
- Exclude secrets, local data, caches, generated assets, and unrelated files.

**Gate:** each intended claim has a candidate evidence path/symbol; unresolved
or dynamically dispatched edges are listed, not guessed.

## 3. Reconstruct the route

- Trace calls and data in order from the selected boundary.
- Record concrete input/output types, field meanings, coordinate units/CRS,
  mutation, persistence, and conversion points when applicable.
- Enumerate guards, branch predicates, early returns, loops, exception scopes,
  fallback behavior, and overall status aggregation.
- Separate what project code controls from behavior delegated to dependencies.
- Keep static call/data relations distinct from inferred route reachability and
  from observed execution.

**Gate:** a reviewer should be able to follow the normal path and important
alternatives from the cited source without filling a major gap by assumption.

## 4. Plan evidence and verification

- Write proposed claims in checkable units and associate each with stable
  evidence IDs and narrow file/symbol/line locators.
- Classify evidence as source, test source, test execution, runtime observation,
  external integration, or other type supported by the schema.
- Define safe, scoped checks only when needed. Identify mocks for network,
  filesystem, GUI, or costly operations. Do not run side-effectful operations
  without authorization.
- Record unavailable verification and the condition needed to close it.

**Gate:** no test reference is worded as a passing test without a recorded
execution result; no static conclusion is worded as runtime behavior.

## 5. Draft for learning

- Fill the canonical template, adapting optional sections to the topic.
- Introduce needed theory before the source operation that uses it.
- Explain purpose, inputs, internal transformations, outputs, collaborators,
  and error/alternate paths for central components.
- Add a small labeled synthetic or source-derived example where it clarifies
  the model; do not fabricate observed output.
- Add exercises and expected checks; mark static-only versus execution-needed.
- Link questions, evidence records, source symbols, tests, and related chapters.

**Gate:** the chapter teaches a coherent model rather than listing symbols or
repeating source line by line.

## 6. Create and check diagrams

- Choose diagram type based on the relationship being explained.
- Draw only source-backed or explicitly labeled inferred edges. Include
  significant decisions, early returns, errors, and output-state distinctions.
- Annotate relation type, source symbols, evidence, omissions, and validation
  method using the diagram conventions.
- Check the diagram against the prose branch by branch. Run a Mermaid parser
  only if one is available and allowed; report manual review separately.

**Gate:** no edge or outcome is more certain than its evidence, and the diagram
does not introduce a route omitted from the source walkthrough.

## 7. Update claims, status, and progress

- Add or update authored claim/evidence records without changing generated
  streams by hand. Preserve stable IDs and validate schema/cross-references.
- Update chapter index and coverage with scope, evidence, status, date/revision,
  next action, and limitations.
- Keep inventory, analysis, documentation, and execution statuses
  independent. Status changes require their defined evidence.
- Preserve historical reports and add dated follow-ups instead of rewriting
  them to match current conclusions.

**Gate:** chapter prose, claim stream, diagram, inventory references, and
progress table agree; no status advances merely because a file exists.

## 8. Independent technical and pedagogical review

The author supplies a handoff using `templates/handoff.md`. A reviewer who did
not author the relevant claims checks:

- current source and test locators;
- normal/alternate/error paths and external-library boundaries;
- claim/evidence sufficiency and status accuracy;
- diagram-to-code and prose-to-diagram agreement;
- prerequisites, explanatory progression, examples, exercises, answers, and
  remaining learning gaps;
- links, schema, IDs, and safe handling.

Record findings using `templates/review.md`. Resolve critical/high findings
before approval; preserve the old verdict and append a dated follow-up. A
review of static claims does not establish execution or external compatibility.

## 9. Final checks and handoff

Run only checks authorized for the task. Depending on scope, check Markdown
links, line locators, JSONL/schema/integrity, diagram syntax, documentation
tests, and whitespace. Report commands and exact outcomes. Do not claim a check
that was not run; identify checks not available or not safe.

The handoff names changed files, scope, evidence/revision, checks and results,
open issues, pre-existing worktree caveats, and the next reviewer action.
