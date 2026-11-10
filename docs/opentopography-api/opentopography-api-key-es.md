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

### Recorrido actual en el código (inspección estática)

`osm2terrn/app/main.py` llama a `load_dotenv()`. El nombre de variable de
entorno es configurable mediante `providers.opentopo_api_key_env_var` en
`osm2terrn/config/models.py`; el servicio de elevación lee ese nombre de
`os.environ` en `osm2terrn/processing/terrain/elevation_service.py`.
El servicio construye una solicitud con:
   - `demtype`
   - `west/south/east/north`
   - `outputFormat=GTiff`
   - `API_Key=<tu_clave>`
2. Una respuesta exitosa se lee como GeoTIFF por el servicio. Esto describe el
   código fuente; no afirma que una solicitud real haya funcionado.

## 5) Comprobación de configuración

1. Crea `.env` con tu clave.
2. Confirma el nombre de variable configurado en `osm2terrn/config/models.py`.
3. No uses una descarga real como comprobación salvo que la tarea autorice
   expresamente solicitudes externas. Esta página no registra resultados de red.

## 6) Errores comunes

- **Variable mal escrita**: debe ser exactamente `OPENTOPO_ELEVATION_API_KEY`.
- **Clave vacía o inválida**: la descarga de elevación falla.
- **Sin `.env` en raíz**: `load_dotenv()` no carga tu clave.
- **Rate limit / red**: puede fallar aunque la clave sea correcta.

## 7) Buenas prácticas de seguridad

- Nunca pegues tu clave real en commits, PRs ni issues.
- Usa `.env.example` para documentar la variable requerida.
- Rota la clave si crees que se expuso.
