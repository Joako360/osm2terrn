# Revisión independiente del contrato documental v3

**Fecha:** 2026-10-20  
**Veredicto:** **REQUIERE CORRECCIONES**  
**Alcance:** esquema v3, generador/validador, nueve streams JSONL, informes, instrucciones, plantillas y pruebas de `docs/book/`. No se modificó el contrato durante la revisión.

## Método y estado del árbol

Se inspeccionó `git status --short`, el diff rastreado y los archivos reales de `docs/book/`. La infraestructura documental y `tests/test_inventory_tool.py` aparecen sin seguimiento en el checkout; por ello el diff de Git no expande esos archivos y se revisaron directamente. Había cambios preexistentes en módulos de la aplicación, tests y otros documentos. No se les atribuye autoría; esta revisión no modificó la aplicación ni esos cambios.

El inventario actual contiene nueve JSONL: `files`, `symbols`, `relations`, `docs_cross_reference`, `control_flow`, `claims`, `unresolved`, `entry_points` y `external_dependencies`. Los streams de referencias, flujo y afirmaciones están vacíos; las demás cifras describen solo el árbol y análisis estático actuales.

## Hallazgos

### V3-01 — Alta: los estados permiten declaraciones contradictorias o sin respaldo

**Evidencia:** `inventory/schema.json:213-337` define `inventory_status` y `inventory_disposition`, pero no exige que sean coherentes. Los enums de `analysisStatus` (`:42-49`) y `documentationStatus` (`:1055-1062`) aceptan `blocked`, `human_reviewed` y `approved` sin motivo, revisor, fecha o ID de revisión. `inventory_tool.py:1532-1537` solo exige evidencia para los estados de ejecución `passed`/`failed`.

**Reproducción:** el validador aceptó un `fileRecord` con `inventory_status=excluded` e `inventory_disposition=included`; también aceptó `analysis_status=blocked`, `analysis_status=human_reviewed` y `documentation_status=approved` sin evidencia adicional. La prueba directa llamó `schema_errors(record, {"$ref":"#/$defs/fileRecord"}, schema)` y obtuvo lista vacía.

**Impacto:** el sistema permite presentar como bloqueado, revisado o aprobado un elemento sin registrar por qué o quién lo decidió. Esto debilita H1 y contradice las transiciones y significados documentados en `inventory/README.md:43-60`.

**Corrección mínima:** agregar condiciones de coherencia entre los dos estados de inventario; requerir motivo para `blocked`/`excluded`; registrar revisor, fecha e ID de revisión para `human_reviewed` y `approved`, y validar esas referencias. Mantener estados independientes, pero exigir evidencia para transiciones que expresan una decisión humana.

### V3-02 — Alta: una relación puede declararse observada en ejecución con evidencia estática

**Evidencia:** `inventory/schema.json:503-510` permite `resolution=runtime_observed`. `inventory_tool.py:1438-1445` verifica endpoints e ID de relación; `:1532-1537` comprueba evidencia solo cuando `execution_status` es `passed` o `failed`, y no vincula `resolution=runtime_observed` con evidencia `runtime_observation`.

**Reproducción:** se presentó una relación `calls` con `resolution=runtime_observed`, `execution_status=not_verified` y evidencia de tipo `source`, sin comando ni observación de ejecución. `global_checks(...)` devolvió `[]`.

**Impacto:** se puede confundir una arista estática con una interacción observada, pese a la regla central del contrato y el workflow.

**Corrección mínima:** exigir para toda relación `runtime_observed` al menos una evidencia `runtime_observation` con los campos estructurados obligatorios; validar la coherencia de su resultado con el estado de ejecución. Añadir un caso negativo a las pruebas.

### V3-03 — Media: los localizadores de flujo de control no se validan contra el archivo

**Evidencia:** `controlFlowRecord` requiere `start_line` y `end_line` (`schema.json:1139-1219`). La comprobación agregada de flujo en `inventory_tool.py:1524-1531` verifica símbolo, ruta y handler, pero no el rango, el orden ni el fin de archivo. La comprobación de rango de líneas de evidencia (`:1489-1503`) no incluye los localizadores propios del registro.

