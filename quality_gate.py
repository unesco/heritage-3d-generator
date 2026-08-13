#!/usr/bin/env python3
"""
🎯 Quality gate for generated 3D heritage models.

A model that isn't good enough must not be published — this module computes
objective metrics from the VoxCity object + exported OBJ, applies pass/fail
rules, and renders a preview PNG for visual inspection.

Status values:
    passed  — primary data sources, plausible content  → eligible for upload
    flagged — degraded fallback sources or suspicious metrics → manual review
    failed  — degenerate output → never uploaded
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# VoxCity standard land cover / voxel class indices
BUILDING_VOXEL_CLASS = 13       # building footprint (surface)
BUILDING_VOLUME_CLASS = -3      # building volume (interior voxels below surface)
NO_DATA_CLASS = 14


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def obj_stats(obj_path: Path) -> dict:
    """Stream-count OBJ vertices/faces (files can be large)."""
    stats = {"obj_exists": False, "obj_size_bytes": 0,
             "obj_vertices": 0, "obj_faces": 0}
    obj_path = Path(obj_path)
    if not obj_path.exists():
        return stats
    stats["obj_exists"] = True
    stats["obj_size_bytes"] = obj_path.stat().st_size
    v = f = 0
    with open(obj_path, "r", errors="ignore") as fh:
        for line in fh:
            if line.startswith("v "):
                v += 1
            elif line.startswith("f "):
                f += 1
    stats["obj_vertices"] = v
    stats["obj_faces"] = f
    return stats


def voxel_metrics(voxcity) -> dict:
    """Content metrics from the VoxCity object grids."""
    cls = np.asarray(voxcity.voxels.classes)
    dem = np.asarray(voxcity.dem.elevation, dtype=float)

    building_mask = (cls == BUILDING_VOXEL_CLASS) | (cls == BUILDING_VOLUME_CLASS)
    building_voxels = int(building_mask.sum())
    building_columns = building_mask.any(axis=2)
    dem_valid = dem[np.isfinite(dem)]

    canopy = getattr(voxcity.tree_canopy, "top", None) if voxcity.tree_canopy else None
    canopy = np.asarray(canopy, dtype=float) if canopy is not None else None

    return {
        "grid_shape": list(cls.shape),
        "mesh_size_m": float(voxcity.voxels.meta.meshsize),
        "total_voxels": int(cls.size),
        "building_voxels": building_voxels,
        "building_coverage_pct": round(float(building_columns.mean()) * 100, 2),
        "canopy_coverage_pct": (round(float((canopy > 0).mean()) * 100, 2)
                                if canopy is not None else None),
        "dem_min_m": round(float(dem_valid.min()), 1) if dem_valid.size else None,
        "dem_max_m": round(float(dem_valid.max()), 1) if dem_valid.size else None,
        "dem_range_m": (round(float(dem_valid.max() - dem_valid.min()), 1)
                        if dem_valid.size else None),
    }


# ---------------------------------------------------------------------------
# Evaluation rules
# ---------------------------------------------------------------------------

def evaluate(metrics: dict, site: dict, strategy_index: int) -> Tuple[str, list]:
    """Apply pass/fail rules. Returns (status, reasons)."""
    reasons = []

    # --- hard failures -----------------------------------------------------
    if not metrics["obj_exists"] or metrics["obj_faces"] == 0:
        reasons.append("OBJ missing or degenerate (0 faces)")
        return "failed", reasons

    if metrics["dem_range_m"] is not None and metrics["dem_range_m"] == 0.0:
        reasons.append("DEM perfectly flat (0.0m range) — terrain data likely missing")
        return "failed", reasons

    expects_buildings = (
        site.get("programme") == "WHC" and site.get("category") in ("Cultural", "Mixed")
    )
    if expects_buildings and metrics["building_voxels"] == 0:
        reasons.append("Cultural/Mixed WHC site with zero building voxels — "
                       "building data missing for a site that must show structures")
        return "failed", reasons

    # --- soft flags ---------------------------------------------------------
    if strategy_index > 0:
        reasons.append(f"Degraded fallback strategy used (index {strategy_index})")

    if metrics["dem_range_m"] is not None and metrics["dem_range_m"] < 1.0:
        reasons.append(f"Suspiciously low DEM relief ({metrics['dem_range_m']}m)")

    if expects_buildings and metrics["building_coverage_pct"] < 0.1:
        reasons.append(f"Very low building coverage ({metrics['building_coverage_pct']}%) "
                       "for a Cultural/Mixed site — check OSM completeness")

    status = "flagged" if reasons else "passed"
    if not reasons:
        reasons.append("All quality checks passed")
    return status, reasons


# ---------------------------------------------------------------------------
# Preview rendering
# ---------------------------------------------------------------------------

def _max_pool(mask: np.ndarray, target: int = 64) -> np.ndarray:
    """Downsample a boolean voxel grid with max-pooling (keeps sparse buildings)."""
    strides = [max(1, int(np.ceil(d / target))) for d in mask.shape]
    out_shape = [int(np.ceil(d / s)) for d, s in zip(mask.shape, strides)]
    pooled = np.zeros(out_shape, dtype=bool)
    for i in range(out_shape[0]):
        for j in range(out_shape[1]):
            for k in range(out_shape[2]):
                if mask[i * strides[0]:(i + 1) * strides[0],
                        j * strides[1]:(j + 1) * strides[1],
                        k * strides[2]:(k + 1) * strides[2]].any():
                    pooled[i, j, k] = True
    return pooled


def render_preview(voxcity, out_png: Path, title: str = "") -> Optional[Path]:
    """3-panel preview: building heights, land cover, downsampled 3D voxels."""
    try:
        heights = np.asarray(voxcity.buildings.heights, dtype=float)
        heights = np.where(np.isfinite(heights), heights, 0)
        land = np.asarray(voxcity.land_cover.classes)
        cls = np.asarray(voxcity.voxels.classes)

        fig, axes = plt.subplots(1, 3, figsize=(21, 7))
        if title:
            fig.suptitle(title, fontsize=14, fontweight="bold")

        im0 = axes[0].imshow(heights, cmap="viridis")
        axes[0].set_title("Building heights (m)")
        fig.colorbar(im0, ax=axes[0], fraction=0.046)

        im1 = axes[1].imshow(land, cmap="tab20", vmin=0, vmax=NO_DATA_CLASS)
        axes[1].set_title("Land cover classes")
        fig.colorbar(im1, ax=axes[1], fraction=0.046)

        ax3 = fig.add_subplot(1, 3, 3, projection="3d")
        axes[2].set_visible(False)  # replace 2D axis with the 3D one
        occupied = (cls != 0) & (cls != NO_DATA_CLASS)
        pooled = _max_pool(occupied, target=48)
        bpool = _max_pool((cls == BUILDING_VOXEL_CLASS) | (cls == BUILDING_VOLUME_CLASS), target=48)
        rgba = np.zeros(pooled.shape + (4,))
        rgba[pooled & bpool] = (0.84, 0.15, 0.16, 1.0)   # buildings red
        rgba[pooled & ~bpool] = (0.12, 0.47, 0.71, 0.6)  # terrain/vegetation blue
        ax3.voxels(pooled, facecolors=rgba, edgecolor="none")
        ax3.set_title("Voxel model (downsampled)")
        ax3.view_init(elev=30, azim=45)
        ax3.set_box_aspect((pooled.shape[0], pooled.shape[1],
                            max(pooled.shape[2], 1)))

        fig.tight_layout()
        fig.savefig(out_png, dpi=110, bbox_inches="tight")
        plt.close(fig)
        return Path(out_png)
    except Exception as e:  # preview is nice-to-have, never block the pipeline
        print(f"⚠️  Preview render failed: {e}")
        plt.close("all")
        return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_quality_gate(voxcity, site: dict, obj_path: Path,
                     strategy_name: str, strategy_index: int,
                     out_dir: Path) -> dict:
    """Compute metrics, evaluate, write quality.json + preview.png."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics = {}
    metrics.update(obj_stats(obj_path))
    metrics.update(voxel_metrics(voxcity))
    metrics["strategy_used"] = strategy_name
    metrics["strategy_index"] = strategy_index

    status, reasons = evaluate(metrics, site, strategy_index)

    preview = render_preview(voxcity, out_dir / "preview.png",
                             title=f"{site.get('name', '')} ({site.get('site_key', '')})")

    report = {
        "site_key": site.get("site_key"),
        "status": status,
        "reasons": reasons,
        "metrics": metrics,
        "preview_png": str(preview) if preview else None,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(out_dir / "quality.json", "w") as f:
        json.dump(report, f, indent=2)
    return report
