---
applyTo: "tests/**/*.py"
---
# Testing Rules

Framework:

* pytest

## Coverage

Generate tests for:

* public functions
* public methods
* business logic
* parsers
* exporters
* geometry calculations
* coordinate transformations

Do not generate tests for:

* constants
* trivial getters
* simple dataclasses

## Test Design

Prefer behavior testing over implementation testing.

Each feature should test:

* expected behavior
* edge cases
* invalid inputs
* error conditions

## Maintenance

When production code changes:

* update affected tests
* remove obsolete tests
* keep test names descriptive

## Exporters

Validate:

* required fields
* output format
* numeric precision
* deterministic ordering

## General Rules

* One responsibility per test.
* Keep tests independent.
* Avoid duplicated test logic.
* Use fixtures when appropriate.
* Prefer parametrized tests for repeated scenarios.
* Avoid testing private methods directly.