**Reproducción:** con un archivo de dos líneas, se validó un registro `conditional_branch` de líneas 50–60 y fuente perteneciente a ese mismo archivo. `global_checks(..., line_count=lambda _: 2)` devolvió `[]`.

**Impacto:** un registro puede parecer una observación localizada en código cuando su ubicación no existe.

**Corrección mínima:** validar `start_line <= end_line` y que ambos extremos no superen el número de líneas del archivo. Agregar pruebas para los dos casos.

### V3-04 — Media: una referencia “resuelta” puede apuntar a una ruta excluida

**Evidencia:** `inventory_tool.py:1510-1519` comprueba que `target_path` pertenezca al conjunto de rutas inventariadas, pero no comprueba que el record de destino esté incluido ni que exista como archivo utilizable.

**Reproducción:** se agregó al conjunto de prueba un `fileRecord` excluido (`inventory_disposition=excluded`) y una referencia con `status=resolved` a esa ruta. `global_checks(...)` devolvió `[]`.

**Impacto:** el contrato puede afirmar que encontró el destino aunque el generador lo haya excluido y no lo haya inspeccionado.

**Corrección mínima:** para `resolved`, requerir destino incluido y existente (o definir explícitamente qué clases de destino excluido pueden considerarse resueltas y cómo se evidencia).

## Comprobaciones aprobadas

| Comprobación | Resultado |
|---|---|
| Enums de los cuatro ejes: valores permitidos y valor desconocido | Pass; los cuatro enums aceptan valores definidos y rechazan `bogus` |
| Referencias `resolved`, `expected_missing`, `unknown`, `unverifiable` | Pass para el contrato normal; falla el caso de destino excluido señalado en V3-04 |
| IDs duplicados de records de claims | Pass; `global_checks` detecta duplicación de `claim_id` |
| Evidencias enlazadas inexistentes y IDs de evidencia conflictivos | Pass; se rechazan ambos casos |
| Evidencia test/runtime sin campos requeridos | Pass; `runtime_observation` incompleta y `test_execution` sin `test_id` se rechazan |
| Relaciones `contains`, `composes`, `aggregates`, `branches_to`, `raises`, `handles` | Pass como variantes representables; el modelo no prueba que composición/agregación sean semánticamente ciertas |
| Generación/validación H5 de los nueve JSONL | Pass: todos presentes, records válidos, referencias cruzadas consistentes, regeneración determinista y artefactos no obsoletos |
| Suite del generador | Pass: 13 tests `unittest` |

La existencia de las variantes de relación es capacidad de contrato. La composición/agregación exige una interpretación revisada; una presencia sintáctica no basta. El AST puede localizar branches y handlers, pero no establece alcanzabilidad ni ejecución. `control_flow.jsonl` y `claims.jsonl` siguen vacíos, por lo que no hay cobertura de contenido que aprobar.

## Comandos ejecutados

Desde la raíz del repositorio, con el Python 3.12.14 incluido en este entorno:

```powershell
python docs/book/inventory/inventory_tool.py validate --write-report
python -m unittest discover -s tests -p test_inventory_tool.py -v
```

Ambos comandos terminaron con código 0. El generador informó PASS para nueve JSONL, esquemas, referencias, determinismo y actualidad de los archivos. Las 13 pruebas terminaron en `OK`. Además, se ejecutaron probes Python in-memory contra `schema_errors` y `global_checks`; V3-01 a V3-04 son los casos que esos probes aceptaron incorrectamente. No se ejecutaron tests de la aplicación, servicios geográficos ni generación de terreno.

Después de agregar este informe se regeneraron y validaron los artefactos:
321 archivos, 776 símbolos, 1.897 relaciones, 1.601 registros sin resolver,
41 puntos de entrada y 62 dependencias. Los streams de etapa posterior siguen
vacíos. La validación final volvió a pasar y los artefactos no están obsoletos.

## Limitaciones y recomendación

El validador implementa un subconjunto propio de JSON Schema y esta revisión no corrió un validador externo del draft 2020-12. Los contratos de claims y flujo están listos para uso futuro, pero sus streams vacíos no prueban trazabilidad aplicada ni análisis de flujo del programa. No se declara cobertura total ni ejecución verificada.

