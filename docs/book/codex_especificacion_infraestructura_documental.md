# Especificación para implementar la infraestructura documental

**OSM2Terrn — Etapa 1.2**

Esta especificación prepara el trabajo de documentación; no redacta capítulos técnicos ni propone cambios al código del producto. La inspección fue estática: no ejecuté la aplicación ni los tests. Las referencias de líneas apuntan al estado del repositorio visible durante esta revisión y pueden cambiar.

## 1. Evaluación del informe inicial

### Hechos comprobados en esta revisión

El informe declara que es una inspección estática y que no ejecutó la aplicación, los tests ni servicios externos. También advierte que registró un árbol de trabajo con cambios locales. Estas limitaciones están en [`initial_repository_audit.md`](C:/Users/Joaquin/OneDrive/Documentos/GitHub/osm2terrn/docs/book/initial_repository_audit.md:3).

Los puntos de entrada principales que identifica son plausibles y sus vínculos centrales se confirman en el código disponible:

- [`osm2terrn/__main__.py`](C:/Users/Joaquin/OneDrive/Documentos/GitHub/osm2terrn/osm2terrn/__main__.py:1) importa `main` desde `osm2terrn.app.main` y termina con `SystemExit(main())`.
- [`pyproject.toml`](C:/Users/Joaquin/OneDrive/Documentos/GitHub/osm2terrn/pyproject.toml:105) declara el comando de consola `osm2terrn = "osm2terrn.app.main:main"`.
- [`osm2terrn/app/main.py`](C:/Users/Joaquin/OneDrive/Documentos/GitHub/osm2terrn/osm2terrn/app/main.py:156) define `main`; en la línea 180 llama a `mainmenu.run()`.
- [`osm2terrn/cli/commands.py`](C:/Users/Joaquin/OneDrive/Documentos/GitHub/osm2terrn/osm2terrn/cli/commands.py:82) contiene `load()`, que muestra “Loading functionality coming soon”.
- [`osm2terrn/processing/orchestrator.py`](C:/Users/Joaquin/OneDrive/Documentos/GitHub/osm2terrn/osm2terrn/processing/orchestrator.py:187) define `export_terrain_assets`, referenciado por la ruta de exportación descrita en el informe.

Por tanto, `python -m osm2terrn` y el comando instalado son **entradas declaradas o visibles estáticamente**. Esto no demuestra que funcionen en un entorno dado ni que sean las únicas rutas de ejecución.

### Contradicciones entre el informe y el árbol actual

El informe dice que no existía `osm2terrn/cache/` cuando se hizo la auditoría ([informe, líneas 39–44](C:/Users/Joaquin/OneDrive/Documentos/GitHub/osm2terrn/docs/book/initial_repository_audit.md:39)). En el árbol disponible ahora sí aparece ese paquete, con `__init__.py` y módulos `backend.py`, `file_cache.py`, `keys.py`, `manager.py`, `metadata.py`, `serializers.py` y `version.py`. Además, hay tests con nombres relacionados con caché, entre ellos `tests/test_cache_infrastructure.py` y `tests/test_osm_loader_cache.py`.

Esto **no demuestra** que el paquete sea correcto, que todos los imports se resuelvan, ni que los tests pasen. Sí significa que el hallazgo de ausencia debe marcarse como **observación histórica de la instantánea de auditoría**, no como descripción del árbol actual.

La auditoría menciona que `docs/book/initial_repository_audit.md` no existía en el momento de inspección (líneas 14–15), pero el archivo ahora está presente. De nuevo, ambas afirmaciones pueden ser correctas en momentos distintos.

El informe registra 19 archivos rastreados modificados y un archivo sin seguimiento (líneas 16–21). En la revisión actual, `git status --short` muestra 19 rutas rastreadas modificadas y archivos sin seguimiento bajo `docs/architecture/` **y** `docs/book/`. No se debe atribuir autoría ni intención a esos cambios. La instantánea actual tampoco es un checkout limpio.

