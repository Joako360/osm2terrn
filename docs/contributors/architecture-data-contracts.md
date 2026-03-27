# Architecture: data contracts

| Stage | Input | Output |
|---|---|---|
| Download | place/bbox | features + bounds |
| Elevation | bounds | elevation matrix + min/max |
| Terrain raster | bounds + elevation | `*_heightmap.png`, `*_groundmap.png` |
| Roads | place + origin | procedural roads `.tobj` |
| Terrain config | world params + raster names | `.otc` and paged `.otc` |
| Entrypoint | terrain metadata + object list | `.terrn2` |
