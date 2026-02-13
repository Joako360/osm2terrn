# Copilot Instructions for OSM2terrn Project

## Project Description
OSM2terrn is an open-source Python project that generates realistic terrains for the Rigs of Rods simulator using real-world data from OpenStreetMap (OSM) and OpenTopoData. The codebase  is modular, clear, and maintainable, organized by function:
- `src/data/`: OSM data download/parsing
- `src/processing/`: Data processing (heightmaps, networks, textures)
- `src/utils/`: Utilities (geometry, logging, constants)
- `main.py`: CLI orchestrator

## Project-Specific Patterns
- Centralized logging: Use `utils/logger.py` (`get_logger`, `log_info`, `log_warning`, `log_error`).
- Modular processing: Separate download, transformation, and export logic into distinct files.
- Use only dependencies from `requirements.txt` unless clearly justified.
- Geographic data is projected/translated to local coordinates via `utils/geometry.py`.

## Project Structure and Modularity
- Organize code in modular files within the folders:
  - `/data/` for data parsing and downloading (OSM, elevation).
  - `/processing/` for processing data into heightmaps, textures, etc.
  - `/utils/` for general-purpose utilities like geometry helpers, file I/O, and logging.
  - `/scripts/` for example or automation scripts.
- Suggest splitting large functions or files into smaller modules when appropriate.
- Follow the principle of separation of concerns; avoid monolithic files.

## Key Workflows
- Run CLI: `python main.py` and follow the interactive menu to download, process, and export maps.
- Heightmaps: Generated as `heightmap.png` and `groundmap.png` via `processing/heightmap_handler.py`.
- Road networks: Processed/exported with `processing/road_network_formatter.py` to `roads.tobj`.
- Data acquisition: OSM/elevation via `data/osm_data_handler.py` and external APIs.

All code, comments, and documentation should be written in **English**, as the project is aimed at an international community.

## Coding Standards

### General Style
- Follow **PEP8** coding style strictly, Python 3.10+.
- When not specified by PEP8, follow the most widely adopted and standardized conventions.
- Maintain clean and readable code, balancing readability and performance. Avoid overly academic or cryptic code.

### Naming Conventions
- Variables, functions, and methods: `snake_case`
- Classes: `CamelCase`
- Constants: `UPPER_SNAKE_CASE`
- Modules and packages: `snake_case`
- Private methods and variables: Prefix with a single underscore `_name`
- Special methods or attributes: Prefix and suffix with double underscores `__name__`
- Instance methods must use `self` as the first argument.
- Class methods must use `cls` as the first argument.
- Boolean variables must have prefixes like `is_`, `has_`, or similar that indicate a yes/no answer.
- Avoid single-letter variable names except for loop counters.
- Avoid variable names starting with numbers or ambiguous names.

### File Naming
- Use descriptive but concise filenames for modules.
- Avoid generic names like `helpers.py`. Instead, prefer names that describe the module's purpose clearly.
- Filenames should follow `snake_case` convention.

### Documentation and Comments
- Always suggest **docstrings for public functions**, following PEP257 style.
- Write **comments in English**.
- Add explanatory comments in complex or non-obvious code sections.
- Emojis can be used in comments or logs when they help convey meaning or improve clarity 🎉.

## Integration & Data Flow
- Typical flow: user selects city → downloads OSM/elevation → processes → exports files for Rigs of Rods.
- Modules communicate via data structures (dict, GeoDataFrame, NetworkX).
- Global constants/API config in `utils/constants.py`.

## Libraries and Compatibility
- Only use libraries listed in `requirements.txt` for code suggestions.
- Copilot may propose the addition of a new library if it is well-justified and relevant.
- Target Python version is **3.10 or later**. Ensure all code suggestions are compatible.
- Avoid suggesting unnecessary dependencies.

## Logging and Error Handling
- Suggest adding logs using the existing `logger.py` module.
- Logs should provide meaningful information about key actions, warnings, and potential errors.
- Use informative and friendly log messages when appropriate.

## Contribution & Maintenance
- Prioritize clarity/maintainability over clever tricks.
- Suggest splitting large functions into smaller modules.
- New dependencies must be relevant and justified.
- Follow community rules and see `CONTRIBUTING.md` for PR/style details.

## Code Contributions Guidelines
- Write code that is understandable for contributors of varying experience levels.
- Prioritize clarity and maintainability.
- Explicit code is preferred over clever "one-liners" that harm readability.
- Follow the modular project structure and file organization.

## Language and Tone
- All suggestions, code, comments, and documentation should be in **English**.
- Copilot may use emojis in comments or logs if they enhance clarity or expressiveness 🤖.

## Example Patterns
- Logging:
  ```python
  from utils.logger import get_logger, log_info
  logger = get_logger("module_name")
  log_info(logger, "Relevant message")
  ```
- Heightmap processing:
  ```python
  from processing.heightmap_handler import generate_heightmaps
  generate_heightmaps(bounds)
  ```
- OSM data handling:
  ```python
  from data.osm_data_handler import download_data
  download_data(place_name, which_option)
  ```
- Road network export :
  ```python
  from processing.road_network_formatter import build_roads_from_place
  roads, terrn2_block = build_roads_from_place(place_name, origin_lon, origin_lat)
  ```