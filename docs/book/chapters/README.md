# Chapter Workspace

The chapter tree contains one scoped pilot:
[OSM bounding-box acquisition](01-osm-bbox-acquisition.md). It is the
methodological reference for structure, evidence labeling, source walkthrough,
diagram scope, synthetic examples, exercises, and answer guides. It remains a
`draft`; using it as a reference does not approve every technical claim or
establish execution behavior.

Preparatory research for the proposed elevation chapter is recorded in
[`../research/02-elevation-processing-research.md`](../research/02-elevation-processing-research.md).
It is an implementation map and open-questions record, not chapter 02; the
chapter remains `not_started` until a draft is actually created.

## Authoring standard

- Follow [`../STYLE_GUIDE.md`](../STYLE_GUIDE.md) for reusable quality rules.
- Use [`../templates/chapter.md`](../templates/chapter.md) as the canonical
  adaptable template.
- Follow [`../WORKFLOW.md`](../WORKFLOW.md) for source reconstruction,
  evidence gates, review, and handoff.
- `../assistant_workflow.md` separately defines Copilot/Codex roles and
  coordination. Do not duplicate those role rules in individual chapters.
- Follow [`diagrams/README.md`](diagrams/README.md) for diagram metadata and
  certainty conventions.

## Before drafting

1. Select and bound a real source route or algorithm; record its caller,
   consumer, exclusions, revision/date, and unresolved edges.
2. Inspect current implementation and relevant test source directly. Generated
   inventories are discovery aids, not human-reviewed explanations.
3. Give each significant claim stable claim/evidence IDs and current source
   locators; distinguish source, test-source, execution, and external evidence.
4. Explain the process progressively for a reader with basic Python knowledge.
   Adapt sections to the topic instead of copying the pilot's exact outline.
5. Add a diagram when it clarifies a multi-step or branching route; show only
   supported relations and label static, inferred, or observed status.
6. Include exercises with answer/check guides and state whether inspection or
   execution is required.
7. Update progress and request an independent review using the existing
   handoff/review templates.

## Chapter status and review

The pilot's claims remain `draft` / `not_verified`; its source-based analysis
and execution status are tracked independently. No chapter may be marked
`reviewed` or `approved` until a reviewer has checked the claims, cited code,
test evidence, diagram, pedagogy, and limitations and the inventory contract's
review evidence requirements are met. Do not label static inspection, test
definitions, or a diagram as runtime verification.

Update [`../progress/coverage.md`](../progress/coverage.md) whenever chapter
scope, evidence, review, or status changes. Proposed topics in
[`../book_plan.md`](../book_plan.md) remain candidates until source inspection
confirms a useful scope.

## Reference-pilot conformance snapshot

This is a structural/pedagogical comparison against the book standard, not a
new independent technical approval of the chapter:

| Standard area | Pilot assessment | Boundary |
|---|---|---|
| Scope, learning goals, prerequisites, and source map | Present | Appropriate to a provider/acquisition topic. |
| Concepts, data contracts, transformations, and source walkthrough | Present with substantial source detail | Review each technical statement against current source when the chapter is next revised. |
| Branches, errors, cache, retries, and integration boundaries | Present | Static source paths and test-source references are explicitly distinguished from executed results. |
| Diagram | Present and labeled inferred/static | Mermaid rendering was not independently established by this structural comparison. |
| Synthetic example and exercises with expected checks | Present | Expected checks are source-derived; no fabricated runtime output is claimed. |
| Claims, evidence IDs, and source locators | Present | Five claims remain `draft` / `not_verified`; their presence is not an independent evidence review. |
| Independent review and runtime verification | Pending/partial | Do not infer technical approval, application execution, live-provider behavior, or simulator compatibility. |

The pilot is therefore a useful **method reference** for future drafts, not a
fully verified chapter and not a mandate to reproduce its length or exact
section layout.

## Stage 3 source map

The current static execution reconstruction is indexed in
[`../execution/README.md`](../execution/README.md). It supports study planning;
it is not a completed chapter, general runtime proof, or replacement for
chapter-specific source review.
