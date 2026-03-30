# `.terrn2` reference

## Purpose

`.terrn2` is the root terrain entrypoint. It should only contain metadata and references.

## Required `[General]` keys

- `Name`
- `GeometryConfig`
- `Gravity`
- `CategoryID`
- `Version`
- `GUID`

## Optional sections

- `[Authors]`
- `[Objects]`
- `[Scripts]`
- `[AssetPacks]`
- `[AI Presets]`

## Rules

- Do not place object instances or procedural geometry in `.terrn2`.
- Keep it small and reviewable.
