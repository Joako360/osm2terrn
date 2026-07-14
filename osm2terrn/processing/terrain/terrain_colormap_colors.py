import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

try:
    import colorcet as cc  # type: ignore[reportMissingImports]
except ImportError:
    cc = None

try:
    import cmasher as cmr  # type: ignore[reportMissingImports]
except ImportError:
    cmr = None

try:
    import cmcrameri.cm as crameri  # type: ignore[reportMissingImports]
except ImportError:
    crameri = None

PHYSICAL_TERRAIN = [
    "midnightblue",
    "royalblue",
    "deepskyblue",
    "khaki",
    "yellowgreen",
    "forestgreen",
    "olivedrab",
    "peru",
    "sienna",
    "darkslategray",
    "lightgray",
    "snow",
]

ALPINE_TOP = [
    "darkolivegreen",
    "olivedrab",
    "peru",
    "sienna",
    "rosybrown",
    "lightgray",
    "snow",
]

DESERT = [
    "midnightblue",
    "steelblue",
    "wheat",
    "tan",
    "burlywood",
    "peru",
    "saddlebrown",
    "lightgray",
]


class TerrainColorMaps:

    @staticmethod
    def from_colors(colors, name="custom", N=1024):
        return LinearSegmentedColormap.from_list(name, colors, N=N)

    @staticmethod
    def mpl(name):
        return plt.get_cmap(name)

    @staticmethod
    def cet(name="CET_L10"):
        if cc is None:
            raise ImportError("colorcet no instalado")
        return cc.cm[name]

    @staticmethod
    def cmr(name="savanna"):
        if cmr is None:
            raise ImportError("cmasher no instalado")
        return getattr(cmr, name)

    @staticmethod
    def crameri_map(name="bukavu"):
        if crameri is None:
            raise ImportError("cmcrameri no instalado")
        return getattr(crameri, name)

    @staticmethod
    def combine(maps, positions=None, samples=2048, name="combined"):
        valid_maps = [m for m in maps if m is not None]
        if len(valid_maps) < 2:
            map_status = [
                (type(m).__name__ if m is not None else "None", m is None)
                for m in maps
            ]
            raise ValueError(
                "Need at least two valid colormaps to combine. "
                "Check optional libraries like colorcet, cmasher or cmcrameri. "
                f"Map status: {map_status}"
            )
        if positions is None or len(positions) != len(valid_maps):
            positions = np.linspace(0, 1, len(valid_maps))
        positions = np.asarray(positions)
        x = np.linspace(0, 1, samples)
        colors = np.zeros((samples, 3))
        for i in range(len(valid_maps) - 1):
            p0 = positions[i]
            p1 = positions[i + 1]
            mask = (x >= p0) & (x <= p1)
            local_x = (x[mask] - p0) / (p1 - p0)
            c0 = valid_maps[i](local_x)[..., :3]
            c1 = valid_maps[i + 1](local_x)[..., :3]
            alpha = local_x[:, None]
            colors[mask] = (1 - alpha) * c0 + alpha * c1
        return ListedColormap(colors, name=name)


PRESETS = {
    "physical": TerrainColorMaps.from_colors(PHYSICAL_TERRAIN),
    "physical_terrain": TerrainColorMaps.from_colors(PHYSICAL_TERRAIN),
    "alpine_top": TerrainColorMaps.from_colors(ALPINE_TOP),
    "desert": TerrainColorMaps.from_colors(DESERT),
    "cet_l10": TerrainColorMaps.cet("CET_L10") if cc else None,
    "cet_l11": TerrainColorMaps.cet("CET_L11") if cc else None,
    "cet_l12": TerrainColorMaps.cet("CET_L12") if cc else None,
    "terrain": TerrainColorMaps.mpl("terrain"),
    "gist_earth": TerrainColorMaps.mpl("gist_earth"),
    "savanna": TerrainColorMaps.cmr("savanna") if cmr else None,
    "rainforest": TerrainColorMaps.cmr("rainforest") if cmr else None,
    "bukavu": TerrainColorMaps.crameri_map("bukavu") if crameri else None,
    "oleron": TerrainColorMaps.crameri_map("oleron") if crameri else None,
}
