#!/usr/bin/env python3
"""
🏗️ Core generation pipeline (VoxCity 1.6 API).

Shared by main.py (single site) and batch.py (multi-site). One site in,
one directory out:

    output/<programme>/<id>_<slug>/
        model.obj / model.mtl   — 3D model
        preview.png             — visual quality check
        quality.json            — metrics + pass/flag/fail status
        metadata.json           — minimal site + provenance metadata
"""

import json
import os
import time
from datetime import datetime, timezone
from math import cos, radians
from pathlib import Path
from typing import List, Optional, Tuple

import ee
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from rich.console import Console

from voxcity.generator import get_voxcity
from voxcity.exporter.obj import export_obj

from quality_config import get_quality_manager
from quality_gate import run_quality_gate
from unesco_data import slugify

console = Console()

SITES_CSV = Path("data/sites.csv")

_ee_initialized = False


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

def load_sites() -> pd.DataFrame:
    """Load the normalized site catalog (run unesco_data.py first)."""
    if not SITES_CSV.exists():
        raise FileNotFoundError(
            f"{SITES_CSV} not found — run: poetry run python unesco_data.py")
    return pd.read_csv(SITES_CSV)


def find_site(site_key: str) -> Optional[dict]:
    """Find one site by key ('whc:80' / 'mab:USYe1976') in the catalog."""
    df = load_sites()
    match = df[df["site_key"] == site_key]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


# ---------------------------------------------------------------------------
# Geometry + Earth Engine
# ---------------------------------------------------------------------------

def create_rectangle_from_center(lat: float, lon: float,
                                 size_meters: int) -> List[Tuple[float, float]]:
    """Rectangle vertices (lon, lat) around a center point."""
    lat_offset = (size_meters / 2) / 111000
    lon_offset = (size_meters / 2) / (111000 * abs(cos(radians(lat))))
    return [
        (lon - lon_offset, lat - lat_offset),  # SW
        (lon - lon_offset, lat + lat_offset),  # NW
        (lon + lon_offset, lat + lat_offset),  # NE
        (lon + lon_offset, lat - lat_offset),  # SE
    ]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def _ee_init(project_id: str):
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["EE_PROJECT"] = project_id
    ee.Initialize(project=project_id)
    ee.Image("USGS/SRTMGL1_003").select("elevation").bandNames()  # test call


def initialize_earth_engine(project_id: Optional[str] = None):
    """Initialize EE once per process. Project id comes from EE_PROJECT_ID
    (.env / environment) — see .env.example."""
    global _ee_initialized
    if _ee_initialized:
        return
    load_dotenv()
    project_id = project_id or os.getenv("EE_PROJECT_ID")
    if not project_id:
        raise RuntimeError(
            "EE_PROJECT_ID is not set — copy .env.example to .env and set "
            "your Google Earth Engine project id")
    with console.status("[bold blue]🌍 Connecting to Google Earth Engine..."):
        _ee_init(project_id)
    _ee_initialized = True
    console.print(f"[green]✅ Earth Engine connected (project: {project_id})[/green]")


# ---------------------------------------------------------------------------
# Generation with fallback strategies
# ---------------------------------------------------------------------------

def _empty_building_gdf():
    """Empty building GeoDataFrame — skips voxcity's building download entirely
    (its downloaders crash on empty results, common for forests/deserts/jungle)."""
    import geopandas as gpd
    return gpd.GeoDataFrame({"height": [], "min_height": []},
                            geometry=gpd.GeoSeries([], crs="EPSG:4326"))


