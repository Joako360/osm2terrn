# Independent Reviews

Use this directory for review records created from `../templates/review.md`.
The original Etapa 1.4 infrastructure audit verdict is preserved in
`phase-1-4-infrastructure-audit.md`; dated follow-ups record subsequent
changes. Read its latest follow-up for the current H1-H5 status. Independent
review is still required before treating contract changes as approved.

The inventory-generator audit is recorded in
`inventory-generator-audit.md`. Its approval applies to the initial static
generator workflow only; it does not establish runtime coverage or completion
of the technical book.

The independent v3 contract review is `contract-v3-independent-review.md`.
Its original verdict records four reproducible findings; a dated follow-up
records implemented corrections, and the independent follow-up on 2026-10-20
found residual edge cases N1-N4. A later implementation follow-up records
fixes and regression results. The final independent follow-up on 2026-10-20
approves beginning functional analysis with limitations; historical
**REQUIERE CORRECCIONES** verdicts remain preserved. Runtime evidence is not
authenticated by the validator, and empty later-stage streams do not establish
coverage. See the latest sections before proceeding.

## Review process

1. Assign a stable review ID and identify the inspected repository revision or
   dated tree.
2. Review claims against their cited files/symbols; do not rely solely on a
   summary or another assistant's conclusions.
3. Record findings with priority, evidence, impact, verdict, and suggested
   action.
4. Distinguish a documentation defect from a product defect. This book
   workflow does not authorize product changes.
5. Record commands and exact outcomes if any are run. An unrun test is not a
   passing test.
6. Keep unresolved findings visible; update coverage only after the review
   outcome is recorded.

Review records provide evidence of review, not proof that all behavior or
branches were covered.
