# Etapa 1.4 — Auditoría de la infraestructura documental

## Registro y método

- **Fecha:** 2026-10-20
- **Alcance:** especificación aprobada y documentos de `docs/book/` disponibles en el árbol actual.
- **Método:** inspección estática, comprobación de presencia de archivos y estado Git, parseo JSON de `inventory/schema.json` y conteo de registros JSONL.
- **Aplicación y tests:** no ejecutados.
- **Decisión:** **REQUIERE CORRECCIONES**.

La especificación de referencia es `../codex_especificacion_infraestructura_documental.md`. El árbol estaba sucio; no atribuyo los cambios existentes.

## Criterios evaluados

| Criterio | Resultado | Evidencia |
|---|---|---|
| Artefactos de la estructura aprobada | **Aprobado** | Existen plan, workflow, informes, esquema, cuatro flujos JSONL, progreso, preguntas, capítulos, diagramas, revisiones y plantillas. Comparado con la lista de la especificación, sección 9. |
| No declarar inventario o libro completos | **Aprobado** | Los cuatro JSONL tienen 0 registros; `inventory/README.md` los identifica como no generados y `progress/coverage.md` deja análisis y capítulos en `not_started`. |
| Preservación de auditoría inicial | **Aprobado** | `audit_review.md` conserva la observación histórica de `osm2terrn/cache/` ausente y la diferencia temporal sin inventar causa. |
| Compatibilidad de instrucciones de asistentes | **Aprobado** | `assistant_workflow.md` asigna implementación a Copilot y revisión independiente a Codex, dueño por archivo y handoff. No hallé contradicciones con README o plantillas. Hay redundancia descriptiva, no conflicto. |
| Plan no presupone arquitectura | **Aprobado** | `book_plan.md` llama los temas candidatos, los declara no analizados exhaustivamente y permite modificarlos tras el inventario. |
| Archivos, módulos, funciones, métodos y clases | **Parcial** | `schema.json` incluye los tipos de símbolo y `owner_symbol_id`; falta separar estado de inventario, análisis y documentación (H1). |
| Herencia y composición | **Parcial** | `relations.kind` tiene `inherits` y `contains`, pero no distingue composición/agregación de contención léxica (H2). |
| Llamadas y dependencias | **Parcial** | Se admiten `calls` e `imports` entre símbolos, pero no hay destino tipado para dependencias externas ni alcance explícito del grafo externo (H2). |
| Ramificaciones y excepciones | **No aprobado** | No existen relaciones/records para condiciones de rama, excepciones lanzadas o manejadas. La plantilla solo permite narrarlas como prosa (H2). |
| Tests | **Parcial** | `references_test` expresa asociación y se aclara que no implica test pasado. No hay registro estructurado de test ejecutado y resultado (H3). |
| Evidencias e incertidumbre | **Parcial** | Todos los records contemplan `evidence`, `uncertainties` y `limitations`; el tipo `runtime_observation` no captura estructuradamente comando, entorno y resultado (H3). |
| Estados independientes de inventario, análisis y documentación | **No aprobado** | `analysis_status` mezcla `inventory_generated`, `reviewed` y `runtime_verified`; `docs_cross_reference.status` indica validez de ruta, no estado editorial. El capítulo tiene un estado textual único (H1). |
| Desconocido/no verificable | **Parcial** | Existen estados `unresolved`/`unverifiable`, pero una referencia sin destino conocido no puede representarse sin ruta: `target_path` es requerido (H4). |
| Trazabilidad capítulo–código | **Parcial** | `templates/chapter.md` pide clasificación y ruta/símbolo; no asigna ID a cada afirmación ni la enlaza a evidencia estructurada o revisión específica (H3). |
| Criterios de aceptación observables | **Parcial** | El esquema parsea como JSON y los JSONL están vacíos. No se validó con motor JSON Schema ni se probaron casos positivos/negativos, unicidad, foreign keys, rangos de línea o determinismo. La propia documentación dice que no hay validador. |