**Recomendación:** corregir V3-01 a V3-04 y añadir los casos de regresión correspondientes antes de iniciar la reconstrucción del flujo de ejecución. H5 funciona en la validación estructural actual, pero no cubre estos defectos semánticos del contrato.

## Seguimiento de corrección — 2026-10-20

El veredicto histórico de esta revisión permanece **REQUIERE CORRECCIONES**. Se corrigieron los cuatro defectos reportados y se añadieron pruebas de regresión; esto es seguimiento de implementación, no una aprobación independiente.

| Hallazgo | Estado de corrección | Cambio y comprobación |
|---|---|---|
| V3-01 | Corregido | `global_checks` ahora exige coherencia entre disposición y estado de inventario; `blocked` requiere incertidumbre o limitación y los estados de revisión/aprobación requieren evidencia `review` estructurada con resultado `passed`. Las nuevas pruebas rechazan los estados sin soporte y aceptan aprobación con evidencia válida. |
| V3-02 | Corregido | Una relación `runtime_observed` requiere en la misma relación `execution_status=passed` y evidencia `runtime_observation` con resultado `passed`; evidencia `source` es rechazada. El test incluye ambas ramas. |
| V3-03 | Corregido | Se validan rangos de flujo, orden, límites del archivo, endpoints de evidencia y disponibilidad del archivo para los localizadores. Se probaron rangos válidos e inválidos, LF/CRLF, archivo sin salto final y archivo vacío (una línea lógica vacía). |
| V3-04 | Corregido | `resolved` requiere destino incluido y disponible en disco. `unknown`, `unverifiable` y `expected_missing` siguen aceptándose sin ruta objetivo. |

**Comprobaciones posteriores:** `python -m unittest discover -s tests -p test_inventory_tool.py -v` terminó con 18 tests `OK`; `py_compile` de generador y tests pasó. `generate` y `validate --write-report` regeneraron y validaron los nueve streams; el validador pasó esquemas, integridad cruzada, archivos incluidos, dos generaciones deterministas, actualidad de artefactos y pruebas negativas. Métricas de esta regeneración: 321 archivos, 782 símbolos, 1.909 relaciones, 1.699 elementos no resueltos, 41 puntos de entrada y 62 dependencias. Los streams de referencias, flujo de control y afirmaciones siguen vacíos.

La validación de disponibilidad de rutas usa el lector configurado por el validador; los tests unitarios de estados/rangos inyectan resultados controlados. No se ejecutó la aplicación ni se generaron terrenos o datos geográficos. Las pruebas no demuestran validez semántica de futuras decisiones de revisión, composición, ramas o excepciones. Se recomienda repetir una revisión independiente del diff y de estas reglas antes de reconstruir el flujo de ejecución.

## Seguimiento de revisión independiente — 2026-10-20

**Veredicto actual: REQUIERE CORRECCIONES.** Este seguimiento es una nueva inspección independiente; no altera el dictamen original ni el seguimiento de implementación anterior. Se inspeccionaron los archivos reales, el estado de Git, los nueve streams, las pruebas y los documentos de contrato/progreso. No se modificaron código, esquema, pruebas ni artefactos generados durante esta revisión.

### Resultado por hallazgo

