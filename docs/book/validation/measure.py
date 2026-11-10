"""Measure artifacts of a validation run (read-only). Usage: measure.py run1"""
from __future__ import annotations

import pickle
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
BASE = REPO / "output" / "validation" / "sf_telegraph_hill"
run = sys.argv[1] if len(sys.argv) > 1 else "run1"
out = BASE / "out" / run

print("== Elevation raster cache entries")
for f in sorted((BASE / "cache" / "providers" / "elevation" / "raster").glob("*.bin")):
    obj = pickle.loads(f.read_bytes())
    value = obj[0] if isinstance(obj, tuple) and len(obj) == 2 and isinstance(obj[1], dict) else obj
    arr, tr, mx, mn = value
    h, w = arr.shape
    west, north = tr * (0, 0)
    east, south = tr * (w, h)
    print(f"{f.name[:10]} shape={arr.shape} nan={int(np.isnan(arr).sum())} min={np.nanmin(arr):.1f} max={np.nanmax(arr):.1f} "
          f"bounds(w,s,e,n)=({west:.5f},{south:.5f},{east:.5f},{north:.5f}) pixel=({tr.a:.6f},{tr.e:.6f}) first_row_mean={np.nanmean(arr[0]):.1f} last_row_mean={np.nanmean(arr[-1]):.1f}")

print("== OSM bundle")
for f in (BASE / "cache" / "providers" / "osm" / "bbox-bundle").glob("*.bin"):
    obj = pickle.loads(f.read_bytes())
    d = obj[0] if isinstance(obj, tuple) and len(obj) == 2 and isinstance(obj[1], dict) else obj
    print("keys:", sorted(d))
    print("bounds:", d["bounds"])
    r = d["roads"]
    g = r.graph
    xs = [n["x"] for _, n in g.nodes(data=True)]
    ys = [n["y"] for _, n in g.nodes(data=True)]
    print(f"roads status={r.status} crs={r.graph_crs} nodes={g.number_of_nodes()} edges={g.number_of_edges()}")
    print(f"roads local extent x=[{min(xs):.1f},{max(xs):.1f}] y=[{min(ys):.1f},{max(ys):.1f}]")
    for k, v in d.items():
        if k in ("bounds", "roads", "rails"):
            continue
        if hasattr(v, "shape"):
            print(f"{k}: rows={len(v)} crs={getattr(v, 'crs', None)} total_bounds={[round(x, 1) for x in v.total_bounds]}")
        else:
            print(f"{k}: {type(v).__name__} {v if not hasattr(v, '__len__') else len(v)}")
    rails = d.get("rails")
    print("rails:", None if rails is None else (rails.number_of_nodes(), rails.number_of_edges()))

print("== Images")
for name in ("heightmap", "groundmap"):
    p = out / f"Telegraph Hill SF validation_{name}.png"
    im = Image.open(p)
    a = np.array(im)
    print(f"{name}: mode={im.mode} size={im.size} dtype={a.dtype} min={a.min()} max={a.max()} mean={a.mean():.1f} unique={len(np.unique(a))}")
    if name == "heightmap":
        g = a if a.ndim == 2 else a[..., 0]
        print(f"  mean rows top/bottom: {g[:8].mean():.1f}/{g[-8:].mean():.1f}; cols left/right: {g[:, :8].mean():.1f}/{g[:, -8:].mean():.1f}")
        print(f"  square={g.shape[0] == g.shape[1]} pow2+1={g.shape[0] - 1 & g.shape[0] - 2 == 0}")

print("== Text artifacts")
for p in sorted(out.glob("*.otc")) + sorted(out.glob("*.terrn2")):
    print(f"--- {p.name}\n{p.read_text(encoding='utf-8', errors='replace')}")
tobj = next(out.glob("*.tobj"))
text = tobj.read_text(encoding="utf-8", errors="replace")
print(f"--- {tobj.name}: {len(text.splitlines())} lines; head:\n" + "\n".join(text.splitlines()[:6]))
roads_tobj = REPO / "osm2terrn" / "output" / "Telegraph Hill SF validation_roads.tobj"
rt = roads_tobj.read_text(encoding="utf-8", errors="replace")
print(f"--- {roads_tobj.name} lines={len(rt.splitlines())}; head:\n" + "\n".join(rt.splitlines()[:8]))
nums = [tuple(map(float, m)) for m in re.findall(r"^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)", rt, re.M)]
if nums:
    arr = np.array(nums)
    print(f"roads tobj numeric triples={len(arr)} x=[{arr[:,0].min():.1f},{arr[:,0].max():.1f}] y=[{arr[:,1].min():.1f},{arr[:,1].max():.1f}] z=[{arr[:,2].min():.1f},{arr[:,2].max():.1f}]")
print("terrn2 references roads tobj:", "roads" in (next(out.glob('*.terrn2'))).read_text(encoding="utf-8", errors="replace").lower())