### Hallazgos del informe que requieren una revisión más completa

El informe describe diferencias entre documentación y configuración, por ejemplo el requisito Python de `pyproject.toml` frente al que declara README/CONTRIBUTING, y referencias a `main.py`, `requirements.txt` y `src/` que señala como inexistentes ([informe, líneas 285–317](C:/Users/Joaquin/OneDrive/Documentos/GitHub/osm2terrn/docs/book/initial_repository_audit.md:285)). Esta revisión comprobó los valores y rutas centrales de `pyproject.toml` y que `main.py`, `requirements.txt` y `src/` no aparecen en el árbol inspeccionado. La comprobación de cada discrepancia documental —incluidas las referencias obsoletas y el nombre de licencia— deberá repetirse al generar el inventario.

El informe identifica preguntas abiertas sobre proveedor de elevación, intención de `load()`, comando de tests mantenido, scripts admitidos y archivos de ejemplo. Esas cuestiones no se resuelven por inspeccionar nombres o declaraciones: algunas requieren localizar los puntos de uso; otras, consultar a quien mantiene el proyecto o ejecutar flujos con condiciones controladas.

### Inferencias y pendientes

- **Inferencia:** `osm2terrn.app.main:main` es una entrada principal probable porque está declarada en el módulo ejecutable y en los metadatos de empaquetado. La condición de “principal y soportada” debe respaldarse con documentación del proyecto o confirmación del mantenedor.
- **Pendiente:** confirmar la lista completa de entradas, incluidas scripts, notebooks, comandos de desarrollo, ejecuciones directas y cualquier ruta dinámica.
- **Pendiente:** regenerar las cifras de archivos del informe, pues describen una instantánea anterior.
- **Pendiente:** resolver imports y llamadas no estáticos y verificar comportamiento con tests o ejecución.
- **Pendiente:** decidir cuáles de los documentos existentes siguen siendo autoridad y cuáles contienen propuestas o referencias obsoletas.

El inventario inicial deberá tomar el árbol actual como objeto de análisis y conservar la fecha o revisión de Git asociada a cada generación. Debe guardar por separado observaciones, inferencias y preguntas abiertas. El informe original no se sobrescribirá para esconder el cambio de estado de la caché; se le añadirá una revisión fechada que explique la discrepancia.

## 2. Estructura documental

```text
docs/book/
├── README.md
├── initial_repository_audit.md
├── book_plan.md
├── assistant_workflow.md
├── audit_review.md
├── progress/
│   ├── coverage.md
│   └── decisions.md
├── inventory/
│   ├── README.md
│   ├── schema.json
│   ├── files.jsonl
│   ├── symbols.jsonl
│   ├── relations.jsonl
│   └── docs_cross_reference.jsonl
├── questions/
│   └── open_questions.md
├── chapters/
│   ├── README.md
│   └── diagrams/
│       └── README.md
├── reviews/
│   └── README.md
└── templates/
    ├── chapter.md
    ├── review.md
    └── handoff.md
```

El informe inicial se conserva como evidencia histórica. `audit_review.md` registra su contraste con el árbol actual: hallazgos, fuentes, diferencias temporales, estados y pendientes.

`book_plan.md` define objetivos, alcance, dependencias y estado de cada etapa y capítulo. No debe declarar de antemano componentes que la inspección no haya encontrado.

`inventory/` contiene registros estructurados, preferentemente generados mediante herramientas estáticas. `coverage.md` resume el alcance y estado sin duplicar los registros fuente. Los diagramas documentan el tipo de relación representada y cómo se obtuvo.

## 3. Contratos de datos

Los inventarios usarán JSONL: un objeto JSON por línea, versionado y validado contra `schema.json`. Las rutas serán relativas a la raíz del repositorio, con `/` como separador. La extracción será determinista para un mismo árbol, versión del extractor y configuración.

