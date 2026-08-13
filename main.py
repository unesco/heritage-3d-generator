#!/usr/bin/env python3
"""
🏛️ UNESCO Heritage Sites 3D Generator (VoxCity 1.6)

Usage:
    python main.py                              # Interactive mode
    python main.py test                         # Mont-Saint-Michel test
    python main.py whc:80                       # Site by key (whc:<id> / mab:<id>)
    python main.py 12                           # Site by catalog row number
    python main.py whc:274 --quality ultimate   # Specific quality preset
    python main.py --envimet whc:80             # Also export ENVI-MET files
    python main.py --list-quality               # List quality presets
    python main.py --quality-details premium    # Show preset details

Batch generation:  python batch.py --help
Catalog refresh:   python unesco_data.py
HF upload:         python upload_hf.py --help
"""

import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt

from pipeline import generate_site, load_sites
from quality_config import get_quality_manager

console = Console()


def print_header(quality: str):
    console.print(Panel(
        f"[bold blue]🏛️ UNESCO Heritage Sites 3D Generator[/bold blue]\n"
        f"[italic]Voxel 3D models of World Heritage & Biosphere sites[/italic]\n"
        f"[bold yellow]Quality: {quality.upper()}[/bold yellow]\n"
        f"[dim]Powered by Google Earth Engine + VoxCity 1.6[/dim]",
        title="[bold green]UNESCO 3D Heritage Modeling[/bold green]",
        border_style="blue"))


def interactive_site(df):
    """Simple interactive picker (paginated by programme)."""
    console.print(f"[green]✅ {len(df)} sites in catalog "
                  f"({(df.programme == 'WHC').sum()} WHC, {(df.programme == 'MAB').sum()} MAB)[/green]")
    console.print(df[["site_key", "name", "country", "category"]]
                  .head(30).to_string())
    console.print("[dim]… showing first 30; use `python main.py <site_key>` for any site[/dim]")
    row = IntPrompt.ask("Choose a row number", default=0)
    if 0 <= row < len(df):
        return df.iloc[row].to_dict()
    console.print("[red]❌ Invalid row number[/red]")
    return None


def resolve_site(arg: str, df):
    if arg == "test":
        match = df[df["name"].str.contains("Mont-Saint-Michel", na=False)]
        if match.empty:
            sys.exit("Mont-Saint-Michel not found in catalog")
        return match.iloc[0].to_dict()
    if arg.isdigit():
        idx = int(arg)
        if 0 <= idx < len(df):
            return df.iloc[idx].to_dict()
        sys.exit(f"Invalid row number: {idx} (catalog has {len(df)} rows)")
    match = df[df["site_key"] == arg]
    if match.empty:
        sys.exit(f"Unknown site key: {arg} — expected whc:<id> or mab:<id>")
    return match.iloc[0].to_dict()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("site", nargs="?",
                        help="Site key (whc:80 / mab:USYe1976), row number, or 'test'")
    parser.add_argument("--quality", default="premium",
                        choices=["preview", "standard", "premium", "ultimate"])
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--envimet", action="store_true",
                        help="Also export ENVI-MET files (off by default)")
    parser.add_argument("--list-quality", action="store_true")
    parser.add_argument("--quality-details",
                        choices=["preview", "standard", "premium", "ultimate"])
    return parser.parse_args()


def main():
    args = parse_arguments()
    manager = get_quality_manager()

    if args.list_quality:
        manager.list_presets()
        return
    if args.quality_details:
        manager.show_preset_details(args.quality_details)
        return

    print_header(args.quality)
    df = load_sites()

    site = resolve_site(args.site, df) if args.site else interactive_site(df)
    if site is None:
        return

    console.print(f"[bold]🗺️  {site['name']}[/bold] — {site['country']} "
                  f"({site['site_key']}, {site['category']}, "
                  f"{site['lat']:.4f}°, {site['lon']:.4f}°)")

    result = generate_site(site, preset_name=args.quality,
                           output_root=args.output_dir, envimet=args.envimet)

    if result["status"] in ("passed", "flagged"):
        console.print(Panel(
            f"[bold green]🎉 Model generated[/bold green]\n"
            f"Site: {site['name']}\n"
            f"Quality gate: {result['status']}\n"
            f"Output: {result['output_dir']}/\n"
            f"Elapsed: {result['elapsed_seconds']}s\n\n"
            f"[bold]View:[/bold] https://3dviewer.net/ (drag & drop model.obj) "
            f"or open the preview.png",
            title="[bold green]✅ Done[/bold green]", border_style="green"))
        if result["status"] == "flagged":
            for reason in result["quality"]["reasons"]:
                console.print(f"[yellow]⚠️  {reason}[/yellow]")
    else:
        console.print(f"[red]❌ Generation failed: {result.get('error')}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
