# Technical Book Style Guide

This guide defines how to explain the current OSM2Terrn implementation as
study material. It complements the repository inventory contract in
`inventory/README.md` and the assistant coordination rules in
`assistant_workflow.md`; it does not replace either one.

## Audience and purpose

Assume the reader knows basic Python and programming fundamentals, but may not
know the project's domain libraries or geospatial concepts. Introduce concepts
when they become necessary, then connect each concept to the concrete code
that uses it. The book is a guided explanation of implementation, not a user
manual, API listing, design proposal, or annotated copy of source files.

## Chapter structure

Use `templates/chapter.md` as the canonical template. Adapt it to the process
being studied; do not add empty headings merely to match another chapter.

| Element | Requirement | Guidance |
|---|---|---|
| Title and metadata | Required | Stable `chapter:<slug>` ID, scope, statuses, inspected revision/date, author/reviewer, and inventory scope. |
| Purpose and scope | Required | State what is explained and excluded. Bound the route or subsystem. |
| Learning goals | Required | Use observable outcomes such as trace, compare, explain, or predict. |
| Prerequisites and concepts | Required when needed | Define domain terms before relying on them; avoid re-teaching familiar basics. |
| Architecture location and entry route | Required | Show where the selected process begins and ends, with evidence. For a library-only algorithm, identify its caller and consumers instead of inventing a CLI route. |
| Detailed source walkthrough | Required | Explain responsibilities, inputs, transformations, outputs/mutations, collaborators, and important branches. |
| Data flow and contracts | Required when data crosses boundaries | Name actual types and fields; distinguish absent, empty, invalid, and failed values where code does. |
| Errors and alternatives | Required | Cover relevant conditions, early returns, fallbacks, exceptions, and continuation behavior. |
| Dependencies | Required when material | Distinguish project code from library behavior; do not attribute undocumented internals to the project. |
| Examples | Recommended | Mark examples as source-derived, synthetic/conceptual, or captured execution. Never present a synthetic value as observed output. |
| Diagrams | Recommended; required for multi-step or branching processes | Select a suitable Mermaid type. Keep diagram relations and evidence class explicit. |
| Exercises and expected checks | Required | Every exercise has an objective, task, answer/check guide, and static-versus-execution label. |
| Self-assessment | Recommended | Ask questions that test the core model, branches, and evidence boundaries; provide a guide. |
| Limitations and open questions | Required | Link tracked question IDs and state what evidence would close each issue. |
| Claims and evidence | Required for significant technical assertions | Use stable claim/evidence IDs in the authored claim stream and precise source locators. |
| Review record | Required | Leave pending fields explicit until an actual review is recorded. |

Sections may be combined when that improves comprehension. Processing chapters
may need algorithm steps, numerical examples, units, invariants, and boundary
cases. Acquisition chapters may need provider, retry, cache, and response-state
sections. Export chapters may need serialization and output-contract sections.
These are topic-specific additions, not universal requirements.

## Explain implementation progressively

For each central component, answer the relevant questions in this order:

1. What problem does it address in this route?
2. What calls or constructs it, and what does it receive?
3. What representation and transformations does it use?
4. What does it return, mutate, persist, or pass onward?
5. What conditions select alternate behavior or failure paths?
6. What downstream code depends on the result?
7. What can be concluded from source, tests, and actual execution separately?

Explain only the details needed to reconstruct the behavior. Use short source
excerpts sparingly and interpret them; do not paraphrase every line. When an
algorithm matters, name its inputs, invariant/decision, and result, and walk
through a small synthetic example without implying an application run.

## Fidelity and certainty

- Current source is authoritative for current implementation claims. Cite
  disagreements with prior documents and preserve historical findings.
- Label claims as `fact`, `inference`, or `runtime_observation` according to
  the claim contract. State narrower certainty in prose where helpful.
- A source branch proves that the branch is implemented, not that it was
  reached in a real run. A test definition proves the case is represented, not
  that the test passed. A passing test proves only its exercised scope.
- Record the command, environment, result, repository revision, and UTC
  observation timestamp for execution evidence as required by the inventory
  contract. Never infer them from a test name or report date.
- Do not call a static AST relation a runtime call graph. Mark unresolved
  dynamic dispatch, callbacks, plugin behavior, reflection, or external
  library internals as limitations when relevant.
- Do not claim completeness when extraction limits, dynamic paths, excluded
  files, or unreviewed branches remain.

## Code references and traceability

- Write repository-relative paths with `/` separators, followed by a symbol
  name where one is known, for example
  `osm2terrn/data/osm_data_handler.py::download_data_from_bbox()`.
- Add `#L<start>` or `#L<start>-L<end>` as a secondary locator. Keep ranges
  narrow enough to identify the evidence and recheck them after source edits.
- Link local Markdown references using paths relative to the referring file.
- Give every significant, independently checkable technical assertion a
  stable claim ID and one or more evidence IDs. Keep the prose claim, claim
  record, evidence locator, and chapter link consistent.
- Use symbol IDs from the generated inventory when available; do not make line
  numbers part of IDs. If extraction cannot identify a symbol, retain a file
  locator and explain the limitation.
- Keep the four record status axes independent. Drafting does not imply
  analysis review, approval, test success, or runtime verification.

## Diagrams

- Put chapter diagrams under `chapters/diagrams/`; give each a stable
  `diagram:<slug>` ID and link it from the chapter.
- State whether it represents imports, static calls, inheritance, inferred
  control/data flow, or recorded execution. Include source symbols, evidence,
  generation method if applicable, omissions, and review status in comments or
  the chapter.
- Use decisions for actual conditions, annotate branches with the condition,
  show meaningful early returns and exception boundaries, and distinguish
  per-item outcomes from overall outcomes.
- Do not collapse valid empty data, missing data, and errors unless the source
  does. Do not draw unverified external-library internals as project behavior.
- Prefer a flowchart for branching control/data flow, a sequence diagram for
  interactions over time, and a class diagram only for relevant structural
  relationships. Keep diagrams scoped and aligned with prose.
- A diagram is not tool-validated unless a parser/renderer was actually run.

## Examples, exercises, and answers

Label each example as one of:

- **Source-derived:** a value or structure directly read from code/config.
- **Synthetic:** fabricated input used to explain a transformation or branch.
- **Execution observation:** captured from a reproducible run with recorded
  evidence; include command, environment, revision, and result.

Every exercise includes its learning objective, instructions, expected answer
or a checkable method, and whether source inspection suffices or execution is
required. Expected checks must say what symbol, variable, test assertion, or
output to inspect. If execution is unsafe, unavailable, or outside scope, say
so and do not invent an output.

## Review and publication

Keep a chapter `draft` until an independent reviewer checks scope, source
claims, tests, limits, diagram, and teaching sequence. Use `reviewed` or
`approved` only with the evidence required by the inventory contract. Record
substantive objections as findings with severity, locator, impact, and
recommended correction; preserve historical verdicts and add dated follow-up.
