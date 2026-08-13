#!/usr/bin/env python3
"""
🔁 Regenerate only model_smooth.glb for completed sites.

Useful after improving smooth_export.py — re-generates the VoxCity model
(download cache makes this fast) and re-exports just the smooth GLB,
leaving OBJ/GLB/quality.json untouched.

Usage:
    python regen_smooth.py --pilot      # all pilot sites with a quality.json
    python regen_smooth.py --sites whc:80 mab:GRMo1981
"""

import argparse
from pathlib import Path

from rich.console import Console

from batch import PILOT_SITES
from pipeline import (create_rectangle_from_center, find_site,
                      generate_with_fallbacks, get_config,
                      initialize_earth_engine, site_output_dir)
from smooth_export import export_smooth_glb

console = Console()


def regen(site_key: str, output_root: str, quality: str) -> bool:
    site = find_site(site_key)
    if site is None:
        console.print(f"[red]❌ Unknown site: {site_key}[/red]")
        return False
    out_dir = site_output_dir(output_root, site)
    if not (out_dir / "quality.json").exists():
        console.print(f"[dim]⏭️  {site['name']} — no completed model, skipping[/dim]")
        return False

    config = get_config(quality, output_root)
    rect = create_rectangle_from_center(float(site["lat"]), float(site["lon"]),
                                        config["zone_size"])
    try:
        voxcity, strategy, _ = generate_with_fallbacks(rect, config)
        glb = export_smooth_glb(voxcity, out_dir / "model_smooth.glb")
        return glb is not None
    except Exception as e:
        console.print(f"[red]❌ {site['name']}: {e}[/red]")
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--sites", nargs="+")
    parser.add_argument("--quality", default="premium")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    keys = PILOT_SITES if args.pilot else (args.sites or [])
    if not keys:
        parser.error("Specify --pilot or --sites")

    initialize_earth_engine()
    ok = sum(regen(k, args.output_dir, args.quality) for k in keys)
    console.print(f"[bold]✅ {ok}/{len(keys)} smooth GLBs regenerated[/bold]")


if __name__ == "__main__":
    main()
