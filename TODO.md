* [x] Revisar Nodos Intersecciones
* [x] Alturas de calles con altura de terreno
* [ ] programar angelscipt para actualizar road meshes
* [ ] extender documentacion sobre ~~procedural_roads~~, tipos de datos principales, proyecciones, etc
* [x] agregar docstrings a todas las funciones

---

# Fase 1 — Consolidación de la arquitectura (Alta prioridad)

---

## □ Crear el modelo de dominio

**Objetivo**

Dejar de depender directamente de los objetos de OSMnx y trabajar con entidades propias.

**Consiste en**

* Crear clases como:
  * Road
  * Intersection
  * TerrainTile
  * Building
  * WaterBody
  * Railway
* Definir qué atributos tiene cada una.
* Crear funciones que conviertan OSM → modelos internos.

**Beneficio**

Toda la lógica posterior será independiente del proveedor de datos.

---

## □ Centralizar la configuración

**Objetivo**

Eliminar parámetros dispersos por todo el proyecto.

**Consiste en**

* Crear un sistema de configuración.
* Leer YAML/TOML.
* Configuración por módulos.

Ejemplo:

```
terrain.yaml
roads.yaml
buildings.yaml
materials.yaml
export.yaml
```

---

## □ Implementar sistema de caché

**Objetivo**

Evitar descargar y reprocesar datos.

**Consiste en**

Cachear

* OSM
* Elevación
* Imágenes
* Texturas
* Datos intermedios

---

## □ Reorganizar utils

Separar

```
utils/

geometry/
io/
logging/
config/
math/
```

para evitar que utils crezca indefinidamente.

---

# Fase 2 — Terreno (Muy alta prioridad)

---

* [x] agregar paletas de colores de pygmt y colorcet, opciones geo, bañometria, cubehelix y mezclas y rampas personalizadas (avance: aliases geo/cubehelix/bathymetry + cc:* y cet_*), creacion de paletas de colores personalizadas (LinearSegmentedColormap), integracion con nomenclatura x11/css4

## □ Mejorar la generación del heightmap

Agregar

* suavizado
* corrección de bordes
* relleno de vacíos
* normalización

---

## □ Implementar máscaras de terreno

Generar automáticamente

* roca
* arena
* barro
* nieve
* césped
* bosque

a partir de

* pendiente
* altura
* uso del suelo

---

## □ Sistema de materiales

Debe decidir automáticamente

```
grass

forest

rock

asphalt

gravel

sand

mud
```

según la información disponible.

---

## □ Texture splatting

Investigar funcionamiento de materiales de OGRE aplicado a texture splatting en rigs of rods

Implementar algoritmo basado en advanced terrain texture splatting por andrey mishkinis

Implementar el algoritmo moderno de mezcla de texturas.

Idealmente

* hasta 16 materiales
* blending suave
* weightmaps

---

## □ Generación de mapas auxiliares

Exportar

* normal map
* slope map
* curvature map
* ambient occlusion (opcional)
* roughness mask

---

# Fase 3 — Carreteras

---

## □ Clasificación automática

Clasificar

* motorway
* trunk
* primary
* secondary
* tertiary
* residential
* service
* track

---

## □ Intersecciones avanzadas

Actualmente funcionan.

Después agregar

* rotondas
* carriles
* radios automáticos
* rampas

---

## □ Puentes

Detectar

```
bridge=yes
```

y generar

* altura
* apoyos
* transición

---

## □ Túneles

Procesar

```
tunnel=yes
```

---

## □ Guardarraíles

Generarlos automáticamente.

---

## □ Banquinas

Agregar según el tipo de camino.

---

## □ Cunetas

Especialmente para caminos rurales.

---

# Fase 4 — Edificios

---

## □ Sistema de edificios

Crear modelo interno.

---

## □ Extrusión

Generar automáticamente

* altura
* techo
* materiales

---

## □ Techos

Soportar

* plano
* dos aguas
* cuatro aguas
* industrial

---

## □ Materiales de edificios

Detectar

* ladrillo
* hormigón
* chapa
* vidrio

---

# Fase 5 — Vegetación

---

## □ Bosques

Generación procedural.

---

## □ Árboles individuales

Usar

```
natural=tree
```

---

## □ Pastizales

---

## □ Cultivos

Detectar

```
farmland
orchard
vineyard
```

---

# Fase 6 — Agua

---

 □ Ríos

 □ Lagos

 □ Costa

 □ Humedales

 □ Playas

---

# Fase 7 — Objetos

---

 □ Señales

 □ Semáforos

 □ Alumbrado

 □ Postes eléctricos

 □ Barreras

 □ Mobiliario urbano

---

# Fase 8 — Exportadores

---

 □ Exportador .terrn2 completo

 □ Exportador .tobj

 □ Exportador .odef

 □ Exportador de materiales

 □ Exportador de texturas

---

# Fase 9 — Optimización

---

## □ Procesamiento paralelo

Multiprocessing.

---

## □ Streaming de datos

Para mapas enormes.

---

## □ Uso eficiente de memoria

---

## □ Benchmarks

Medir tiempos.

---

# Fase 10 — Calidad

---

## □ Cobertura >95 %

---

## □ Tests de integración

---

## □ Tests de mapas reales

---

## □ CI automática

GitHub Actions.

---

## □ Versionado semántico

---

# Fase 11 — Ecosistema

---

## □ API pública

Que otros programas puedan usar osm2terrn como librería.

---

## □ Sistema de plugins

Por ejemplo

```
plugins/

roads/

terrain/

vegetation/

exporters/
```

---

## □ SDK

Para desarrollar extensiones.

---

## □ Documentación para desarrolladores

Arquitectura, diagramas y ejemplos.

---

# Fase 12 — Calidad visual (Visión a largo plazo)

Esta sería la etapa "premium", donde el objetivo deja de ser generar un mapa funcional y pasa a ser generar un mapa que luzca casi profesional.

* □ Sistema PBR completo (albedo, normal, roughness, AO, height).
* □ Texture splatting avanzado basado en pendientes, curvatura y altura (inspirado en el trabajo de Andrey Mishkinis que estuvimos analizando).
* □ Biblioteca de materiales libres con metadatos y atribuciones automáticas (integrando fuentes como 3dassets.one y otras colecciones con licencias abiertas).
* □ Biomas procedurales (vegetación, suelos y materiales según clima y región).
* □ Colocación procedural de rocas, árboles y detalles menores.
* □ Sistema de LOD para objetos y vegetación.
* □ Variantes aleatorias de edificios y materiales para reducir repeticiones.
* □ Iluminación y parámetros ambientales configurables por región.
* □ Optimización específica para mapas extensos de Rigs of Rods.

---

# Orden de prioridad recomendado

Si el objetivo es llegar cuanto antes a una versión **1.0** sólida y extensible, este sería el orden que seguiría:

1. **Consolidación de la arquitectura** (modelo de dominio, configuración, caché y reorganización de utilidades).
2. **Motor de terreno** (heightmaps, máscaras, materiales y texture splatting).
3. ​**Sistema avanzado de carreteras**​.
4. ​**Edificios**​.
5. ​**Agua y vegetación**​.
6. ​**Objetos urbanos**​.
7. ​**Optimización y rendimiento**​.
8. ​**Cobertura de pruebas y automatización (CI/CD)**​.
9. ​**API pública y sistema de plugins**​.
10. ​**Calidad visual y generación procedural avanzada**​.