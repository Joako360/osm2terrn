---
applyTo: "docs/**/*.md"
---

# Documentation — Copilot-Optimized Instructions

## Objective
Help GitHub Copilot write clear, accurate, and consistent documentation for OSM2terrn. This file defines rules for docs content in `docs/`; implementation and exporter behavior belong in code files and in other specialized instruction files.

---

### Content Rules
- All documentation must be in **English**.
- Use plain language, short paragraphs, headings, and bullet lists.
- Prefer active voice and direct guidance.
- Use code formatting for filenames, commands, config keys, and short snippets.
- Keep docs concise and topic-focused; avoid broad history or unrelated detail.
- For exporter-specific docs, refer to `.github/instructions/exporters.instructions.md`.

## Scope
- Docs should explain project workflows, configuration, usage, and contributor guidance.
- Do not use docs for low-level implementation details or algorithm design.
- Refer readers to source files when they need exact code behavior.

## Contribution & Maintenance
- Prioritize clarity and maintainability.
- Keep docs short, focused, and easy to scan.
- Avoid duplicate guidance across files.
- Link to existing docs pages instead of repeating content.

## Structure
- Start each docs file with a top-level heading `#`.
- Use `##` and `###` headings to organize sections.
- Keep one main idea per paragraph.
- Use tables or lists to compare related concepts.
- Prefer repo paths and commands over external URLs.

