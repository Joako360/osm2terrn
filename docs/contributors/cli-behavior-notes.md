# CLI: behavior notes and improvement ideas

## Current behavior

- `load()` is a placeholder.
- Multiple stages use broad exception handling for resilience.
- Export depends on valid `bounds` in session state.

## Suggested improvements

1. Add explicit pre-export validation helpers.
2. Replace `print()` status with structured logger calls.
3. Implement `load()` for cached sessions.
4. Use typed exceptions and actionable error messages.