def build_fallback_strategies(config: dict) -> List[dict]:
    """Ordered fallback chain — auto/region-optimal first, then Overpass-free
    EE-only configs (empty-building-safe), then explicit OSM configs."""
    strategies = [
        # Auto-selects per region: EUBUCCO/MBFP/OpenBuildings, 1m canopy,
        # high-res national DEMs (France 1m, USGS 3DEP, ...), 10m height fill
        {"name": "Auto (region-optimal)",
         "building_source": None,
         "land_cover_source": None,
         "canopy_height_source": None,
         "dem_source": None},
        # Auto buildings/DEM/canopy but raster land cover (no Overpass land cover)
        {"name": "Auto + ESA WorldCover",
         "building_source": None,
         "land_cover_source": "ESA WorldCover",
         "canopy_height_source": None,
         "dem_source": None},
        # EE raster buildings (Africa/S+SE Asia/LatAm) — no Overpass at all
        {"name": "EE raster buildings + ESA WorldCover",
         "building_source": "Open Building 2.5D Temporal",
         "building_complementary_source": "None",
         "land_cover_source": "ESA WorldCover",
         "canopy_height_source": "ETH Global Sentinel-2 10m Canopy Height (2020)",
         "dem_source": "FABDEM"},
        # Same but COPERNICUS DEM — covers coastal zones where FABDEM has gaps
        {"name": "EE raster buildings + COPERNICUS DEM",
         "building_source": "Open Building 2.5D Temporal",
         "building_complementary_source": "None",
         "land_cover_source": "ESA WorldCover",
         "canopy_height_source": "ETH Global Sentinel-2 10m Canopy Height (2020)",
         "dem_source": "COPERNICUS"},
        # Overture vector footprints (downloaded by us, rasterized by voxcity —
        # bypasses the broken Overture source and Overpass alike)
        {"name": "Overture footprints + ESA WorldCover",
         "building_source": "OpenStreetMap",  # ignored: building_gdf provided
         "building_gdf": "overture",  # lazily downloaded if this strategy is reached
         "building_complementary_source": "None",
         "land_cover_source": "ESA WorldCover",
         "canopy_height_source": "ETH Global Sentinel-2 10m Canopy Height (2020)",
         "dem_source": "FABDEM"},
    ]
    # Empty-buildings config is only valid where buildings are legitimately
    # absent (biosphere reserves, natural sites) — the quality gate would
    # correctly reject a zero-building model for cultural sites anyway.
    if config.get("allow_empty_buildings"):
        strategies.append(
            {"name": "No buildings (EE-only)",
             "building_source": "OpenStreetMap",  # ignored: building_gdf provided
             "building_gdf": _empty_building_gdf(),
             "building_complementary_source": "None",
             "land_cover_source": "ESA WorldCover",
             "canopy_height_source": "ETH Global Sentinel-2 10m Canopy Height (2020)",
             "dem_source": "FABDEM"})
        strategies.append(
            {"name": "No buildings + COPERNICUS DEM",
             "building_source": "OpenStreetMap",  # ignored: building_gdf provided
             "building_gdf": _empty_building_gdf(),
             "building_complementary_source": "None",
             "land_cover_source": "ESA WorldCover",
             "canopy_height_source": "ETH Global Sentinel-2 10m Canopy Height (2020)",
             "dem_source": "COPERNICUS"})
    strategies += [
        {"name": "Explicit preset sources",
         "building_source": config["building_source"],
         "land_cover_source": config["land_cover_source"],
         "canopy_height_source": config["canopy_height_source"],
         "dem_source": config["dem_source"]},
        {"name": "ETH Canopy Data",
         "building_source": config["building_source"],
         "land_cover_source": config["land_cover_source"],
         "canopy_height_source": "ETH Global Sentinel-2 10m Canopy Height (2020)",
         "dem_source": config["dem_source"]},
        {"name": "OpenStreetMap Land Cover",
         "building_source": config["building_source"],
         "land_cover_source": "OpenStreetMap",
         "canopy_height_source": config["canopy_height_source"],
         "dem_source": config["dem_source"]},
        {"name": "ETH Canopy + OSM Land Cover",
         "building_source": config["building_source"],
         "land_cover_source": "OpenStreetMap",
         "canopy_height_source": "ETH Global Sentinel-2 10m Canopy Height (2020)",
         "dem_source": config["dem_source"]},
        {"name": "Basic OpenStreetMap Configuration",
         "building_source": "OpenStreetMap",
         "land_cover_source": "OpenStreetMap",
         "canopy_height_source": "ETH Global Sentinel-2 10m Canopy Height (2020)",
         "dem_source": "FABDEM"},
        {"name": "No Canopy Data",
         "building_source": config["building_source"],
         "land_cover_source": "OpenStreetMap",
         "canopy_height_source": None,
         "dem_source": config["dem_source"]},
        {"name": "Minimal Reliable Configuration",
         "building_source": "OpenStreetMap",
         "land_cover_source": "OpenStreetMap",
         "canopy_height_source": None,
         "dem_source": "FABDEM"},
    ]
    return strategies


def _overture_building_gdf(rectangle_vertices):
    """Download Overture building footprints for the bbox (used as a fallback
    when Overpass/OSM is unreachable — voxcity 1.6.2 can't voxelize its own
    Overture source, but rasterizing the GDF ourselves works)."""
    from overturemaps import core as _ov_core
    lons = [v[0] for v in rectangle_vertices]
    lats = [v[1] for v in rectangle_vertices]
    bbox = (min(lons), min(lats), max(lons), max(lats))
    gdf = _ov_core.geodataframe("building", bbox=bbox)
    if gdf is None or len(gdf) == 0:
        raise RuntimeError("Overture returned no buildings for this bbox")
    keep = [c for c in ("height", "min_height", "geometry") if c in gdf.columns]
    gdf = gdf[keep].copy()
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    # voxcity drops heightless footprints and complement_height is not reliably
    # forwarded — fill defaults ourselves (10m global median, ground-based).
    if "height" in gdf.columns:
        gdf["height"] = gdf["height"].fillna(10.0)
    else:
        gdf["height"] = 10.0
    if "min_height" in gdf.columns:
        gdf["min_height"] = gdf["min_height"].fillna(0.0)
    return gdf