| Hallazgo | Resultado actual | Evidencia independiente |
|---|---|---|
| V3-01 | **Parcial; requiere corrección adicional** | Las contradicciones de `inventory_status`/`inventory_disposition` y la ausencia total de motivo/revisión ahora se rechazan. Sin embargo, `uncertainties=[" "]` permite `analysis_status=blocked`; una evidencia `review` con `reviewer=" "`, `review_id=" "` y `observed_at="yesterday"` permite `documentation_status=approved`. En ambos probes `global_checks` y el esquema devolvieron `[]`. Los campos son no vacíos por longitud, pero no contienen motivo ni metadatos utilizables. |
| V3-02 | **Parcial; requiere corrección adicional** | Evidencia solamente `source` se rechaza y evidencia de runtime completa, con resultado aprobado, se acepta. Pero una relación `runtime_observed` con `command=" "`, `environment=" "`, `description=" "`, `repository_revision="x"` y `observed_at="yesterday"` pasó esquema y `global_checks` sin errores. El requisito actual valida presencia/tipo, pero no que la evidencia sea una observación revisable. |
| V3-03 | **Parcial; defecto reproducible** | Rangos fuera del archivo y rutas inexistentes se rechazan; LF, CRLF y archivos con o sin salto final de dos líneas dan rango válido `1-2`. En un archivo físicamente vacío, `_line_count_bytes(b"")` da 1 y un `control_flow` en `1-1` pasa `global_checks`. No existe línea de código que pueda respaldar ese localizador. Como caso adicional, bytes con terminadores CR aislados (`b"one\\rtwo"`) se cuentan como una sola línea. |
| V3-04 | **Parcial; requiere corrección adicional** | Destinos `resolved` excluidos o ausentes se rechazan; destino incluido existente se acepta; `unknown`, `unverifiable` y `expected_missing` se aceptan sin `target_path`. Aun así, una referencia `unknown` puede incluir `target_symbol_id="py:does_not_exist.py::nope"`; el esquema lo permite y `global_checks` no comprueba el ID porque la validación del símbolo está dentro de la rama `resolved`. El registro queda en estado desconocido con un objetivo simbólico inexistente. |

### Reproducciones adicionales

**Anclas de implementación:** `schema.json:100-189` define campos de ejecución y revisión solo como strings con `minLength`; `inventory_tool.py:387` cuenta el archivo vacío como una línea; `inventory_tool.py:1525-1539` valida destinos de referencias solo dentro de `resolved`; `inventory_tool.py:1565-1581` aplica las reglas de estado y runtime por presencia/tipo. Las regresiones existentes están en `tests/test_inventory_tool.py:67-174`; en particular el test de líneas espera que vacío cuente como una línea, pero no crea un record de flujo sobre ese archivo.

Los siguientes probes se ejecutaron en memoria contra `schema_errors` y `global_checks` usando el fixture común de `tests/test_inventory_tool.py`; para rangos, se usó además un archivo temporal real leído por el helper de líneas:

```text
empty file: _line_count_bytes(b"") -> 1
flow range 1-1 against empty file -> []
missing flow source file -> control flow ... source path cannot be verified on disk
unknown xref with nonexistent target_symbol_id -> []
blocked record with uncertainties=[" "] -> []
approved record with whitespace review_id/reviewer and observed_at="yesterday" -> schema [] ; global []
runtime_observed with whitespace command/environment/description and observed_at="yesterday" -> schema [] ; global []
CR-only content b"one\\rtwo" -> line count 1
```

Los rangos LF/CRLF y sin salto final se aceptaron para un archivo existente de dos líneas. Las variantes fuera de límite y la ruta ausente produjeron errores. La referencia a destino incluido existente pasó; los tres estados no resueltos pasaron sin ruta, como se espera.

### Calidad de pruebas y estado de los streams

`python -m unittest discover -s tests -p test_inventory_tool.py -v`: **18 tests, OK**. `python docs/book/inventory/inventory_tool.py validate`: **PASS** en JSONL, schemas, integridad cruzada, existencia de incluidos, determinismo, actualidad de artefactos y negativos incorporados. Se verificaron además los IDs de cada stream: `files` 321, `symbols` 782, `relations` 1.909, `docs_cross_reference` 0, `control_flow` 0, `claims` 0, `unresolved` 1.699, `entry_points` 41, `external_dependencies` 62; no hubo errores JSONL ni IDs duplicados.

Los 18 tests cubren los cuatro repros originales en sus formas principales, pero no cubren el archivo vacío con un record de flujo, los textos compuestos solo por espacios, una fecha inválida, campos runtime presentes pero vacíos/inutilizables ni un `target_symbol_id` colgante en una referencia no resuelta. La validación de referencias/claims sobre esos streams vacíos es estructuralmente correcta pero vacua: no acredita contenido real ni aplicación de trazabilidad.

### Hallazgos nuevos y correcciones mínimas