### Registro de archivo

```json
{
  "file_id": "file:osm2terrn/app/main.py",
  "path": "osm2terrn/app/main.py",
  "kind": "python_source",
  "git_state": "modified",
  "analysis_status": "inventory_generated",
  "evidence": [],
  "uncertainties": [],
  "limitations": []
}
```

`git_state` distinguirá, cuando pueda obtenerse, `tracked`, `modified`, `untracked`, `ignored` y `unknown`. Archivos excluidos se registrarán por categoría y motivo; no se leerán contenidos sensibles.

### Registro de símbolo

```json
{
  "symbol_id": "py:osm2terrn/app/main.py::main",
  "file_id": "file:osm2terrn/app/main.py",
  "path": "osm2terrn/app/main.py",
  "qualified_name": "main",
  "kind": "function",
  "owner_symbol_id": null,
  "start_line": 156,
  "end_line": 183,
  "signature": "main(argv: list[str] | None = None) -> int",
  "analysis_status": "inventory_generated",
  "evidence": [],
  "uncertainties": [],
  "limitations": []
}
```

Los identificadores derivan de ruta y nombre cualificado, no de líneas. Para símbolos anidados se incluirá su clase o función propietaria. Casos de homónimos u overloads requieren una regla de desambiguación estable, documentada en el esquema. Las líneas inclusivas pueden omitirse si el extractor no logra determinarlas.

### Relaciones

`relations.jsonl` expresará las relaciones con registros dirigidos:

```json
{
  "relation_id": "rel:<identificador-determinista>",
  "source_symbol_id": "py:<ruta>::<caller>",
  "target_symbol_id": "py:<ruta>::<callee>",
  "kind": "calls",
  "resolution": "static",
  "evidence": [],
  "analysis_status": "inventory_generated",
  "uncertainties": [],
  "limitations": []
}
```

Tipos mínimos: `calls`, `imports`, `inherits`, `contains`, `references_test`. Resolución mínima: `static`, `inferred`, `runtime_observed`, `unresolved`. Una llamada entrante se obtiene consultando relaciones cuyo destino es el símbolo; una saliente, las que lo tienen como origen. Si se materializan ambos sentidos, el dato debe poder regenerarse de las mismas relaciones.

`references_test` enlazará a una función de test si la relación se puede resolver estáticamente. Si solo se conoce el archivo de test o el vínculo es una hipótesis semántica, la resolución y la evidencia deben indicarlo. Una referencia a un test **no** significa que haya pasado.

### Evidencia, estado e incertidumbre

Cada registro debe permitir localizar evidencia con ruta, líneas opcionales, tipo y descripción breve. Tipos de evidencia sugeridos: `source`, `test_source`, `configuration`, `documentation`, `runtime_observation`. Los estados deben distinguir al menos `not_started`, `inventory_generated`, `reviewed`, `runtime_verified`, `blocked`. Los estados no implican calidad por sí mismos: el significado y las condiciones de transición se documentan.

Las incertidumbres describen dudas concretas; las limitaciones, lo que el método no puede determinar. Nunca se agregan valores de secretos: como máximo, nombres de variables de entorno si son pertinentes.

## 4. Trazabilidad libro–código

Cada capítulo y diagrama tendrá un identificador estable, por ejemplo `chapter:<slug>` y `diagram:<slug>`. Las afirmaciones técnicas verificables llevarán referencias a ruta y símbolo, con líneas cuando ayuden a localizar el pasaje.

Las afirmaciones inferidas se etiquetarán y citarán las premisas que las motivan. Las observaciones de ejecución deben identificar comando, entorno y resultado registrado. Las referencias de línea no son anclas permanentes: la ruta y el identificador de símbolo son obligatorios cuando el símbolo esté disponible, y el revisor debe comprobar que la evidencia aún respalda el texto.

