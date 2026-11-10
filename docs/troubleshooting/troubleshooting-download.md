# Troubleshooting: download issues

## `No place or bounding box selected`
- Re-run CLI and complete prompts.
- Validate manual bbox format.

## Overpass errors or incomplete OSM data

The bbox downloader requests buildings, parks, lakes, roads, and rails
independently. A failed layer is not treated as an empty result. Successful
layers, including valid empty results, are cached independently and can be
reused on a later run when another layer failed.

The downloader retries temporary HTTP errors (408, 425, 429, and 5xx),
connection errors, and timeouts up to three total attempts per layer. Retries
use exponential full jitter, capped at 30 seconds, and honor a valid
`Retry-After` header when it fits within the 120-second per-layer time budget.
Permanent 4xx errors are not retried. OSMnx's internal 429/504 retry path is
intercepted so it cannot add unbounded retries.

Configure the primary endpoint with `OVERPASS_URL`. Optional alternate
endpoints can be provided as a comma-separated list in
`OVERPASS_ALTERNATE_URLS`; attempts cycle through the configured endpoints.
`OVERPASS_MAX_ATTEMPTS` and `OVERPASS_MAX_ELAPSED_SECONDS` set the per-layer
limits. Endpoint values must be HTTP(S) URLs without credentials, query
parameters, or fragments. See `.env.example` for the defaults.

Overpass capacity and availability remain outside the application's control.
Do not increase the query area to work around provider saturation. Check the
layer-specific failure diagnostic and try again later; cached successful
layers are reused.