- **N1 — Media, V3-01:** normalizar con `strip()` motivos, reviewer e IDs; validar el formato documentado de `observed_at`; definir un mínimo verificable para `review_id` y aclarar qué artefacto de revisión respalda el estado. La validación no puede autenticar por sí sola una identidad humana, por lo que el workflow debe exigir referencia a un registro revisable.
- **N2 — Alta, V3-02:** rechazar valores vacíos/blancos y fechas no válidas en la evidencia de ejecución. Definir cómo `evidence.path` identifica el registro de salida o reporte verificable de la ejecución. La mera presencia de strings no prueba que el comando se haya ejecutado; esta limitación debe permanecer explícita aunque se refuerce el contrato.
- **N3 — Media, V3-03:** tratar un archivo vacío como cero líneas direccionables para evidencia/flujo, aunque se conserve una ubicación sintética del símbolo módulo si el inventario la necesita. Contar CR aislado como terminador o documentar formalmente que no está admitido.
- **N4 — Media, V3-04:** prohibir `target_symbol_id` en estados que no representan una resolución, o validar que el ID exista y que el estado permita esa asociación. Agregar prueba para ID inexistente en `unknown`/`unverifiable`.

### H1–H5, límites y recomendación

- **H1:** contrato mejorado, pero validación de motivo/revisión aún insuficiente (N1); no aprobado.
- **H2:** relaciones y campos de flujo existen; el stream de flujo está vacío. La validación runtime es estructural y vulnerable a campos ficticios (N2). No hay CFG, alcanzabilidad ni ejecución verificada.
- **H3:** IDs de claims/evidencia están definidos; `claims.jsonl` está vacío y los estados pueden respaldarse con declaraciones textuales no verificables (N1). Trazabilidad aplicada no demostrada.
- **H4:** destino resuelto excluido/inexistente se bloquea; queda la incoherencia de `target_symbol_id` en estados no resueltos (N4).
- **H5:** pasa para los nueve streams presentes, sin errores JSONL/IDs duplicados y con generación determinista y artefactos actuales. La aprobación se limita a estas comprobaciones; streams vacíos no dan cobertura semántica.


## Seguimiento de implementación N1-N4 — 2026-10-20

Este seguimiento registra cambios realizados después del hallazgo independiente
anterior. Conserva el veredicto histórico **REQUIERE CORRECCIONES**; no es una
revisión independiente ni una aprobación de H1-H5.

### Cambios y comprobaciones

| Hallazgo | Corrección aplicada | Evidencia ejecutada |
|---|---|---|
| N1 | Los campos que exigen texto usan `nonBlankString`. `review_id` requiere `review:<slug>`. `observed_at` exige `YYYY-MM-DDTHH:MM:SSZ` y el validador comprueba que sea fecha UTC real. Una revisión necesita evidencia `review` con resultado `passed`, reviewer, ID, timestamp y revisión Git válida. | Regresiones para incertidumbre en blanco, description/reviewer/ID en blanco, fecha arbitraria e imposible, revisión con evidencia válida y SHA existente. Los registros sin evidencia de revisión se rechazan; aprobación válida se conserva. |
| N2 | Evidencia de ejecución requiere texto significativo para comando, entorno y descripción; timestamp UTC válido y revisión completa SHA-1/SHA-256. El validador verifica que el objeto resuelva a un commit Git disponible. Resultados de evidencia deben concordar con `execution_status`; `not_applicable` no admite evidencia de ejecución. | Regresiones para comando/entorno/descripción vacíos, revisión `x`, fecha inválida, hash bien formado pero commit no disponible y contradicción entre evidencia y estado. `runtime_observed` sigue exigiendo estado `passed` y evidencia runtime `passed`. No se creó ni ejecutó observación de la aplicación. |
| N3 | Conteo físico: CRLF cuenta como un terminador; LF y CR aislado también; terminador final no crea línea adicional; contenido final sin terminador cuenta como línea. Archivo vacío cuenta cero. Símbolo módulo y evidencia de módulo vacío usan localizadores nulos; flujo no puede localizar líneas en vacío. | Pruebas con temporales vacíos, LF, CRLF, CR aislado, sin terminador final y una línea; rangos válidos e inválidos usaron el mismo lector. La generación completa validó el módulo vacío sin asignarle `1-1`. |
| N4 | `target_symbol_id` se comprueba siempre que aparezca, sin depender de `status`. IDs malformados fallan esquema; IDs ausentes de `symbols` fallan integridad cruzada. Los estados `unknown`, `unverifiable` y `expected_missing` siguen permitiendo omitir el destino. | Casos negativos con símbolo inexistente en cada estado no resuelto; caso positivo con destino simbólico existente en `unknown`; estados sin destino siguen pasando. |

