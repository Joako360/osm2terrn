# OpenTopography API: key setup, `.env`, and project usage

This document explains how to:

1. Get an OpenTopography API key.
2. Configure it in a local `.env` file.
3. Understand how OSM2terrn uses that key at runtime.

## 1) How to get an OpenTopography API key

1. Create an account (or sign in) in the OpenTopography portal.
2. Go to the API section (Global DEM API).
3. Generate or copy your personal API key.
4. Store it securely (a password manager is recommended).

Project endpoint reference:
- `https://portal.opentopography.org/API/globaldem`

## 2) How to configure the key with `.env`

Create a `.env` file in the repository root:

```env
OPENTOPO_ELEVATION_API_KEY=your_real_key_here
```

> Important: `.env` is already ignored by Git in `.gitignore`, so your key should not be committed.

## 3) Recommended template (`.env.example`)

Use `.env.example` to document required configuration without leaking secrets:

```env
# Copy this file to .env and replace with your real key
OPENTOPO_ELEVATION_API_KEY=replace_with_your_opentopography_key
```

## 4) How the key is loaded inside the project

### Step A: automatic `.env` loading

At startup, `src/main.py` calls `load_dotenv()`, so variables from `.env` are loaded into the process environment.

### Step B: key retrieval

`src/utils/constants.py` defines:
- `get_opentopo_elevation_api_key()`

This function reads `OPENTOPO_ELEVATION_API_KEY` from environment variables.

### Step C: API request usage

In `src/processing/heightmap_handler.py`:
1. `get_opentopo_elevation_api_key()` is called.
2. The `requests.get(...)` parameters include:
   - `demtype`
   - `west/south/east/north`
   - `outputFormat=GTiff`
   - `API_Key=<your_key>`
3. The elevation GeoTIFF is downloaded and parsed.

## 5) Quick setup test

1. Create `.env` with your API key.
2. Run the project (`python main.py`).
3. Execute Download → Export.
4. Check elevation logs (you should see masked key usage and successful download).

## 6) Common errors

- **Wrong variable name**: it must be exactly `OPENTOPO_ELEVATION_API_KEY`.
- **Missing/invalid key**: elevation download fails.
- **No `.env` in project root**: `load_dotenv()` cannot load your key.
- **Rate limits/network issues**: requests may fail even with a valid key.

## 7) Security best practices

- Never paste your real key in commits, PRs, or issues.
- Use `.env.example` to document required environment variables.
- Rotate your key if you suspect exposure.
