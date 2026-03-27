# GuÃ­a de onboarding para contribuidores (espaÃ±ol)

Este documento propone el **camino mÃ­nimo** que deberÃ­a seguir una persona nueva para entender el proyecto rÃ¡pido y empezar a contribuir sin perderse.

## Orden de lectura recomendado

1. **README.md**
   - QuÃ© hace el proyecto (objetivo y outputs).
   - Flujo de uso de punta a punta desde CLI.
   - Estructura de carpetas.

2. **CONTRIBUTING.md**
   - Convenciones de contribuciÃ³n, ramas, commits y estilo.
   - Criterios de calidad esperados para PRs.

3. **`src/main.py` (flujo principal)**
   - Punto de entrada de la aplicaciÃ³n.
   - Secuencia: descargar datos â†’ procesar/exportar.
   - Estado de sesiÃ³n (`MapData`) y menÃº interactivo.

4. **DocumentaciÃ³n de exportadores (`.docs/exporters-docs.md`)**
   - Explica el contrato de salida de archivos (`.terrn2`, `.otc`, `.tobj`).

5. **Referencia funcional (`.docs/function-reference.md`)**
   - Resumen por mÃ³dulo de funciones y clases clave.
   - QuÃ© entra/sale de cada parte del pipeline.

---

## ArtÃ­culos fundamentales que deberÃ­a tener la documentaciÃ³n

Si quieres que la documentaciÃ³n sirva para contributors nuevos, estos son los artÃ­culos mÃ¡s importantes.

### 1) Arquitectura y pipeline general
**Objetivo:** explicar cÃ³mo viajan los datos desde OSM hasta archivos de terreno para RoR.

Debe responder:
- Â¿QuÃ© mÃ³dulos participan y en quÃ© orden?
- Â¿QuÃ© estructuras se comparten entre mÃ³dulos?
- Â¿DÃ³nde se guarda estado temporal?

> Estado actual: parte de esta explicaciÃ³n ya estÃ¡ en `README.md`, pero conviene extraerla a un artÃ­culo dedicado de arquitectura.

### 2) GuÃ­a del flujo de ejecuciÃ³n (CLI)
**Objetivo:** describir exactamente quÃ© hace cada opciÃ³n del menÃº principal.

Debe responder:
- Â¿QuÃ© hace `dlcity()`?
- Â¿QuÃ© valida `download_menu()`?
- Â¿QuÃ© genera `export()` y en quÃ© carpeta?
- Â¿QuÃ© variables de entorno afectan el resultado?

### 3) Referencia de mÃ³dulos y funciones
**Objetivo:** mapa navegable de â€œquÃ© hace cada funciÃ³nâ€ para no tener que abrir todo el repo.

Debe incluir:
- `src/data/*`: descarga y parsing OSM.
- `src/processing/*`: altura, carreteras y exportadores.
- `src/utils/*`: BBox, geometrÃ­a, logging, constantes.
- Firma resumida + propÃ³sito + side effects de cada funciÃ³n pÃºblica.

### 4) Formatos de salida (contratos)
**Objetivo:** documentar los formatos generados y su semÃ¡ntica para evitar regressions.

Debe cubrir:
- `.terrn2`: secciones y campos obligatorios.
- `.otc` global y paged: parÃ¡metros clave.
- `.tobj`: objetos y carreteras procedurales.
- Convenciones de nombres de archivos en `output/`.

### 5) Errores comunes y troubleshooting
**Objetivo:** ahorrar tiempo de debugging a quienes contribuyen por primera vez.

Debe cubrir:
- Fallos tÃ­picos de Overpass/OpenTopoData.
- CRS/bbox invÃ¡lido.
- Datos incompletos (sin carreteras o sin elevaciÃ³n).
- QuÃ© logs mirar y dÃ³nde.

### 6) GuÃ­a de pruebas y validaciÃ³n
**Objetivo:** definir cÃ³mo verificar cambios antes de abrir PR.

Debe incluir:
- Tests unitarios disponibles.
- Checks rÃ¡pidos recomendados.
- Criterios de aceptaciÃ³n para cambios en exportadores.

---


## DocumentaciÃ³n especÃ­fica (dividida por tema)

- [Ãndice de documentaciÃ³n para contributors](README.md)
- [ConfiguraciÃ³n de clave API OpenTopography](opentopography-api/opentopography-api-key-es.md)
- [Ãndice de documentaciÃ³n de exporters](exporters/README.md)

---

## RecomendaciÃ³n prÃ¡ctica para empezar a contribuir

1. Corre el flujo completo con un bbox pequeÃ±o.
2. Abre los archivos resultantes en `output/` y valida que se generan todos.
3. Revisa `.docs/function-reference.md` para ubicar quÃ© mÃ³dulo tocar segÃºn tu issue.
4. Haz cambios pequeÃ±os (un mÃ³dulo por PR) y adjunta evidencia de salida.

---

## Alcance de `.docs/function-reference.md`

La referencia funcional fue pensada como Ã­ndice de navegaciÃ³n:
- **No** reemplaza docstrings detallados.
- **SÃ­** acelera el onboarding al mostrar dependencias y responsabilidades por mÃ³dulo.