### Ejecuciones registradas

Comandos ejecutados desde la raíz del repositorio, usando el Python incluido
en el entorno:

```text
python -m unittest discover -s tests -p test_inventory_tool.py -v
  19 tests, OK
python -m py_compile docs/book/inventory/inventory_tool.py tests/test_inventory_tool.py
  exit 0
python docs/book/inventory/inventory_tool.py generate
  exit 0; files=321 symbols=784 relations=1913 unresolved=1746 entries=41 deps=62
python docs/book/inventory/inventory_tool.py validate --write-report
  PASS: nueve streams, esquemas, integridad cruzada, archivos, determinismo,
  actualidad de artefactos y pruebas negativas
```

La implementación anterior reprodujo N1-N4 antes de editar: aceptó campos en
blanco/fechas arbitrarias, aceptó el destino simbólico inexistente, contó el
archivo vacío como una línea y subcontó CR aislado. También pasaban los 18
tests anteriores, que no incluían esos bordes. Después de las correcciones,
la suite ampliada pasa. La generación y validación no ejecutan la aplicación;
los streams `docs_cross_reference`, `control_flow` y `claims` permanecen
vacíos según el reporte regenerado.

### Estado y límites

N1-N4: **corregidos en implementación y cubiertos por regresiones; revisión
independiente pendiente**. El SHA se valida contra el almacén Git local: un
commit no disponible localmente no puede respaldar evidencia. Esto no prueba
que el comando registrado se haya ejecutado ni autentica a quien firma una
revisión. La validación sigue siendo estructural/semántica acotada; no prueba
comprensión de ramas, composición, excepciones, cobertura dinámica ni
veracidad de afirmaciones futuras.

**Recomendación:** solicitar una nueva revisión independiente de N1-N4 y del
diff antes de iniciar la reconstrucción del flujo de ejecución. H1-H5 no se
declaran aprobados por este seguimiento; H5 se limita a la validación de los
artefactos generados, no a completitud semántica.

## Revisión independiente final de N1-N4 y contrato v3 — 2026-10-20

**Veredicto: APROBADO CON LIMITACIONES para iniciar el análisis funcional.**
Este dictamen confirma las reglas de N1-N4 y las comprobaciones del contrato
v3 que se ejecutaron en esta revisión. No aprueba la infraestructura documental
completa, no cambia dictámenes históricos y no afirma que el flujo real de
OSM2Terrn haya sido ejecutado o reconstruido.

### Estado por hallazgo

| Hallazgo | Resultado | Evidencia y alcance |
|---|---|---|
| N1 — estados y revisiones | **Resuelto en el contrato revisado** | Se rechazaron incertidumbres solo de espacios, reviewer en blanco, ID de revisión mal formado, timestamps arbitrarios/imposibles y revisión sin evidencia aprobada. Se aceptó un registro válido con `review:<slug>`, UTC timestamp, reviewer significativo y SHA local resoluble. La regla de bloqueo acepta un motivo significativo. |
| N2 — evidencia de ejecución | **Metadatos y coherencia validados; ejecución real no demostrable por el validador** | Se rechazaron campos vacíos, timestamp inválido, SHA mal formado/no resoluble y resultados contradictorios; se aceptó SHA válido y una relación `runtime_observed` con evidencia de resultado `passed`; evidencia exclusivamente estática no satisface la regla. En una prueba sintética, un comando ficticio con metadatos completos también fue aceptado. Por diseño, el validador no comprueba logs, captura de salida ni que el comando se haya ejecutado. La documentación advierte esta limitación. |
| N3 — localizadores | **Resuelto en los casos probados** | Conteos observados: LF=2, CRLF=2, CR aislado=2, sin terminador final=2, una línea=1 y vacío=0. Pruebas existentes y probes independientes aceptaron rangos válidos, rechazaron límites excedidos y flujo `1-1` en archivo vacío. Los rangos de un archivo inexistente fallan como no verificables. La extracción y validación llaman al mismo `_line_count_bytes`. |
| N4 — referencias | **Resuelto en los casos probados** | Un `target_symbol_id` colgante fue rechazado en `unknown`, `unverifiable` y `expected_missing`; ID mal formado falla esquema; destino omitido en esos estados sigue siendo válido; símbolo existente en `unknown` se acepta. Para `resolved`, destino incluido disponible pasó; destino excluido y ruta ausente del inventario fallaron. |

