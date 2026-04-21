# Troubleshooting: elevation and raster issues

## Elevation fetch failure
- Check network/API availability.
- Try a smaller bbox.
- Verify API env configuration if required.

## Flat/low-detail heightmap
- Confirm elevation data exists (not fallback only).
- Try a terrain area with stronger elevation variation.
- Inspect min/max elevation values in debug output.
