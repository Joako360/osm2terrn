# Quick Start Guide: Realistic Elevation and Water Levels

## 🎯 What Changed?

Generated maps now have:
- **Realistic height**: The vertical size of the terrain (WorldSizeY) is automatically calculated based on actual elevation differences
- **Realistic water**: The water level (WaterLine) is automatically placed at the appropriate level according to topography

## 🚀 Usage

**No changes required to your normal workflow:**

```
1. Run main.py
2. Download a city
3. Export the terrain
↓
Realistic values are calculated automatically ✅
```

## 📊 Example Output

```
✅ Export complete:
   📊 Elevation range: 45.50m - 235.80m
   📏 World height (Y): 190.30m
   📁 Output files:
     - output/MyCity.terrn2
     - output/MyCity.otc
     - output/MyCity-page-0-0.otc
     - output/MyCity_heightmap.png
     - output/MyCity_groundmap.png
     - output/MyCity.tobj
```

In the `.terrn2` file you'll see:
```
WaterLine = -45.50
WaterBottomLine = -195.50
```

## ⚙️ Configuration (Optional)

If you want to adjust the behavior, edit [osm2terrn/utils/constants.py](../osm2terrn/utils/constants.py):

```python
# Disable realistic scaling (reverts to default values)
ENABLE_REALISTIC_ELEVATION = False

# Disable automatic water level calculation
ENABLE_REALISTIC_WATER = False

# Adjust water depth (meters)
WATER_DEPTH_DEFAULT = 150.0

# Adjust height limits
MIN_WORLD_SIZE_Y = 50.0
MAX_WORLD_SIZE_Y = 10000.0
```

## 📝 Technical Details

### WorldSizeY Calculation

The vertical size of the terrain is simply the difference between maximum and minimum elevation:

```
WorldSizeY = max_elevation - min_elevation
Limits: 50m min, 10km max
```

**Example:** Terrain with elevation 45m-235m
```
WorldSizeY = 235 - 45 = 190m
```

### WaterLine Calculation

The water level is placed at the negative of the minimum elevation, making sea level (0) the reference:

```
WaterLine = -min_elevation
WaterBottomLine = WaterLine - water_depth (150m by default)
```

**Example:** Terrain with elevation 45m-235m
```
WaterLine = -45m
WaterBottomLine = -45 - 150 = -195m
Result: The terrain appears 190m tall from water (-45m to 145m)
```

## ✅ Validation

Verify the generated values in `.otc` and `.terrn2` files:

**In `.otc`:**
```
WorldSizeY=190   ← Real difference: max - min
```

**In `.terrn2`:**
```
WaterLine = -45.50        ← Negative of minimum elevation
WaterBottomLine = -195.50 ← WaterLine - depth (150m)
```

**Realism verification:**
- WorldSizeY must be exactly (max_elevation - min_elevation)
- WaterLine must be -min_elevation
- Terrain must appear from WaterLine to WaterLine + WorldSizeY

## 🎨 Expected Results

| Terrain | Elev. Range | WorldSizeY | WaterLine | Apparent |
|---------|-------------|-----------|-----------|----------|
| Mountain | 2500-4200m | 1700m | -2500m | 1700m from water |
| Plain | 50-120m | 70m | -50m | 70m from water |
| Coast | 0-150m | 150m | 0m | 150m from water |
| Urban | 45-235m | 190m | -45m | 190m from water |

## 💡 Tips

1. **For very flat terrain**: Uses minimum (50m) to avoid rendering issues
2. **For very tall terrain**: Limited to 10km to avoid memory problems
3. **Adjust manually** if you want a different artistic effect (edit `.terrn2` and `.otc`)

## 📚 More Information

See [elevation_realism_improvements-en.md](./elevation-realism/elevation_realism_improvements-en.md) for complete technical details.
