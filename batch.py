#!/usr/bin/env python3
"""
📦 Batch runner for the UNESCO heritage 3D pipeline.

Usage:
    python batch.py --pilot                     # 10-site pilot (5 WHC + 5 MAB)
    python batch.py --sites whc:80 mab:USYe1976 # specific sites
    python batch.py --all --limit 50            # first N of full catalog
    python batch.py --pilot --quality standard  # override quality preset

Resume-safe: sites whose quality.json already reports "passed" are skipped.
Every attempt is appended to output/batch_status.jsonl.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

from pipeline import generate_site, load_sites, site_output_dir

console = Console()

STATUS_FILE = Path("output/batch_status.jsonl")

# Pilot: 5 iconic WHC sites + 5 Biosphere Reserves across regions
PILOT_SITES = [
    "whc:80",        # Mont-Saint-Michel and its Bay, France
    "whc:274",       # Historic Sanctuary of Machu Picchu, Peru (Mixed)
    "whc:326",       # Petra, Jordan
    "whc:668",       # Angkor, Cambodia
    "whc:252",       # Taj Mahal, India
    "mab:USYe1976",  # Yellowstone - Grand Teton, USA
    "mab:MXSi1986",  # Sian Ka'an, Mexico
    "mab:TZSe1981",  # Serengeti-Ngorongoro, Tanzania
    "mab:FRFo1998",  # Fontainebleau et du Gâtinais, France
    "mab:GRMo1981",  # Mount Olympus, Greece
]


def already_passed(site: dict, output_root: str, preset_name: str) -> bool:
    """Skip only sites that passed at the SAME quality preset."""
    site_dir = site_output_dir(output_root, site)
    qj = site_dir / "quality.json"
    mj = site_dir / "metadata.json"
    if not qj.exists() or not mj.exists():
        return False
    try:
        if json.loads(qj.read_text()).get("status") != "passed":
            return False
        preset = (json.loads(mj.read_text())
                  .get("generator", {}).get("preset", ""))
        return preset.lower() == preset_name.lower()
    except json.JSONDecodeError:
        return False


def append_status(result: dict):
    STATUS_FILE.parent.mkdir(exist_ok=True)
    entry = {k: v for k, v in result.items() if k != "quality"}
    entry["quality_status"] = (result.get("quality") or {}).get("status")
    entry["ts"] = datetime.now(timezone.utc).isoformat()
    with open(STATUS_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def resolve_sites(args) -> list:
    df = load_sites()
    if args.pilot:
        keys = PILOT_SITES
    elif args.sites:
        keys = args.sites
    elif args.all:
        keys = df["site_key"].tolist()
    else:
        sys.exit("Specify --pilot, --sites ..., or --all")

    sites, missing = [], []
    for key in keys:
        match = df[df["site_key"] == key]
        if match.empty:
            missing.append(key)
        else:
            sites.append(match.iloc[0].to_dict())
    for key in missing:
        console.print(f"[red]❌ Unknown site_key: {key}[/red]")
    if args.limit:
        sites = sites[: args.limit]
    return sites


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pilot", action="store_true", help="Run the 10-site pilot")
    parser.add_argument("--sites", nargs="+", help="Site keys (whc:80 mab:USYe1976 ...)")
    parser.add_argument("--all", action="store_true", help="Full catalog")
    parser.add_argument("--limit", type=int, help="Max number of sites")
    parser.add_argument("--quality", default="premium",
                        choices=["preview", "standard", "premium", "ultimate"],
                        help="Quality preset (default: premium)")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--envimet", action="store_true", help="Also export ENVI-MET")
    args = parser.parse_args()

    sites = resolve_sites(args)
    console.print(f"[bold cyan]📦 Batch: {len(sites)} sites, "
                  f"quality={args.quality}[/bold cyan]")

    results = []
    for i, site in enumerate(sites, 1):
        if already_passed(site, args.output_dir, args.quality):
            console.print(f"[dim]⏭️  [{i}/{len(sites)}] {site['name']} — already passed, skipping[/dim]")
            continue
        console.print(f"\n[bold]▶ [{i}/{len(sites)}] {site['name']}[/bold]")
        result = generate_site(site, preset_name=args.quality,
                               output_root=args.output_dir, envimet=args.envimet)
        append_status(result)
        results.append(result)

    # Summary
    table = Table(title="Batch summary")
    table.add_column("Site", style="cyan")
    table.add_column("Status")
    table.add_column("Strategy", style="dim")
    table.add_column("Time", justify="right")
    counts = {"passed": 0, "flagged": 0, "failed": 0}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        style = {"passed": "green", "flagged": "yellow", "failed": "red"}.get(r["status"], "")
        table.add_row(r["name"][:45], f"[{style}]{r['status']}[/{style}]",
                      (r.get("quality") or {}).get("metrics", {}).get("strategy_used", "-"),
                      f"{r['elapsed_seconds']:.0f}s")
    console.print(table)
    console.print(f"[bold]✅ {counts.get('passed', 0)} passed · "
                  f"⚠️  {counts.get('flagged', 0)} flagged · "
                  f"❌ {counts.get('failed', 0)} failed[/bold]")
    console.print(f"Status log: {STATUS_FILE}")

    if counts.get("failed"):
        sys.exit(1)


if __name__ == "__main__":
    main()