## Comprobaciones realizadas

- `Get-ChildItem docs/book -Recurse -File`: artefactos listados en la especificación presentes.
- `git status --short`: checkout sucio, con modificaciones preexistentes y `docs/book/` sin seguimiento; no se atribuye autoría.
- `Get-Content -Raw docs/book/inventory/schema.json | ConvertFrom-Json`: **parseo JSON correcto**; esto no demuestra conformidad JSON Schema 2020-12.
- Conteo de no-vacías: `files.jsonl`, `symbols.jsonl`, `relations.jsonl` y `docs_cross_reference.jsonl` tienen **0** registros cada uno.
- No se ejecutaron aplicación, extractor, validador, pruebas ni generación de inventarios.

## Problemas por gravedad y corrección mínima

### H1 — Alta: estados de trabajo mezclados

**Archivos:** `inventory/schema.json` (`analysisStatus` y usos); `inventory/README.md` (“Format”); `progress/coverage.md`; `templates/chapter.md`.

Un solo `analysis_status` intenta representar generación de inventario, revisión y verificación de ejecución. El estado de `docs_cross_reference` mide resolución de referencia, no avance de documentación. No se puede registrar por separado una función inventariada, aún sin analizar, y un capítulo redactado o pendiente de revisión.

**Corrección mínima:** separar campos/enums `inventory_status`, `analysis_status` y `documentation_status`; definirlos en schema, README, cobertura y plantilla. Mantener la verificación de ejecución como eje separado si se necesita.

### H2 — Alta: faltan flujo de control y relaciones de composición

**Archivo:** `inventory/schema.json`, `$defs.relationRecord.kind`.

El enum no representa condiciones/ramas, excepciones lanzadas o capturadas, ni composición/agregación. Tampoco permite modelar de forma tipada dependencias externas en el grafo.

**Corrección mínima:** añadir records de flujo de control o relaciones con campos para condición, ubicación, tipo de excepción y manejador; separar `composes`/`aggregates` de `contains`. Decidir explícitamente si dependencias externas entran al grafo con nodos tipados o quedan en inventario aparte. Etiquetar todas las aristas estáticas como no-runtime.

### H3 — Media: evidencia runtime y trazabilidad por afirmación incompletas

**Archivos:** `inventory/schema.json` (`evidence`); `templates/chapter.md`; `templates/review.md`; `templates/handoff.md`.

Una evidencia `runtime_observation` solo requiere ruta, tipo y descripción; no registra comando, entorno, resultado ni test ejecutado. Las afirmaciones de capítulos no tienen ID estable que pueda enlazarse a uno o varios registros de evidencia.

**Corrección mínima:** añadir ID de afirmación y referencias a IDs de evidencia; estructurar observaciones con comando, entorno, resultado, fecha/revisión y, para tests, test ID y resultado. Mantener las líneas como localizadores secundarios.

### H4 — Media: referencias con destino desconocido no representables

**Archivo:** `inventory/schema.json`, `$defs.documentationReferenceRecord`.

`target_path` es obligatorio incluso con estado `missing` o `unverifiable`; un destino realmente desconocido no puede expresarse sin inventar una ruta.

**Corrección mínima:** hacer `target_path` nullable para estados sin destino, o guardar `target_text` separado del destino resuelto y condicionar en schema cuándo este último es obligatorio.

### H5 — Media: la aceptación no puede reproducirse aún

**Archivos:** `inventory/README.md`, “Generation requirements”; `README.md`, “Inventory and regeneration”; `progress/coverage.md`, “Book infrastructure”.

El progreso admite que falta validación agregada. No hay validador que compruebe esquema, IDs únicos, referencias cruzadas, líneas o determinismo. El parseo JSON efectuado no cubre esos criterios.

**Corrección mínima:** agregar un validador pequeño o instrucciones reproducibles con herramienta disponible para validar contrato y relaciones, junto con registros de ejemplo válidos e inválidos. No hace falta generar todavía el inventario completo.

