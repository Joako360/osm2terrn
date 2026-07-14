# OpenTopography API: clave, `.env` e integración en OSM2terrn

Este documento explica cómo:

1. Obtener una clave de OpenTopography.
2. Configurarla en un archivo `.env`.
3. Entender cómo el proyecto usa esa clave al pedir elevación.

## 1) Cómo obtener la clave API de OpenTopography

1. Crea una cuenta (o inicia sesión) en el portal de OpenTopography.
2. Ve a la sección de APIs (Global DEM).
3. Genera o copia tu API key personal.
4. Guarda la clave en un lugar seguro (password manager recomendado).

Referencia del endpoint que usa este proyecto:
- `https://portal.opentopography.org/API/globaldem`

## 2) Cómo incluir la clave en el proyecto con `.env`

En la raíz del repo, crea un archivo llamado `.env`:

```env
OPENTOPO_ELEVATION_API_KEY=tu_clave_real_aqui
```

> Importante: `.env` ya está ignorado por Git en `.gitignore`, así que tu clave no debería subirse al repositorio.

## 3) Plantilla recomendada (`.env.example`)

Para compartir configuración sin exponer secretos, usa `.env.example`:

```env
# Copy this file to .env and replace with your real key
OPENTOPO_ELEVATION_API_KEY=replace_with_your_opentopography_key
```

## 4) Cómo se carga la clave dentro del proyecto

### Paso A: carga automática de `.env`

Al iniciar la app, `osm2terrn/main.py` ejecuta `load_dotenv()`, por lo que variables del `.env` pasan al entorno del proceso.

### Paso B: lectura de la variable

`osm2terrn/utils/constants.py` define:
- `get_opentopo_elevation_api_key()`

Esta función lee `OPENTOPO_ELEVATION_API_KEY` desde variables de entorno.

### Paso C: uso al llamar la API

`osm2terrn/processing/heightmap_handler.py`:
1. Llama a `get_opentopo_elevation_api_key()`.
2. Construye parámetros de `requests.get(...)` con:
   - `demtype`
   - `west/south/east/north`
   - `outputFormat=GTiff`
   - `API_Key=<tu_clave>`
3. Descarga el GeoTIFF de elevación.

## 5) Prueba rápida de configuración

1. Crea `.env` con tu clave.
2. Ejecuta el proyecto (`python main.py`).
3. Corre flujo Download → Export.
4. Verifica logs de elevación (deberías ver uso de API key enmascarada y descarga exitosa).

## 6) Errores comunes

- **Variable mal escrita**: debe ser exactamente `OPENTOPO_ELEVATION_API_KEY`.
- **Clave vacía o inválida**: la descarga de elevación falla.
- **Sin `.env` en raíz**: `load_dotenv()` no carga tu clave.
- **Rate limit / red**: puede fallar aunque la clave sea correcta.

## 7) Buenas prácticas de seguridad

- Nunca pegues tu clave real en commits, PRs ni issues.
- Usa `.env.example` para documentar la variable requerida.
- Rota la clave si crees que se expuso.
