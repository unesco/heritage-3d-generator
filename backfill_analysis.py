#!/usr/bin/env python3
"""
☀️ Backfill analysis layers (solar, GVI, SVI) for already-generated sites.

Regenerates the VoxCity model (fast via download cache) and computes only the
analysis artifacts — OBJ/GLB/quality outputs are untouched.

Usage:
    python backfill_analysis.py --pilot
    python backfill_analysis.py --sites whc:80 mab:GRMo1981
"""

import argparse

from rich.console import Console

from batch import PILOT_SITES
from pipeline import (create_rectangle_from_center, find_site,
                      generate_with_fallbacks, get_config,
                      initialize_earth_engine, site_output_dir)
from analysis import run_analysis

console = Console()


def backfill(site_key: str, output_root: str, quality: str) -> bool:
    site = find_site(site_key)
    if site is None:
        console.print(f"[red]❌ Unknown site: {site_key}[/red]")
        return False
    out_dir = site_output_dir(output_root, site)
    if not (out_dir / "quality.json").exists():
        console.print(f"[dim]⏭️  {site['name']} — no completed model, skipping[/dim]")
        return False

    console.print(f"\n[bold]▶ {site['name']}[/bold]")
    config = get_config(quality, output_root)
    config["allow_empty_buildings"] = (
        site.get("programme") == "MAB" or site.get("category") == "Natural")
    rect = create_rectangle_from_center(float(site["lat"]), float(site["lon"]),
                                        config["zone_size"])
    try:
        voxcity, strategy, _ = generate_with_fallbacks(rect, config)
        artifacts = run_analysis(voxcity, out_dir, site)
        ok = sum(1 for v in artifacts.values() if v)
        console.print(f"[green]✅ {ok}/{len(artifacts)} analysis layers[/green]")
        return ok > 0
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
    ok = sum(backfill(k, args.output_dir, args.quality) for k in keys)
    console.print(f"[bold]✅ {ok}/{len(keys)} sites got analysis layers[/bold]")


if __name__ == "__main__":
    main()