## Aspectos que deben conservarse

- Los JSONL vacíos están declarados explícitamente como no generados, no como ausencia de código.
- La auditoría histórica se preserva; la revisión no inventa ejecución ni causa para cambios temporales.
- Plan y diagramas distinguen temas candidatos, relaciones estáticas e interacción observada.
- Las plantillas documentan comandos no ejecutados y limitaciones; se prohíbe inferir resultados de tests.

## Decisión final

**REQUIERE CORRECCIONES.** La infraestructura evita afirmar que el programa ya fue analizado, pero sus contratos no representan todo el flujo de control requerido, mezclan estados independientes y no ofrecen trazabilidad estructurada por afirmación.

Orden recomendado: **H1**, **H2**, **H3**, **H4**, **H5**. Tras corregirlos, actualizar `progress/coverage.md`, validar el schema con casos positivos/negativos y solicitar nueva revisión independiente. La aprobación no requiere inventario completo ni capítulos terminados.

## Seguimiento fechado — 2026-10-20

Este seguimiento conserva el veredicto histórico anterior y registra cambios
posteriores:

- **H5 — Resuelto para los streams JSONL:** el esquema v2 cubre los siete
  streams y el validador aplica los contratos de sidecars además de los
  registros principales. `tests/test_inventory_tool.py` añade regresiones y
  la generación/validación volvió a ejecutarse. Esto no resuelve por sí solo
  la validación general de JSON Schema fuera del subconjunto documentado.
- **H1–H4 — Aún abiertos:** los estados independientes, el modelado de flujo
  de control/composición, la evidencia enlazable por afirmación y las
  referencias sin destino conocido siguen pendientes para una futura
  actualización acotada del contrato documental.

La revisión actualizada del generador y sus métricas está en
`inventory-generator-audit.md`.

## Seguimiento fechado — 2026-10-20 — Contrato v3

Este seguimiento no altera el dictamen histórico **REQUIERE CORRECCIONES** ni
declara aprobación independiente. La implementación actual incorpora contratos
y pruebas para los hallazgos:

- **H1 — Resuelto en contrato/generador:** todos los records tienen estados
  independientes de inventario, análisis, documentación y ejecución. El
  generador emite `inventoried`/`excluded`, `static_analyzed`,
  `not_documented`, `not_verified`; nunca emite `human_reviewed`, `approved`,
  `passed` ni `failed` por inferencia. Enumeraciones y validación están en
  `inventory/schema.json` y `inventory/inventory_tool.py`.
- **H2 — Resuelto como capacidad de contrato; extracción parcial pendiente:**
  se separa `contains` de `composes`/`aggregates`; las relaciones contemplan
  ramas, excepciones y referencias a dependencias; `control_flow.jsonl` puede
  registrar ocurrencias estáticas con ubicación y campos obligatorios. Las
  dependencias mantienen IDs de los módulos internos importadores. El
  generador deja `control_flow.jsonl` vacío; no construye CFG, no determina
  alcanzabilidad ni registra resultados de ejecución. La relación de
  composición/agregación requiere revisión semántica y no se infiere del AST
  actual.
- **H3 — Resuelto en contrato y plantillas:** cada afirmación usa `claim_id`
  y `evidence_ids`; la evidencia tiene `evidence_id`, tipo, ruta y descripción.
  Evidencia de test/ejecución requiere comando, entorno, resultado, revisión y
  fecha, más test ID cuando corresponda. Las plantillas de capítulo, revisión
  y handoff exigen esos enlaces. `claims.jsonl` sigue vacío y no se afirma que
  haya capítulos documentados.
- **H4 — Resuelto en contrato/validador:** las referencias distinguen
  `resolved`, `expected_missing`, `unknown` y `unverifiable`. Solo `resolved`
  requiere `target_path`; los otros estados retienen `original_reference` sin
  inventar una ruta.
