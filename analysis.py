#!/usr/bin/env python3
"""
☀️ Analysis layers for generated heritage models (the "useful" renders).

Per site, computes on the voxel model:
  - Green View Index (GVI)  — vegetation visibility from pedestrian level
  - Sky View Index (SVI)    — sky openness from pedestrian level
  - Solar irradiance        — instantaneous (solstice noon) + daily cumulative
                              (kWh/m²), using the nearest EPW weather file

All layers are best-effort: failures are logged, never fatal to the pipeline.
Outputs are PNG maps (+ raw numpy grids as .npz for reuse) in the site dir.
"""

from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SOLSTICE = {"calc_time": "06-21 12:00:00"}  # summer solstice noon
SOLSTICE_DAY = {"start_time": "06-21 05:00:00", "end_time": "06-21 21:00:00"}


def _save_npz(out_dir: Path, name: str, grid) -> Path:
    path = out_dir / f"{name}.npz"
    np.savez_compressed(path, grid=np.asarray(grid))
    return path


def _save_png(out_dir: Path, name: str, grid, title: str, cbar_label: str,
              cmap: str, vmin=None, vmax=None) -> Path:
    """Render an analysis grid as a color-mapped PNG with colorbar."""
    g = np.asarray(grid, dtype=float)
    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(g, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel("east →")
    ax.set_ylabel("← south")
    fig.colorbar(im, ax=ax, fraction=0.046, label=cbar_label)
    path = out_dir / f"{name}.png"
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return path


def compute_view_indices(voxcity, out_dir: Path) -> dict:
    """GVI + SVI maps. Returns {layer: png_path}."""
    from voxcity.simulator.view import get_view_index
    out = {}
    for mode, cmap, extra in (
        ("green", "viridis", {}),
        ("sky", "BuPu_r", {"elevation_min_degrees": 0}),
    ):
        try:
            kwargs = {
                "view_point_height": 1.5,
                "colormap": cmap,
                "obj_export": False,
                "output_directory": str(out_dir),
                "output_file_name": mode,
                **extra,
            }
            grid = get_view_index(voxcity, mode=mode, **kwargs)
            _save_npz(out_dir, f"{mode}_index", grid)
            png = _save_png(out_dir, f"{mode}_index", grid,
                            title=f"{'Green' if mode == 'green' else 'Sky'} View Index",
                            cbar_label="index (0-1)", cmap=cmap, vmin=0, vmax=1)
            out[f"{mode}_view_index"] = str(png)
            print(f"✅ {mode.upper()} computed")
        except Exception as e:
            print(f"⚠️  {mode.upper()} failed: {e}")
    return out


def compute_solar(voxcity, out_dir: Path) -> dict:
    """Instantaneous (solstice noon) + daily cumulative solar irradiance."""
    from voxcity.simulator.solar import get_global_solar_irradiance_using_epw
    out = {}
    base_kwargs = {
        "download_nearest_epw": True,
        "view_point_height": 1.5,
        "tree_k": 0.6,
        "tree_lad": 1.0,
        "obj_export": False,
        "output_directory": str(out_dir),
    }
    for name, calc_type, extra, title, unit in (
        ("solar_solstice_noon", "instantaneous", SOLSTICE,
         "Solar irradiance — Jun 21 12:00", "W/m²"),
        ("solar_solstice_day", "cumulative", SOLSTICE_DAY,
         "Cumulative solar irradiance — Jun 21", "Wh/m²·day"),
    ):
        try:
            grid = get_global_solar_irradiance_using_epw(
                voxcity, calc_type=calc_type,
                output_file_name=name, **base_kwargs, **extra)
            _save_npz(out_dir, name, grid)
            png = _save_png(out_dir, name, grid, title=title,
                            cbar_label=unit, cmap="magma", vmin=0)
            out[name] = str(png)
            print(f"✅ {name} computed")
        except Exception as e:
            print(f"⚠️  {name} failed: {e}")
    return out


def run_analysis(voxcity, out_dir, site: Optional[dict] = None,
                 solar: bool = True, view: bool = True) -> dict:
    """Compute all analysis layers. Returns {layer: path or None}."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {}
    if view:
        artifacts.update(compute_view_indices(voxcity, out_dir))
    if solar:
        artifacts.update(compute_solar(voxcity, out_dir))
    return artifacts
