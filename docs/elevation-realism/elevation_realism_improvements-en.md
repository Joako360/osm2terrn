# Realistic Elevation and Water Level Adjustments

This document describes the improvements implemented to make map height levels and water levels more realistic in OSM2terrn.

## 🎯 Main Changes

### 1. **Dynamic Height Scaling (WorldSizeY)**

**Before:** The world height (WorldSizeY) was hardcoded to 250-300 meters, regardless of actual elevation differences.

**Now:** It is dynamically calculated as the direct difference between elevations:

```
WorldSizeY = max_elevation - min_elevation
```

Example: Terrain with 45m-235m elevation
```
WorldSizeY = 235 - 45 = 190m
```

Limits are respected: minimum 50m, maximum 10km.

### 2. **Realistic Water Level**

**Before:** Water was always set at WaterLine=0.0, creating unrealistic behavior in high-altitude or inland areas.

**Now:** It is automatically detected as the negative of the minimum elevation, using sea level (0) as the reference point:

```
WaterLine = -min_elevation
WaterBottomLine = WaterLine - water_depth (150m by default)
```

Example: Terrain with 45m-235m elevation
```
WaterLine = -45m
WaterBottomLine = -195m
Result: The terrain appears to have a real height of 190m (ranging from -45m to 145m)
```

### 3. **Improved Return Information**

The `generate_heightmap_n_texture()` function now returns elevation statistics:
```python
{
    'min_elevation': float,      # Minimum elevation in meters
    'max_elevation': float,      # Maximum elevation in meters
    'elevation_range': float,    # Elevation range
}
```

## 📦 Modified Files

### New Files
- **[osm2terrn/utils/elevation_utils.py](../../osm2terrn/utils/elevation_utils.py)**
  - Functions for calculating realistic water levels
  - Dynamic world height calculation
  - Elevation parameter normalization

### Updated Files
- **[osm2terrn/utils/constants.py](../../osm2terrn/utils/constants.py)**
  - New constants for realistic configuration
  - Adjustable parameters for elevation scaling
  - Realistic water configuration settings

- **[osm2terrn/processing/heightmap_handler.py](../../osm2terrn/processing/heightmap_handler.py)**
  - `generate_heightmap_n_texture()` now returns elevation statistics
  - Improved parameter documentation

- **osm2terrn/processing/otc_exporter.py**
  - New function `calculate_world_size_y()`
  - Dynamic height calculation based on real-world data

- **osm2terrn/processing/terrn2_exporter.py**
  - New function `prepare_water_config()`
  - Support for `elevation_stats` parameter
  - Realistic water calculation during TERRN2 export

- **osm2terrn/main.py**
  - Captures elevation statistics
  - Handles dynamic WorldSizeY calculation
  - Passes elevation data to exporters
  - Improved informative progress output

## ⚙️ Configuration

The new features are controlled via constants in osm2terrn/utils/constants.py:

```python
# Enable dynamic elevation scaling
ENABLE_REALISTIC_ELEVATION = True

# Enable automatic water level calculation
ENABLE_REALISTIC_WATER = True

# Default water depth (meters)
WATER_DEPTH_DEFAULT = 150.0

# World height limits
MIN_WORLD_SIZE_Y = 50.0      # Minimum 50 meters
MAX_WORLD_SIZE_Y = 10000.0   # Maximum 10 kilometers
```

## 🔧 How It Works

### Improved Export Flow

```
1. Download OSM and elevation data
   ↓
2. generate_heightmap_n_texture() generates maps
   ├─ Calculates elevation statistics
   └─ Returns min/max/range
   ↓
3. otc_exporter calculates realistic WorldSizeY
   └─ calculate_world_size_y(min_elev, max_elev)
   ↓
4. terrn2_exporter calculates realistic water levels
   └─ prepare_water_config(elevation_stats)
   ↓
5. Exports .otc and .terrn2 files with realistic values
```

## 📊 Result Examples

### Mountainous Terrain (Andes)
```
min_elevation: 2500m
max_elevation: 4200m
WorldSizeY: 1700m (4200 - 2500)
WaterLine: -2500m
WaterBottomLine: -2650m (depth 150m)
Apparent height: 1700m from the water level
```

### Flat Terrain (Plains)
```
min_elevation: 50m
max_elevation: 120m
WorldSizeY: 70m (120 - 50)
WaterLine: -50m
WaterBottomLine: -200m
Apparent height: 70m from the water level
```

### Urban Terrain (Coastal)
```
min_elevation: 0m (sea level)
max_elevation: 150m
WorldSizeY: 150m (150 - 0)
WaterLine: 0m (sea level)
WaterBottomLine: -150m
Apparent height: 150m from the water level
```

### Intermediate Urban Terrain
```
min_elevation: 45m
max_elevation: 235m
WorldSizeY: 190m (235 - 45)
WaterLine: -45m
WaterBottomLine: -195m
Apparent height: 190m from the water level
```

## ✅ Validation

To verify that the new features are working correctly:

1. Download an urban or mountainous map.
2. Export the terrain.
3. Check the generated files:
   - `.otc` should have a realistic `WorldSizeY` (it won't always be 300).
   - `.terrn2` should have a `WaterLine` that matches the local topography.

## 🚀 Possible Future Improvements

- Automatic detection of significant water bodies for realistic placement.
- Integration with sea-level data based on geographic location.
- Procedural generation of waterfalls on steep terrain.
- Realistic slope calculation for determining visual erosion.

## 📝 Notes

- Accuracy depends on the quality of elevation data from OpenTopography.
- Calculations assume projections are in meters (UTM).
- Safety margins can be adjusted based on artistic requirements.