- **H5 — Se mantiene resuelto para los streams JSONL** según el seguimiento
  anterior; el validador ahora incluye también streams de control y claims.

Comprobaciones ejecutables y resultados de este seguimiento se registran en
`inventory-generator-audit.md` bajo el seguimiento v3 y en
`progress/inventory_report.md`. La decisión final sobre cierre independiente
de H1-H4 queda pendiente de una revisión separada. No se ejecutó la aplicación.

## Seguimiento fechado — 2026-10-20 — Revisión independiente del contrato v3

La revisión independiente está en `contract-v3-independent-review.md` y
concluye **REQUIERE CORRECCIONES**. Este seguimiento actualiza el estado
operativo sin borrar las evaluaciones históricas previas:

- **H1 — Reabierto/parcial:** los cuatro campos y enums existen, pero se
  aceptan estados contradictorios (`inventory_status=excluded` con
  `inventory_disposition=included`) y afirmaciones `blocked`,
  `human_reviewed` o `approved` sin motivo/revisión registrada.
- **H2 — Parcial:** las clases de relación existen. Falta comprobar que una
  relación `runtime_observed` tenga evidencia de ejecución y que los
  localizadores de `control_flow.jsonl` sean válidos. No se genera un CFG ni
  se verifica ejecución.
- **H3 — Parcial:** las referencias de claim a evidencia inexistente y los
  IDs duplicados se detectan, pero los estados de revisión/aprobación no están
  vinculados a una revisión comprobable; tampoco se impide usar evidencia
  estática para una relación runtime.
- **H4 — Parcial:** los cuatro estados y la omisión de `target_path` para
  destinos no resueltos funcionan. Un `target_path` excluido todavía puede
  aceptarse como `resolved`.
- **H5 — Aprobado para validación estructural actual:** los nueve streams,
  esquemas implementados, integridad cruzada, determinismo y vigencia pasan.
  Este resultado no cubre las invariantes semánticas anteriores.

Por los hallazgos V3-01 a V3-04, no se recomienda comenzar la reconstrucción
del flujo de ejecución hasta corregirlos y repetir la revisión.

## Seguimiento de corrección — 2026-10-20

Se implementaron correcciones para V3-01 a V3-04 en el esquema/validador y
tests. El informe histórico `contract-v3-independent-review.md` conserva su
veredicto y contiene los detalles de los casos de regresión y validación. La
suite específica pasó 18 tests; los nueve streams se regeneraron y la
validación de esquema, integridad cruzada, determinismo y actualidad pasó.
H5 permanece aprobado para las comprobaciones implementadas.

Estado operativo: H1 y H4 tienen las invariantes documentadas y probadas;
H2 tiene relaciones y localizadores estructuralmente verificables, pero no
hay flujo de control extraído ni ejecución observada; H3 tiene el contrato de
evidencia y claims, pero `claims.jsonl` sigue vacío. Por tanto, no se declara
completa la extracción, la revisión semántica ni la cobertura del libro. Se
recomienda una nueva revisión independiente de las correcciones antes de
iniciar la reconstrucción del flujo de ejecución.

## Seguimiento de revisión independiente — 2026-10-20

La inspección de seguimiento está registrada en
`contract-v3-independent-review.md`. Su veredicto actual es
**REQUIERE CORRECCIONES**: las principales regresiones originales se bloquean,
pero probes adicionales aceptan motivos/revisiones y observaciones de runtime
con campos en blanco o fechas inválidas; también se acepta un localizador
`1-1` para un archivo vacío y un símbolo inexistente en una referencia
`unknown`. Se añaden N1-N4 para mantener estos casos visibles.

H5 pasa para los nueve streams presentes, IDs y determinismo comprobados; los
streams de referencias, flujo de control y claims están vacíos. H1-H4 no se
consideran cerrados. No iniciar la reconstrucción del flujo de ejecución hasta
corregir N1-N4 y completar otra revisión independiente.
