# CLI: download flow (`dlcity`)

`dlcity()` is the interactive download callback. The following is a static
source description, not a claim that providers or the complete UI route were
executed.

1. Runs the download menu. A manually entered bbox currently returns an empty
   place label; the callback returns early unless both place and bbox are
   truthy, so that selection does not reach the downloader (`download_menu.py`,
   `commands.py`).
2. For an accepted selection, calls `download_data_from_bbox(bbox)` and stores
   the returned bundle, place and origin in the application session state.
3. Calls the elevation prefetch path after acquisition. The
   `pipeline.preload_elevation` option is parsed, but this callback does not
   consult it in the inspected source.
4. Layer results distinguish `not_requested`, `empty`, `available` and
   `failed`; failure does not mean an empty successful result.

Provider responses and application execution have not been established by
this source map. The session behavior after cancel/invalid selection and
subsequent export remains an open question.
