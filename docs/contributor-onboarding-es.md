# Guía de onboarding para contribuidores (español)

Este documento propone el **camino mínimo** que debería seguir una persona nueva para entender el proyecto rápido y empezar a contribuir sin perderse.

## Orden de lectura recomendado

1. **README.md**
   - Qué hace el proyecto (objetivo y outputs).
   - Flujo de uso de punta a punta desde CLI.
   - Estructura de carpetas.

2. **CONTRIBUTING.md**
   - Convenciones de contribución, ramas, commits y estilo.
   - Criterios de calidad esperados para PRs.

3. **`src/main.py` (flujo principal)**
   - Punto de entrada de la aplicación.
   - Secuencia: descargar datos → procesar/exportar.
   - Estado de sesión (`MapData`) y menú interactivo.

4. **Documentación de exportadores (`docs/exporters-docs.md`)**
   - Explica el contrato de salida de archivos (`.terrn2`, `.otc`, `.tobj`).

5. **Referencia funcional (`docs/function-reference.md`)**
   - Resumen por módulo de funciones y clases clave.
   - Qué entra/sale de cada parte del pipeline.

---

## Artículos fundamentales que debería tener la documentación

Si quieres que la documentación sirva para contributors nuevos, estos son los artículos más importantes.

### 1) Arquitectura y pipeline general
**Objetivo:** explicar cómo viajan los datos desde OSM hasta archivos de terreno para RoR.

Debe responder:
- ¿Qué módulos participan y en qué orden?
- ¿Qué estructuras se comparten entre módulos?
- ¿Dónde se guarda estado temporal?

> Estado actual: parte de esta explicación ya está en `README.md`, pero conviene extraerla a un artículo dedicado de arquitectura.

### 2) Guía del flujo de ejecución (CLI)
**Objetivo:** describir exactamente qué hace cada opción del menú principal.

Debe responder:
- ¿Qué hace `dlcity()`?
- ¿Qué valida `download_menu()`?
- ¿Qué genera `export()` y en qué carpeta?
- ¿Qué variables de entorno afectan el resultado?

### 3) Referencia de módulos y funciones
**Objetivo:** mapa navegable de “qué hace cada función” para no tener que abrir todo el repo.

Debe incluir:
- `src/data/*`: descarga y parsing OSM.
- `src/processing/*`: altura, carreteras y exportadores.
- `src/utils/*`: BBox, geometría, logging, constantes.
- Firma resumida + propósito + side effects de cada función pública.

### 4) Formatos de salida (contratos)
**Objetivo:** documentar los formatos generados y su semántica para evitar regressions.

Debe cubrir:
- `.terrn2`: secciones y campos obligatorios.
- `.otc` global y paged: parámetros clave.
- `.tobj`: objetos y carreteras procedurales.
- Convenciones de nombres de archivos en `output/`.

### 5) Errores comunes y troubleshooting
**Objetivo:** ahorrar tiempo de debugging a quienes contribuyen por primera vez.

Debe cubrir:
- Fallos típicos de Overpass/OpenTopoData.
- CRS/bbox inválido.
- Datos incompletos (sin carreteras o sin elevación).
- Qué logs mirar y dónde.

### 6) Guía de pruebas y validación
**Objetivo:** definir cómo verificar cambios antes de abrir PR.

Debe incluir:
- Tests unitarios disponibles.
- Checks rápidos recomendados.
- Criterios de aceptación para cambios en exportadores.

---


## Documentación específica (dividida por tema)

- [Índice de documentación para contributors](contributors/README.md)
- [Configuración de clave API OpenTopography](contributors/opentopography-api-key.md)

---

## Recomendación práctica para empezar a contribuir

1. Corre el flujo completo con un bbox pequeño.
2. Abre los archivos resultantes en `output/` y valida que se generan todos.
3. Revisa `docs/function-reference.md` para ubicar qué módulo tocar según tu issue.
4. Haz cambios pequeños (un módulo por PR) y adjunta evidencia de salida.

---

## Alcance de `docs/function-reference.md`

La referencia funcional fue pensada como índice de navegación:
- **No** reemplaza docstrings detallados.
- **Sí** acelera el onboarding al mostrar dependencias y responsabilidades por módulo.

