# Troubleshooting: roads export issues

## Roads `.tobj` not created
- Verify `OSM2TERRN_ORIGIN_LON/LAT` after download.
- Re-run download and export in same session.
- Add stage logging in `road_network_formatter.py`.

## Roads generated but look wrong
- Validate coordinate transforms.
- Compare outputs with and without merge stage.
- Inspect densification settings and source graph geometry.