def generate_with_fallbacks(rectangle_vertices, config: dict):
    """Try strategies in order. Returns (voxcity, strategy_name, strategy_index)."""
    strategies = build_fallback_strategies(config)
    kwargs = {"output_dir": config["output_dir"],
              "dem_interpolation": config["dem_interpolation"]}

    last_error = None
    for i, strategy in enumerate(strategies):
        try:
            building_gdf = strategy.get("building_gdf")
            run_kwargs = dict(kwargs)
            if building_gdf == "overture":  # lazy download, only if reached
                building_gdf = _overture_building_gdf(rectangle_vertices)
            if building_gdf is not None:
                # footprints without heights need a default, else they are dropped
                run_kwargs.setdefault("building_complement_height", 10.0)
            if i > 0:
                console.print(f"[blue]🔄 Trying {strategy['name']}...[/blue]")
            voxcity = get_voxcity(
                rectangle_vertices,
                config["mesh_size"],
                building_source=strategy["building_source"],
                land_cover_source=strategy["land_cover_source"],
                canopy_height_source=strategy["canopy_height_source"],
                dem_source=strategy["dem_source"],
                building_complementary_source=strategy.get("building_complementary_source"),
                building_gdf=building_gdf,
                **run_kwargs,
            )
            if i > 0:
                console.print(f"[green]✅ Success with {strategy['name']}[/green]")
            # A generation that "succeeds" but yields zero buildings is a
            # content failure for sites that must show structures — keep
            # walking the chain instead of letting the quality gate fail it.
            if not config.get("allow_empty_buildings"):
                # buildings appear as class 13 (footprint surface) and/or -3 (volume)
                cls = np.asarray(voxcity.voxels.classes)
                building_voxels = int(((cls == 13) | (cls == -3)).sum())
                if building_voxels == 0:
                    raise RuntimeError(
                        f"{strategy['name']}: zero building voxels for a "
                        "building-expected site — trying next strategy")
            # Same for terrain: a (near-)flat DEM means missing data
            # (e.g. FABDEM coastal gaps) — try the next strategy's DEM.
            # Threshold matches the quality gate's fail rule (rounds to 0.0).
            dem = np.asarray(voxcity.dem.elevation, dtype=float)
            dem_valid = dem[np.isfinite(dem)]
            if dem_valid.size == 0 or float(dem_valid.max() - dem_valid.min()) < 0.5:
                raise RuntimeError(
                    f"{strategy['name']}: flat/empty DEM — trying next strategy")
            return voxcity, strategy["name"], i
        except Exception as e:
            last_error = e
            console.print(f"[yellow]⚠️  {strategy['name']} failed: {e}[/yellow]")

    raise RuntimeError(f"All fallback strategies failed. Last error: {last_error}")


def _parse_mtl_colors(mtl_path: Path) -> dict:
    """material name -> (r, g, b) floats from Kd lines of an MTL file."""
    colors, name = {}, None
    with open(mtl_path, errors="ignore") as f:
        for line in f:
            if line.startswith("newmtl"):
                name = line.split(maxsplit=1)[1].strip()
            elif line.startswith("Kd") and name:
                r, g, b = (float(x) for x in line.split()[1:4])
                colors[name] = (r, g, b)
    return colors


