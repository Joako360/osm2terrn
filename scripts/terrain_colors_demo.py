"""
terrain_pipeline.py

Pipeline modular para mapas físicos de elevación.

Compatible con:
- Matplotlib
- ColorCET
- CMasher
- cualquier colormap matplotlib-compatible

Instalación recomendada:

pip install matplotlib colorcet cmasher cmcrameri
"""

import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "src",
        )
    ),
)

import numpy as np
import matplotlib.pyplot as plt

from processing.terrain_colormap import (
    BaseMap,
    BlendMap,
    HeightTint,
    HeightWarp,
    PRESETS,
    TerrainColorMaps,
    TerrainPipeline,
)

if __name__ == "__main__":
    x = np.linspace(-3, 3, 1000)
    y = np.linspace(-3, 3, 1000)

    X, Y = np.meshgrid(x, y)

    dem = (
        np.sin(X * 2) *
        np.cos(Y * 2)
        +
        np.exp(-(X**2 + Y**2))
    )

    combined = TerrainColorMaps.combine(
        [
            PRESETS["physical"],
            PRESETS["terrain"],
            PRESETS["gist_earth"],
        ],
        positions=[0.0, 0.35, 1.0],
        name="hybrid_terrain",
    )

    pipeline = TerrainPipeline([
        HeightWarp(gamma=0.85),
        BaseMap(combined),
        BlendMap(
            PRESETS["gist_earth"],
            low=0.65,
            high=1.0,
            strength=0.35,
        ),
        HeightTint(
            low_color="darkseagreen",
            high_color="snow",
            strength=0.12,
        ),
    ])

    rgb = pipeline.render(dem)
    if rgb is None:
        raise ValueError("Pipeline failed to render RGB data.")

    plt.figure(figsize=(12, 10))
    plt.imshow(rgb)
    plt.axis("off")
    plt.title("Hybrid Physical Terrain")
    plt.show()
