# Function reference: application entry and session

The declared entry point is `osm2terrn.app.main:main` in `pyproject.toml`;
`osm2terrn/__main__.py` delegates to it. Interactive callbacks are in
`osm2terrn/cli/commands.py`, and session state is in
`osm2terrn/app/app_state.py`. The former flat entry-module path is absent from
the current package tree.

For current call paths and evidence limits, see the
[execution map](../book/execution/README.md). The generated
[symbol inventory](../book/inventory/symbols.jsonl) provides AST-extracted
symbol names and line locators; it is not semantic verification.