def convert_to_glb(obj_path: Path) -> Optional[Path]:
    """Convert OBJ+MTL to a single binary GLB with per-class colors baked in
    as vertex colors (trimesh's default MTL->GLB material conversion loses
    the per-class colors, rendering models uniformly white)."""
    try:
        import trimesh
        obj_path = Path(obj_path)
        colors = _parse_mtl_colors(obj_path.with_suffix(".mtl"))
        scene = trimesh.load(str(obj_path), force="scene")
        out = trimesh.Scene()
        for name, mesh in scene.geometry.items():
            rgb = colors.get(name) or colors.get(name.split("|")[0])
            if rgb is not None and hasattr(mesh, "faces"):
                rgba = [int(round(255 * c)) for c in rgb] + [255]
                mesh.visual = trimesh.visual.ColorVisuals(
                    mesh, face_colors=np.tile(rgba, (len(mesh.faces), 1)))
            out.add_geometry(mesh, geom_name=name)
        # VoxCity OBJ is Z-up; glTF viewers expect Y-up — rotate -90° about X
        out.apply_transform(
            trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
        glb_path = obj_path.with_suffix(".glb")
        out.export(str(glb_path))
        console.print(f"[green]✅ GLB exported: {glb_path}[/green]")
        return glb_path
    except Exception as e:
        console.print(f"[yellow]⚠️  GLB conversion failed: {e}[/yellow]")
        return None


# ---------------------------------------------------------------------------
# Per-site pipeline
# ---------------------------------------------------------------------------

def site_output_dir(output_root: str, site: dict) -> Path:
    programme, sid = site["site_key"].split(":", 1)
    return Path(output_root) / programme.lower() / f"{sid}_{slugify(site['name'])}"


def get_config(preset_name: str, output_root: str) -> dict:
    preset = get_quality_manager().get_preset(preset_name)
    return {
        "preset_name": preset.name,
        "zone_size": preset.zone_size,
        "mesh_size": preset.mesh_size,
        "building_source": preset.building_source,
        "land_cover_source": preset.land_cover_source,
        "canopy_height_source": preset.canopy_height_source,
        "dem_source": preset.dem_source,
        "dem_interpolation": preset.dem_interpolation,
        "output_dir": output_root,
    }


def generate_site(site: dict, preset_name: str = "premium",
                  output_root: str = "output", envimet: bool = False) -> dict:
    """Full pipeline for one site. Returns a result dict (also written to disk)."""
    import voxcity as _voxcity_pkg

    config = get_config(preset_name, output_root)
    # Biosphere reserves and natural sites may legitimately have no buildings
    config["allow_empty_buildings"] = (
        site.get("programme") == "MAB" or site.get("category") == "Natural"
    )
    out_dir = site_output_dir(output_root, site)
    out_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    result = {
        "site_key": site["site_key"],
        "name": site["name"],
        "preset": config["preset_name"],
        "output_dir": str(out_dir),
        "status": "failed",
        "error": None,
    }

    try:
        initialize_earth_engine()

        rectangle = create_rectangle_from_center(
            float(site["lat"]), float(site["lon"]), config["zone_size"])

        console.print(f"[bold]🏗️  {site['name']}[/bold] "
                      f"({site['site_key']}, {config['preset_name']}, "
                      f"{config['zone_size']}m @ {config['mesh_size']}m)")
        voxcity, strategy_name, strategy_index = generate_with_fallbacks(rectangle, config)

        # OBJ export (deliverable)
        export_obj(voxcity, str(out_dir), "model")
        obj_path = out_dir / "model.obj"
        console.print(f"[green]✅ OBJ exported: {obj_path}[/green]")

        # GLB export (web-friendly single-file 3D model)
        convert_to_glb(obj_path)

        # Smooth hybrid GLB (no voxels: DEM terrain + LOD1 buildings)
        try:
            from smooth_export import export_smooth_glb
            export_smooth_glb(voxcity, out_dir / "model_smooth.glb")
        except Exception as e:
            console.print(f"[yellow]⚠️  Smooth GLB export failed: {e}[/yellow]")

        # ENVI-MET (opt-in)
        if envimet:
            try:
                from voxcity.exporter.envimet import export_inx
                export_inx(voxcity, output_directory=str(out_dir),
                           file_basename="model",
                           land_cover_source=config["land_cover_source"],
                           author_name="UNESCO Data & AI",
                           model_description=f"3D model of {site['name']}")
                console.print("[green]✅ ENVI-MET INX exported[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️  ENVI-MET export failed: {e}[/yellow]")

        # Quality gate
        report = run_quality_gate(voxcity, site, obj_path,
                                  strategy_name, strategy_index, out_dir)
        result["status"] = report["status"]
        result["quality"] = report

        # Sources actually used (recorded by voxcity, incl. auto-selection)
        selected = dict((voxcity.extras or {}).get("selected_sources", {}) or {})

        # Minimal metadata
        metadata = {
            "site_key": site["site_key"],
            "name": site["name"],
            "programme": site["programme"],
            "category": site["category"],
            "country": site["country"],
            "iso": site["iso"],
            "lat": float(site["lat"]),
            "lon": float(site["lon"]),
            "year": str(site.get("year", "")),
            "source_url": site["source_url"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": {
                "tool": "voxcity",
                "voxcity_version": getattr(_voxcity_pkg, "__version__", "unknown"),
                "preset": config["preset_name"],
                "zone_size_m": config["zone_size"],
                "mesh_size_m": config["mesh_size"],
                "strategy_used": strategy_name,
                "selected_sources": selected,
                "building_source": config["building_source"],
                "land_cover_source": config["land_cover_source"],
                "canopy_height_source": config["canopy_height_source"],
                "dem_source": config["dem_source"],
            },
            "quality_status": report["status"],
            "quality_metrics": report["metrics"],
        }
        with open(out_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    except Exception as e:
        result["error"] = str(e)
        console.print(f"[red]❌ {site['name']} failed: {e}[/red]")

    result["elapsed_seconds"] = round(time.time() - started, 1)
    return result
