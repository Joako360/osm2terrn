# Diagram Conventions

No diagrams are currently claimed as generated or reviewed.

Every diagram must have a stable ID in the form `diagram:<slug>` and state:

- what relation it represents: imports, static calls, inheritance, inferred
  flow, or observed execution;
- the source files and symbols used;
- whether the diagram is static, inferred, or based on recorded execution;
- generation method/tool and relevant version, if generated;
- unresolved edges and known omissions;
- review date and status.

Do not label AST-derived edges as runtime calls. Do not imply that a test
reference or an unexecuted pipeline is observed behavior. Use
`runtime_observed` only when a command, environment, and result are recorded.
Link the diagram from its owning chapter and include its evidence references
there as well.

The Stage 3 source-based flow map is stored at
`../../execution/diagrams/application-flow.mmd`. It is a static/inferred
application route, not a runtime observation or a chapter-owned diagram.
