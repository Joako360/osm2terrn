import numpy as np
from matplotlib.colors import Colormap, to_rgb
import matplotlib.pyplot as plt

from osm2terrn.utils.logger import get_logger, log_warning
from osm2terrn.processing.terrain.terrain_colormap_colors import PRESETS

logger = get_logger("terrain_colormap_ops")


def normalize01(a):
    a = np.asarray(a, dtype=float)
    amin = np.nanmin(a)
    amax = np.nanmax(a)
    if amin == amax:
        return np.zeros_like(a)
    return np.clip((a - amin) / (amax - amin), 0.0, 1.0)


def smoothstep(edge0, edge1, x):
    x = np.asarray(x)
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def sample_cmap(cmap, h):
    h = np.clip(h, 0.0, 1.0)
    return cmap(h)[..., :3]


class Stage:
    def apply(self, h, rgb=None):
        return h, rgb


class HeightWarp(Stage):
    def __init__(self, gamma: float = 1.0):
        self.gamma = gamma

    def apply(self, h, rgb=None):
        h = np.power(h, self.gamma)
        return h, rgb


class BaseMap(Stage):
    def __init__(self, cmap: Colormap):
        self.cmap = cmap

    def apply(self, h, rgb=None):
        return h, sample_cmap(self.cmap, h)


class BlendMap(Stage):
    def __init__(self, cmap: Colormap, low: float = 0.0, high: float = 1.0, strength: float = 1.0):
        self.cmap = cmap
        self.low = low
        self.high = high
        self.strength = strength

    def apply(self, h, rgb=None):
        other = sample_cmap(self.cmap, h)
        alpha = smoothstep(self.low, self.high, h)[..., None] * self.strength
        if rgb is None:
            return h, other
        rgb = (1 - alpha) * rgb + alpha * other
        return h, np.clip(rgb, 0, 1)


class HeightTint(Stage):
    def __init__(self, low_color: str = "white", high_color: str = "white", strength: float = 0.15):
        self.low_color = low_color
        self.high_color = high_color
        self.strength = strength

    def apply(self, h, rgb=None):
        if rgb is None:
            return h, rgb
        low = np.array(to_rgb(self.low_color))
        high = np.array(to_rgb(self.high_color))
        tint = (1 - h[..., None]) * low + h[..., None] * high
        rgb = (1 - self.strength) * rgb + self.strength * rgb * tint
        return h, np.clip(rgb, 0, 1)


class TerrainPipeline:
    def __init__(self, stages):
        self.stages = stages

    def render(self, elevation):
        h = normalize01(elevation)
        rgb = None
        for stage in self.stages:
            h, rgb = stage.apply(h, rgb)
        return np.clip(rgb, 0, 1) if rgb is not None else None

    __call__ = render


PRESET_ALIASES = {
    "geo": "gist_earth",
    "cubehelix": "cubehelix",
    "bathymetry": "ocean",
    "earth": "terrain",
    "dem4": "terrain",
    "relief": "terrain",
    "bathy": "ocean",
}


def render_heightmap_rgb(elevation: np.ndarray, cmap_name: str = "gist_earth") -> np.ndarray:
    cmap = resolve_ground_colormap(cmap_name)
    return (cmap(normalize01(elevation))[:, :, :3] * 255).astype(np.uint8)


def resolve_ground_colormap(cmap_name: str) -> Colormap:
    requested = (cmap_name or "gist_earth").strip()
    key = requested.lower()

    if key in PRESETS:
        cmap = PRESETS[key]
        if cmap is not None:
            return cmap
        log_warning(logger, f"Preset '{requested}' is unavailable. Falling back to gist_earth.")
        return plt.get_cmap("gist_earth")

    candidate = PRESET_ALIASES.get(key, requested)
    if candidate in PRESETS and PRESETS[candidate] is not None:
        return PRESETS[candidate]

    try:
        return plt.get_cmap(candidate)
    except ValueError:
        pass

    colorcet_key = None
    if key.startswith("cc:"):
        colorcet_key = requested.split(":", 1)[1]
    elif key.startswith("cet_"):
        colorcet_key = requested

    if colorcet_key:
        try:
            if PRESETS.get("cet_l10") is None and "colorcet" not in globals():
                raise ImportError("colorcet no instalado")
            return plt.get_cmap(colorcet_key)
        except Exception as exc:
            log_warning(logger, f"Colorcet not available or palette load failed ({exc}). Falling back to gist_earth.")

    if key.startswith("gmt:"):
        cpt_name = requested.split(":", 1)[1].strip().lower() or "geo"
        gmt_alias_map = {
            "geo": "gist_earth",
            "earth": "terrain",
            "dem4": "terrain",
            "relief": "terrain",
            "bathy": "ocean",
            "bathymetry": "ocean",
            "polar": "coolwarm",
            "cubehelix": "cubehelix",
        }
        mapped = gmt_alias_map.get(cpt_name)
        if mapped:
            return plt.get_cmap(mapped)
        log_warning(logger, f"GMT/PyGMT palette alias '{cpt_name}' not recognized. Falling back to gist_earth.")

    log_warning(logger, f"Unknown colormap '{requested}'. Falling back to gist_earth.")
    return plt.get_cmap("gist_earth")