### Casos y comandos ejecutados

Se inspeccionaron el estado de Git, la implementación, esquema, pruebas,
informes, progreso, README del inventario y los nueve streams. Se ejecutaron
los 19 tests y probes independientes en memoria; no se escribieron fixtures
en los streams.

```text
python -m unittest discover -s tests -p test_inventory_tool.py -v
  19 tests, OK
python -m py_compile docs/book/inventory/inventory_tool.py tests/test_inventory_tool.py
  exit 0
python docs/book/inventory/inventory_tool.py validate
  PASS: nueve JSONL, schemas, integridad cruzada, archivos incluidos,
  determinismo, vigencia y pruebas negativas; exit 0
git diff --check
  exit 0; avisos de finales de línea solo en archivos preexistentes
```

La validación revisó los nueve streams presentes: 321 archivos, 784 símbolos,
1.913 relaciones, 0 referencias documentales, 0 controles de flujo, 0 claims,
1.746 no resueltos, 41 entradas y 62 dependencias. IDs duplicados, JSONL
inválido, referencias cruzadas defectuosas, contenido obsoleto y divergencia
entre dos generaciones no fueron reportados. La prueba unitaria y el comando
`validate` son fuentes separadas: el primero ejercitó las regresiones; el
segundo validó los artefactos generados.

### Estado H1-H5

- **H1 — Contrato de estados:** las invariantes revisadas se aplican en esquema
  y validador. No se certifica que futuros motivos o revisiones sean
  semánticamente correctos, ni la calidad de cada análisis humano.
- **H2 — Relaciones y flujo:** los estados y tipos están representados, pero
  `control_flow.jsonl` está vacío. No hay reconstrucción del flujo, CFG,
  alcanzabilidad ni observaciones de ejecución verificadas.
- **H3 — Claims y trazabilidad:** el contrato de evidencia existe y las
  referencias estructurales se validan, pero `claims.jsonl` está vacío; no hay
  trazabilidad aplicada a explicaciones de capítulos.
- **H4 — Referencias documentales:** las reglas de destino se aplican en los
  casos probados, pero `docs_cross_reference.jsonl` está vacío; esto no
  demuestra cobertura de referencias reales.
- **H5 — Streams y regeneración:** **aprobado para la validación estructural
  ejecutada**: nueve streams, integridad cruzada, unicidad, determinismo y
  vigencia pasaron. No implica completitud semántica.

### Límites del diff y recomendación

El `git status` inicial ya mostraba cambios en 20 rutas rastreadas fuera de
esta revisión y `docs/book/`, `tests/test_inventory_tool.py` y otros elementos
sin seguimiento. `git diff --stat` no incluye archivos sin seguimiento, por lo
que no fue posible atribuir esos contenidos a un diff contra `HEAD`; se
inspeccionó el contenido actual y no se modificaron generador, esquema, tests
ni código de aplicación durante esta revisión. Los avisos de `git diff
--check` corresponden a finales de línea en archivos rastreados preexistentes.

**Recomendación:** sí, puede comenzar el análisis funcional y la reconstrucción
documental del flujo con relaciones etiquetadas como estáticas, inferidas o
pendientes de revisión. No se debe etiquetar ninguna ruta como `runtime_observed`
basándose únicamente en que el registro estructurado pase el validador; para
esa afirmación hace falta conservar y revisar evidencia real de ejecución. No
se ejecutó OSM2Terrn, tests de la aplicación, descargas geográficas ni
generación de terrenos.
