#!/usr/bin/env python3
"""
🏙️ Smooth hybrid GLB export — an alternative to the voxel ("Minecraft") OBJ.

Built from the same VoxCity model, but without cubes:
  - terrain: triangulated DEM surface, vertex-colored by land cover class
  - buildings: LOD1 extrusions of the original vector footprints (sharp walls,
    flat roofs) — not voxelized single-height stacks
  - everything assembled Y-up for glTF viewers

Output: model_smooth.glb next to the voxel exports.
"""

from pathlib import Path
from typing import Optional

import numpy as np
import trimesh
from shapely.geometry import Polygon

from voxcity.visualizer import get_voxel_color_map
from voxcity.utils.projector import GridProjector

DEFAULT_BUILDING_HEIGHT_M = 10.0
BUILDING_RGBA = [205, 205, 210, 255]  # light neutral gray


def _palette() -> dict:
    """VoxCity class index -> RGBA (0-255)."""
    pal = {}
    for k, v in get_voxel_color_map().items():
        pal[int(k)] = (list(v) + [255])[:4]
    return pal


def _terrain_mesh(dem: np.ndarray, land_cover: np.ndarray, meshsize: float,
                  palette: dict, stride: int = 1) -> trimesh.Trimesh:
    """Triangulated DEM surface, vertex-colored by land cover class."""
    d = dem[::stride, ::stride].astype(float)
    lc = land_cover[::stride, ::stride]
    if not np.isfinite(d).all():
        d = np.where(np.isfinite(d), d, np.nanmin(d[np.isfinite(d)]))
    ni, nj = d.shape
    east, north = np.meshgrid(np.arange(nj) * meshsize * stride,
                              np.arange(ni) * meshsize * stride)
    verts = np.column_stack([east.ravel(), north.ravel(), d.ravel()])

    a = np.arange((ni - 1) * (nj - 1))
    i, j = divmod(a, nj - 1)
    v0 = i * nj + j
    v1 = v0 + 1
    v2 = v0 + nj
    v3 = v2 + 1
    faces = np.empty((len(a) * 2, 3), dtype=np.int64)
    faces[0::2] = np.column_stack([v0, v2, v1])
    faces[1::2] = np.column_stack([v1, v2, v3])

    fallback = [190, 190, 190, 255]
    vcolors = np.array([palette.get(int(c), fallback) for c in lc.ravel()],
                       dtype=np.uint8)
    return trimesh.Trimesh(vertices=verts, faces=faces,
                           vertex_colors=vcolors, process=False)


def _building_meshes(voxcity, palette: dict,
                     default_height: float = DEFAULT_BUILDING_HEIGHT_M) -> list:
    """LOD1 prisms from the original vector building footprints."""
    gdf = (voxcity.extras or {}).get("building_gdf")
    if gdf is None or len(gdf) == 0:
        return []

    projector = GridProjector.from_city(voxcity)
    dem = np.asarray(voxcity.dem.elevation, dtype=float)
    ms = float(voxcity.voxels.meta.meshsize)
    ni, nj = dem.shape

    meshes = []
    for _, row in gdf.iterrows():
        geom = getattr(row, "geometry", None)
        if geom is None or geom.is_empty:
            continue
        h = row.get("height") if hasattr(row, "get") else None
        try:
            h = float(h)
        except (TypeError, ValueError):
            h = np.nan
        if not np.isfinite(h) or h <= 0:
            h = default_height

        polys = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
        for poly in polys:
            if getattr(poly, "geom_type", None) != "Polygon":
                continue
            lon, lat = poly.exterior.coords.xy
            ci, cj = projector.lon_lat_to_cell(np.asarray(lon), np.asarray(lat))
            east, north = np.asarray(cj) * ms, np.asarray(ci) * ms
            if east.max() < 0 or north.max() < 0 or \
               east.min() > nj * ms or north.min() > ni * ms:
                continue  # footprint fully outside the grid
            # base elevation = DEM at footprint centroid
            bi = int(np.clip(np.nanmean(ci), 0, ni - 1))
            bj = int(np.clip(np.nanmean(cj), 0, nj - 1))
            base = dem[bi, bj]
            if not np.isfinite(base):
                base = 0.0
            try:
                prism = trimesh.creation.extrude_polygon(
                    Polygon(zip(east, north)), height=h)
            except Exception:
                continue  # degenerate footprint
            prism.apply_translation([0, 0, base])
            prism.visual = trimesh.visual.ColorVisuals(
                prism, face_colors=np.tile(BUILDING_RGBA, (len(prism.faces), 1)))
            meshes.append(prism)
    return meshes


def export_smooth_glb(voxcity, out_path, terrain_stride: int = 1) -> Optional[Path]:
    """Assemble terrain + LOD1 buildings into a Y-up GLB (no voxels)."""
    try:
        dem = np.asarray(voxcity.dem.elevation, dtype=float)
        land_cover = np.asarray(voxcity.land_cover.classes)
        ms = float(voxcity.voxels.meta.meshsize)
        palette = _palette()

        # The voxel grid has better water detection (coastline processing) than
        # the raw land cover grid — let it win for water cells.
        WATER_CLASS = 9
        vox = np.asarray(voxcity.voxels.classes)
        if vox.shape[:2] == land_cover.shape:
            land_cover = np.where((vox == WATER_CLASS).any(axis=2),
                                  WATER_CLASS, land_cover)

        scene = trimesh.Scene()
        scene.add_geometry(_terrain_mesh(dem, land_cover, ms, palette,
                                         stride=terrain_stride),
                           geom_name="terrain")
        buildings = _building_meshes(voxcity, palette)
        for k, m in enumerate(buildings):
            scene.add_geometry(m, geom_name=f"building_{k}")

        # Z-up assembly -> Y-up glTF
        scene.apply_transform(
            trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
        out_path = Path(out_path)
        scene.export(str(out_path))
        print(f"✅ Smooth GLB exported: {out_path} "
              f"({len(buildings)} buildings, stride={terrain_stride})")
        return out_path
    except Exception as e:
        print(f"⚠️  Smooth GLB export failed: {e}")
        return None
