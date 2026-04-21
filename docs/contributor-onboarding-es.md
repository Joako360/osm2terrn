# Guá de onboarding para contribuidores (español)

Este documento propone el **camino mí­nimo** que deberá seguir una persona nueva para entender el proyecto rápido y empezar a contribuir sin perderse.

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
   - Secuencia: descargar datos â†’ procesar/exportar.
   - Estado de sesión (`MapData`) y menú interactivo.

4. **Documentación de exportadores (`.docs/exporters-docs.md`)**
   - Explica el contrato de salida de archivos (`.terrn2`, `.otc`, `.tobj`).

5. **Referencia funcional (`.docs/function-reference.md`)**
   - Resumen por módulo de funciones y clases clave.
   - Qué entra/sale de cada parte del pipeline.

---

## Artí­culos fundamentales que deberá tener la documentación

Si quieres que la documentación sirva para contributors nuevos, estos son los artí­culos más importantes.

### 1) Arquitectura y pipeline general
**Objetivo:** explicar cómo viajan los datos desde OSM hasta archivos de terreno para RoR.

Debe responder:
- Â¿Qué módulos participan y en qué orden?
- Â¿Qué estructuras se comparten entre módulos?
- Â¿Dónde se guarda estado temporal?

> Estado actual: parte de esta explicación ya está en `README.md`, pero conviene extraerla a un artí­culo dedicado de arquitectura.

### 2) Guá del flujo de ejecución (CLI)
**Objetivo:** describir exactamente qué hace cada opción del menú principal.

Debe responder:
- Â¿Qué hace `dlcity()`?
- Â¿Qué valida `download_menu()`?
- Â¿Qué genera `export()` y en qué carpeta?
- Â¿Qué variables de entorno afectan el resultado?

### 3) Referencia de módulos y funciones
**Objetivo:** mapa navegable de â€œqué hace cada funciónâ€ para no tener que abrir todo el repo.

Debe incluir:
- `src/data/*`: descarga y parsing OSM.
- `src/processing/*`: altura, carreteras y exportadores.
- `src/utils/*`: BBox, geometrá, logging, constantes.
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
- Fallos tí­picos de Overpass/OpenTopoData.
- CRS/bbox inválido.
- Datos incompletos (sin carreteras o sin elevación).
- Qué logs mirar y dónde.

### 6) Guá de pruebas y validación
**Objetivo:** definir cómo verificar cambios antes de abrir PR.

Debe incluir:
- Tests unitarios disponibles.
- Checks rápidos recomendados.
- Criterios de aceptación para cambios en exportadores.

---


## Documentación especí­fica (dividida por tema)

- [índice de documentación para contributors](README.md)
- [Configuración de clave API OpenTopography](opentopography-api/opentopography-api-key-es.md)
- [índice de documentación de exporters](exporters/README.md)

---

## Recomendación práctica para empezar a contribuir

1. Corre el flujo completo con un bbox pequeño.
2. Abre los archivos resultantes en `output/` y valida que se generan todos.
3. Revisa `.docs/function-reference.md` para ubicar qué módulo tocar según tu issue.
4. Haz cambios pequeños (un módulo por PR) y adjunta evidencia de salida.

---

## Alcance de `.docs/function-reference.md`

La referencia funcional fue pensada como í­ndice de navegación:
- **No** reemplaza docstrings detallados.
- **Sí­** acelera el onboarding al mostrar dependencias y responsabilidades por módulo.