Cada diagrama indicará qué representa: imports, llamadas estáticas, herencia, flujo inferido o comportamiento observado. Un grafo estático no se presentará como un grafo real de ejecución. Las explicaciones sin evidencia verificable no se publican como hechos; quedan como preguntas abiertas o se revisan.

## 5. Coordinación de Copilot y Codex

### Responsabilidades

- **GitHub Copilot** implementa los archivos, esquemas, plantillas y herramientas de extracción bajo esta especificación. Contrasta los datos con el árbol y mantiene los artefactos generados. No convierte un diseño propuesto o un nombre de test en evidencia de comportamiento.
- **ChatGPT/Codex** revisa el informe inicial y las conclusiones de Copilot de forma independiente. Comprueba citas y límites, busca contradicciones en el código disponible y entrega hallazgos con evidencia. No declara que una prueba pase sin resultado de ejecución.

### Entregas y control de duplicación

Cada entrega usa `templates/handoff.md`: objetivo, revisión/commit inspeccionado, archivos tocados, comandos y resultados, hallazgos, incertidumbres, limitaciones y trabajo pendiente. Las revisiones usan `templates/review.md`: identificador, prioridad, afirmación, evidencia, impacto, veredicto y acción sugerida.

Copilot mantiene esquemas y extractores; Codex produce una revisión independiente antes de que esas conclusiones se marquen como verificadas. Se asigna un dueño por archivo en cada lote. Inventarios generados se regeneran desde la herramienta; no se editan manualmente sin explicar la excepción y evitar que la siguiente generación descarte cambios.

`coverage.md` registra estado por archivo o símbolo, capítulos relacionados, última revisión y cobertura pendiente. `open_questions.md` asigna a cada pregunta un identificador, evidencia ya consultada, responsable y condición para cerrarla. `decisions.md` registra decisiones de documentación con fecha y justificación, sin reinterpretar la implementación.

## 6. Automatización y revisión semántica

**Automatizable con la biblioteca estándar de Python:** enumerar archivos; filtrar por reglas explícitas; extraer con `ast` módulos, clases, funciones, métodos, firmas aproximadas, docstrings, líneas, imports, decoradores y herencia escrita directamente; detectar guards de ejecución directa; producir relaciones sintácticas de llamadas; validar esquemas, IDs y enlaces; y comprobar consistencia de rutas.

El extractor debe listar archivos omitidos, fallidos y no interpretados. Debe identificar sus resultados como estáticos y no esconder llamadas sin resolver.

**Requiere inspección semántica o ejecución:** despacho dinámico, reflexión, alias complejos, plugins, imports condicionales, efectos de decoradores, ramas dependientes del entorno, comportamiento de APIs, efectos secundarios, flujo de datos real y soporte oficial de scripts. Los tests pueden aportar evidencia sobre las rutas que ejercitan, pero no prueban las que no ejecutan. Toda evidencia de ejecución debe registrar qué se ejecutó y en qué condiciones.

## 7. Criterios de aceptación

La infraestructura inicial se acepta si se puede comprobar que:

1. La estructura documental existe y su README explica fuentes de verdad, regeneración, exclusiones y estados.
2. El esquema acepta registros válidos y rechaza IDs duplicados, rutas absolutas y referencias rotas.
3. Una ejecución repetida del extractor sobre el mismo árbol produce inventarios idénticos.
4. Los archivos omitidos, fallidos y dinámicos se registran; no se reporta cobertura total por defecto.
5. Símbolos y relaciones enlazan a registros existentes, y líneas de origen son válidas cuando están presentes.
6. Las llamadas estáticas están diferenciadas de relaciones inferidas y observaciones de ejecución.
7. El inventario de tests distingue referencias de resultados de ejecución.
8. Plantillas de capítulo y diagrama exigen referencias y tipo de evidencia para afirmaciones técnicas.
9. Progreso, preguntas abiertas, decisiones y limitaciones tienen formatos consistentes y rastreables.
10. Una persona distinta del autor puede validar o regenerar los artefactos siguiendo las instrucciones.
11. La revisión del informe marca como histórica la ausencia de `osm2terrn/cache/` descrita en la auditoría, y registra la presencia actual verificada.
12. Ningún archivo generado incluye secretos ni requiere dependencias nuevas sin justificación documentada.

