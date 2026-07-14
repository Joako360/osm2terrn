# Guía Rápida: Ajustes Realistas de Elevación y Agua

## 🎯 ¿Qué se cambió?

Los mapas generados ahora tienen:
- **Altura más realista**: El tamaño vertical del terreno (WorldSizeY) se calcula automáticamente basado en las diferencias de elevación real
- **Agua realista**: El nivel del agua (WaterLine) se coloca automáticamente al nivel apropiado según la topografía

## 🚀 Uso

**No requiere cambios en el flujo de trabajo normal:**

```
1. Ejecuta main.py
2. Descarga una ciudad
3. Exporta el terreno
↓
Los valores realistas se calculan automáticamente ✅
```

## 📊 Ejemplo de Salida

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

En el archivo `.terrn2` verás:
```
WaterLine = -45.50
WaterBottomLine = -195.50
```

## ⚙️ Configuración (Opcional)

Si quieres ajustar el comportamiento, edita osm2terrn/utils/constants.py:

```python
# Deshabilitar escalado realista (vuelve a valores por defecto)
ENABLE_REALISTIC_ELEVATION = False

# Deshabilitar cálculo automático de agua
ENABLE_REALISTIC_WATER = False

# Ajustar profundidad del agua (metros)
WATER_DEPTH_DEFAULT = 150.0

# Ajustar límites de altura
MIN_WORLD_SIZE_Y = 50.0
MAX_WORLD_SIZE_Y = 10000.0
```

## 📝 Detalles Técnicos

### Cálculo de WorldSizeY

El tamaño vertical del terreno es simplemente la diferencia entre elevación máxima y mínima:

```
WorldSizeY = max_elevation - min_elevation
Límites: 50m mín, 10km máx
```

**Ejemplo:** Terreno con elevación 45m-235m
```
WorldSizeY = 235 - 45 = 190m
```

### Cálculo de WaterLine

El nivel del agua se coloca al nivel negativo de la elevación mínima, haciendo que el nivel del mar (0) sea la referencia:

```
WaterLine = -min_elevation
WaterBottomLine = WaterLine - profundidad_agua (150m por defecto)
```

**Ejemplo:** Terreno con elevación 45m-235m
```
WaterLine = -45m
WaterBottomLine = -45 - 150 = -195m
Resultado: El terreno aparenta altura real 190m desde el agua (-45m a 145m)
```

## ✅ Validación

Verifica los valores generados en los archivos `.otc` y `.terrn2`:

**En `.otc`:**
```
WorldSizeY=190   ← Diferencia real: max - min
```

**En `.terrn2`:**
```
WaterLine = -45.50        ← Negativo de la elevación mínima
WaterBottomLine = -195.50 ← WaterLine - profundidad (150m)
```

**Verificación de realismo:**
- WorldSizeY debe ser exactamente (max_elevation - min_elevation)
- WaterLine debe ser -min_elevation
- El terreno debe aparecer desde WaterLine hasta WaterLine + WorldSizeY

## 🎨 Resultados Esperados

| Terreno | Rango Elev. | WorldSizeY | WaterLine | Aparente |
|---------|-------------|-----------|-----------|----------|
| Montaña | 2500-4200m | 1700m | -2500m | 1700m desde agua |
| Llanura | 50-120m | 70m | -50m | 70m desde agua |
| Costa | 0-150m | 150m | 0m | 150m desde agua |
| Urbano | 45-235m | 190m | -45m | 190m desde agua |

## 💡 Tips

1. **Para terrenos muy planos**: Se usa el mínimo (50m) para evitar problemas de renderizado
2. **Para terrenos muy altos**: Se limita a 10km para evitar problemas de memoria
3. **Ajusta manualmente** si quieres un efecto artístico diferente (edita `.terrn2` y `.otc`)

## 📚 Más Información

Ver [elevation_realism_improvements-es.md](./elevation-realism/elevation_realism_improvements-es.md) para detalles técnicos completos.
