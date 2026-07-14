---
## applyTo: "osm2terrn/**/*.py"
---
# Pipeline Rules

## Purpose

The pipeline defines the flow of data through the project.

Each stage has a single responsibility.

---

## Pipeline

Acquire
→ Parse
→ Validate
→ Build Domain Models
→ Process
→ Generate
→ Export

Each stage consumes the output of the previous stage.

---

## Stage Responsibilities

Acquire:

* retrieve source data

Parse:

* convert source data into internal structures

Validate:

* verify data integrity and consistency

Build Domain Models:

* create domain representations

Process:

* transform domain data

Generate:

* create terrain-related artifacts

Export:

* convert generated data into output formats

---

## Separation of Concerns

Stages should remain independent.

Avoid combining multiple pipeline stages within the same module.

---

## Dependencies

Later stages may depend on earlier stages.

Earlier stages must not depend on later stages.

Avoid circular dependencies.

---

## Validation

Validate data before passing it to the next stage.

Invalid data should fail early.

Avoid propagating invalid state through the pipeline.

---

## Data Flow

Pass structured data between stages.

Prefer domain models over unstructured data.

Avoid bypassing intermediate stages.

---

## Generation Rules

Keep pipeline behavior deterministic and reproducible.

Reuse existing pipeline stages before creating new ones.

Avoid duplicate processing logic.

Maintain a clear and traceable flow from acquisition to export.