## 8. Riesgos y limitaciones

- La auditoría representa una instantánea anterior y el árbol actual está modificado. No mezclar estados temporales ni atribuir cambios a una persona.
- `ast` no resuelve todas las llamadas; los grafos requieren etiquetas de resolución y límites explícitos.
- Los números de línea cambian. No usarlos como únicos identificadores.
- El mapeo test–código puede ser parcial y no implica cobertura de ejecución.
- La lista de entradas estáticas puede omitir rutas dinámicas o herramientas de desarrollo.
- Los archivos ignorados, locales o voluminosos requieren exclusiones cuidadosas. Registrar categorías y metadatos seguros, nunca secretos o contenido privado.
- Las discrepancias entre documentación y código son hallazgos de documentación; no autorizan a “arreglar” el comportamiento del producto dentro de esta etapa.

## 9. Archivos para la siguiente tarea

Orden sugerido de creación:

1. `docs/book/README.md`
2. `docs/book/audit_review.md`
3. `docs/book/book_plan.md`
4. `docs/book/assistant_workflow.md`
5. `docs/book/progress/coverage.md`
6. `docs/book/progress/decisions.md`
7. `docs/book/inventory/README.md`
8. `docs/book/inventory/schema.json`
9. `docs/book/inventory/files.jsonl`
10. `docs/book/inventory/symbols.jsonl`
11. `docs/book/inventory/relations.jsonl`
12. `docs/book/inventory/docs_cross_reference.jsonl`
13. `docs/book/questions/open_questions.md`
14. `docs/book/chapters/README.md`
15. `docs/book/chapters/diagrams/README.md`
16. `docs/book/reviews/README.md`
17. `docs/book/templates/chapter.md`
18. `docs/book/templates/review.md`
19. `docs/book/templates/handoff.md`

El informe existente, `docs/book/initial_repository_audit.md`, se conserva sin reescritura. La especificación no exige aún implementar el extractor; esa herramienta podrá proponerse después de validar que los contratos y reglas de exclusión son suficientes.

## Adenda — Contrato v3 (2026-10-20)

Esta adenda conserva la especificación aprobada y define las decisiones que
resuelven H1–H4 en `reviews/phase-1-4-infrastructure-audit.md`:

- Cada record mantiene cuatro ejes independientes: `inventory_status`,
  `analysis_status`, `documentation_status`, `execution_status`. El generador
  registra inventario y análisis estático, pero jamás marca revisión humana,
  aprobación editorial o ejecución como completadas.
- `relations.jsonl` distingue contención léxica, composición/agregación,
  ramas/excepciones y relaciones hacia IDs de dependencia. Los registros
  localizados de `control_flow.jsonl` son estáticos; no constituyen un CFG ni
  una observación de ramas ejecutadas. El extractor actual deja este stream
  vacío.
- `claims.jsonl` asigna IDs estables a afirmaciones y las enlaza con IDs de
  evidencia. La evidencia de tests/ejecución registra comando, test ID cuando
  corresponda, entorno, resultado, revisión del repositorio y fecha. Las líneas
  son localizadores secundarios.
- Referencias documentales usan `resolved`, `expected_missing`, `unknown` o
  `unverifiable`. Solo el estado `resolved` requiere `target_path`; los otros
  conservan `original_reference`.

Los contratos v3, validaciones agregadas, streams adicionales y ejemplos
positivos/negativos se encuentran en `inventory/schema.json`,
`inventory/inventory_tool.py` y `tests/test_inventory_tool.py`. La adenda no
declara capítulos terminados ni comportamiento de aplicación ejecutado.
