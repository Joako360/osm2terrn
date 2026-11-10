# Review: <subject>

## Metadata

- ID: `review:<slug>`
- Subject: <document, inventory batch, or chapter>
- Inspected revision/date: <revision or date>
- Reviewer: <name/assistant>
- Review date: <date>
- Claim IDs reviewed: <claim IDs, or `None`>
- Evidence IDs checked: <evidence IDs>

## Scope and method

- Files/claims reviewed: <paths, symbols, IDs>
- Commands executed: <exact commands and results, or `None`>
- Exclusions and limitations: <what was not checked>

## Findings

For each finding, use:

### `<finding-id>` — <priority>

- Claim under review: <claim>
- Evidence IDs and locators: `<ev:id>` plus `<repository-relative path>::<symbol>` (line range is a locator)
- Impact: <why it matters>
- Verdict: `confirmed` | `partially_supported` | `unsupported` | `unresolved`
- Status changes supported by this review: <inventory/analysis/documentation/execution axes, or `None`>
- Suggested action: <documentation-only action or follow-up question>

If there are no findings, state `No findings` and describe the reviewed scope;
do not imply exhaustive coverage unless it was established.

## Overall verdict

`accepted` | `accepted_with_open_questions` | `changes_requested` | `blocked`

## Follow-up

- <owner, action, and closure condition, or `None`>
