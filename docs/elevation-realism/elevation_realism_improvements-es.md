# Ajustes Realistas de Altura y Agua

Este documento describe las mejoras implementadas para hacer que los niveles de altura del mapa y el nivel del agua sean más realistas en OSM2terrn.

## 🎯 Cambios Principales

### 1. **Escalado Dinámico de Altura (WorldSizeY)**

**Antes:** La altura del mundo (WorldSizeY) estaba hardcodeada en 250-300 metros sin relación con las elevaciones reales.

**Ahora:** Se calcula dinámicamente como la diferencia directa entre elevaciones:

```
WorldSizeY = max_elevation - min_elevation
```

Ejemplo: Terreno con 45m-235m de elevación
```
WorldSizeY = 235 - 45 = 190m
```

Se respetan límites: mínimo 50m, máximo 10km.

### 2. **Nivel de Agua Realista**

**Antes:** El agua siempre estaba en WaterLine=0.0, creando un comportamiento poco realista.

**Ahora:** Se detecta automáticamente como el negativo de la elevación mínima, usando el nivel del mar (0) como referencia:

```
WaterLine = -min_elevation
WaterBottomLine = WaterLine - water_depth (150m por defecto)
```

Ejemplo: Terreno con 45m-235m de elevación
```
WaterLine = -45m
WaterBottomLine = -195m
Resultado: El terreno aparenta altura real 190m (desde -45m hasta 145m)
```

### 3. **Información de Retorno Mejorada**

La función `generate_heightmap_n_texture()` ahora retorna estadísticas de elevación:
```python
{
    'min_elevation': float,      # Elevación mínima en metros
    'max_elevation': float,      # Elevación máxima en metros
    'elevation_range': float,    # Rango de elevación
}
```

## 📦 Archivos Modificados

### Nuevos Archivos
- **[src/utils/elevation_utils.py](src/utils/elevation_utils.py)**
  - Funciones para calcular niveles de agua realistas
  - Cálculo dinámico de altura del mundo
  - Normalización de parámetros de elevación

### Archivos Actualizados
- **[src/utils/constants.py](src/utils/constants.py)**
  - Nuevas constantes para configuración realista
  - Parámetros ajustables para escala de elevación
  - Configuración de agua realista

- **[src/processing/heightmap_handler.py](src/processing/heightmap_handler.py)**
  - `generate_heightmap_n_texture()` ahora retorna estadísticas de elevación
  - Mejor documentación de parámetros

- **[src/processing/otc_exporter.py](src/processing/otc_exporter.py)**
  - Nueva función `calculate_world_size_y()`
  - Cálculo dinámico de altura basado en datos reales

- **[src/processing/terrn2_exporter.py](src/processing/terrn2_exporter.py)**
  - Nueva función `prepare_water_config()`
  - Soporte para parámetro `elevation_stats`
  - Cálculo de agua realista en exportación TERRN2

- **[src/main.py](src/main.py)**
  - Captura de estadísticas de elevación
  - Cálculo dinámico de WorldSizeY
  - Paso de datos de elevación a exportadores
  - Mejor salida informativa del progreso

## ⚙️ Configuración

Las nuevas características se controlan mediante constantes en `src/utils/constants.py`:

```python
# Habilitar escalado dinámico de elevación
ENABLE_REALISTIC_ELEVATION = True

# Habilitar cálculo automático de nivel de agua
ENABLE_REALISTIC_WATER = True

# Profundidad del agua por defecto (metros)
WATER_DEPTH_DEFAULT = 150.0

# Límites de altura del mundo
MIN_WORLD_SIZE_Y = 50.0      # Mínimo 50 metros
MAX_WORLD_SIZE_Y = 10000.0   # Máximo 10 kilómetros
```

## 🔧 Cómo Funciona

### Flujo de Exportación Mejorado

```
1. Descarga datos OSM y elevación
   ↓
2. generate_heightmap_n_texture() genera mapas
   ├─ Calcula estadísticas de elevación
   └─ Retorna min/max/rango
   ↓
3. otc_exporter calcula WorldSizeY realista
   └─ calculate_world_size_y(min_elev, max_elev)
   ↓
4. terrn2_exporter calcula agua realista
   └─ prepare_water_config(elevation_stats)
   ↓
5. Exporta archivos .otc y .terrn2 con valores realistas
```

## 📊 Ejemplos de Resultado

### Terreno Montañoso (Andes)
```
min_elevation: 2500m
max_elevation: 4200m
WorldSizeY: 1700m (4200 - 2500)
WaterLine: -2500m
WaterBottomLine: -2650m (profundidad 150m)
Aparente: 1700m de altura desde el agua
```

### Terreno Plano (Llanura)
```
min_elevation: 50m
max_elevation: 120m
WorldSizeY: 70m (120 - 50)
WaterLine: -50m
WaterBottomLine: -200m
Aparente: 70m de altura desde el agua
```

### Terreno Urbano (Costa)
```
min_elevation: 0m (nivel del mar)
max_elevation: 150m
WorldSizeY: 150m (150 - 0)
WaterLine: 0m (nivel del mar)
WaterBottomLine: -150m
Aparente: 150m de altura desde el agua
```

### Terreno Urbano Intermedio
```
min_elevation: 45m
max_elevation: 235m
WorldSizeY: 190m (235 - 45)
WaterLine: -45m
WaterBottomLine: -195m
Aparente: 190m de altura desde el agua
```

## ✅ Validación

Para verificar que las nuevas características funcionan correctamente:

1. Descargar un mapa urbano o montañoso
2. Exportar el terreno
3. Verificar en los archivos generados:
   - `.otc` debe tener un `WorldSizeY` realista (no siempre 300)
   - `.terrn2` debe tener un `WaterLine` que coincida con la topografía

## 🚀 Próximas Mejoras Posibles

- Detección automática de cuerpos de agua importantes para colocación realista
- Integración con datos de nivel del mar por ubicación geográfica
- Generación procedural de cascadas en terrenos escarpados
- Cálculo de pendientes realista para determinación de erosión visual

## 📝 Notas

- La precisión depende de los datos de elevación de OpenTopography
- Los cálculos asumen proyecciones en metros (UTM)
- Los márgenes de seguridad pueden ajustarse según necesidades artísticas

