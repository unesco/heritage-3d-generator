#!/usr/bin/env python3
"""
🤗 Publish quality-passed 3D models to a Hugging Face dataset.

Usage:
    export HF_TOKEN=hf_...                 # token with write access
    python upload_hf.py                    # upload all passed sites
    python upload_hf.py --include-flagged  # also upload flagged sites
    python upload_hf.py --dry-run          # show what would be uploaded
    python upload_hf.py --repo you/heritage-3d-models   # override target repo

Target repo: --repo flag or HF_DATASET_REPO env var.
Repo layout:
    whc/<id>_<slug>/{model.obj, model.mtl, model.glb, model_smooth.glb,
                     preview.png, solar_solstice_noon/day.png/.npz,
                     green_index.png/.npz, sky_index.png/.npz,
                     metadata.json, quality.json}
    mab/<id>_<slug>/...
    metadata.jsonl   # one record per uploaded site
    README.md        # dataset card
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi

DEFAULT_REPO = os.environ.get("HF_DATASET_REPO", "your-username/heritage-3d-models")
OUTPUT_ROOT = Path("output")

UPLOAD_SUFFIXES = {".obj", ".mtl", ".glb", ".png", ".json", ".npz"}


def collect_sites(include_flagged: bool, preset: str = None) -> list:
    """Scan output/ for site dirs with a passing quality.json (optionally preset-filtered)."""
    wanted = {"passed"} | ({"flagged"} if include_flagged else set())
    sites = []
    for qj in sorted(OUTPUT_ROOT.glob("*/*/quality.json")):
        try:
            quality = json.loads(qj.read_text())
        except json.JSONDecodeError:
            continue
        if quality.get("status") not in wanted:
            continue
        site_dir = qj.parent
        metadata_path = site_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        metadata = json.loads(metadata_path.read_text())
        if preset and metadata.get("generator", {}).get("preset", "").lower() != preset.lower():
            continue
        sites.append({
            "dir": site_dir,
            "programme": site_dir.parent.name,  # whc / mab
            "metadata": metadata,
            "quality": quality,
        })
    return sites


def build_metadata_jsonl(sites: list) -> str:
    lines = []
    for s in sites:
        m = dict(s["metadata"])
        m["hf_path"] = f"{s['programme']}/{s['dir'].name}/"
        lines.append(json.dumps(m, ensure_ascii=False))
    return "\n".join(lines) + "\n"


def build_readme(sites: list) -> str:
    n_whc = sum(1 for s in sites if s["programme"] == "whc")
    n_mab = sum(1 for s in sites if s["programme"] == "mab")
    status_icon = {"passed": "✅", "flagged": "⚠️", "failed": "❌"}
    rows = "\n".join(
        f"| `{s['metadata']['site_key']}` | {s['metadata']['name']} | "
        f"{s['metadata']['country']} | {s['metadata']['category']} | "
        f"{status_icon.get(s['quality']['status'], '❔')} {s['quality']['status']} |"
        for s in sites
    )
    return f"""---
license: cc-by-sa-4.0
tags:
  - unesco
  - world-heritage
  - biosphere-reserve
  - 3d-models
  - voxel
  - voxcity
  - solar-irradiance
  - green-view-index
  - sky-view-index
  - digital-twin
pretty_name: UNESCO Heritage 3D Models
---

# 🏛️ UNESCO Heritage 3D Models

> **3D digital twins of UNESCO World Heritage Sites & Biosphere Reserves** —
> quality-gated voxel models with environmental analysis layers, generated
> from open geospatial data with [VoxCity](https://github.com/kunifujiwara/VoxCity).

🌍 **{n_whc} World Heritage sites** · 🌿 **{n_mab} Biosphere Reserves** · ✅ **automated quality gate**

## 📦 What's inside

Each site ships as a folder under `whc/` or `mab/`:

```
<programme>/<id>_<slug>/
├── model.obj / model.mtl        # 🧱 voxel geometry (original)
├── model.glb                    # 🌐 web-friendly voxel (Y-up, colored)
├── model_smooth.glb             # 🏙️ smooth hybrid: DEM terrain + LOD1 buildings
├── preview.png                  # 👁️ 3D render for quick inspection
├── solar_solstice_noon.png/.npz # ☀️ instantaneous irradiance, Jun 21 12:00 (W/m²)
├── solar_solstice_day.png/.npz  # 📆 cumulative irradiance, Jun 21 day (Wh/m²·day)
├── green_index.png/.npz         # 🌳 Green View Index at pedestrian level (0–1)
├── sky_index.png/.npz           # 🌤️ Sky View Index at pedestrian level (0–1)
├── metadata.json                # 📋 provenance + generation config
└── quality.json                 # 🎯 quality-gate metrics + status
```

`metadata.jsonl` at the root indexes all sites.

## ☀️ Analysis layers — useful, not just beautiful

Beyond geometry, every model carries **simulation-ready environmental layers**
computed on the voxel grid (viewpoint height 1.5 m, tree parameters k=0.6,
LAD=1.0; solar uses the nearest EPW weather file):

| Layer | What it tells you | Typical use |
|---|---|---|
| ☀️ **Solar irradiance** (noon / full day, summer solstice) | Sun exposure & shading of facades and ground | Solar potential, heat-stress hotspots, visitor comfort |
| 🌳 **Green View Index** | How much vegetation a pedestrian sees | Greenery assessment, wellbeing, urban forestry |
| 🌤️ **Sky View Index** | Sky openness from the ground | Canyon effects, ventilation, daylight access |

Raw grids are provided as compressed `.npz` for downstream analysis:

```python
import numpy as np
grid = np.load("solar_solstice_day.npz")["grid"]  # 2D array, Wh/m²·day
```

View a model directly in the browser: drag `model.glb` onto
[3dviewer.net](https://3dviewer.net/) or any glTF viewer.

## 🎯 Quality gate

Only models that **passed the automated quality gate** are published here —
checks include degenerate geometry, terrain relief, and building plausibility
for Cultural/Mixed sites (see each site's `quality.json`). Models built from
degraded fallback data sources are **flagged** for manual review and included
only when noted.

## 🗺️ Data sources

- 📍 Site coordinates & metadata: UNESCO open data portal —
  [World Heritage List (whc001)](https://data.unesco.org/explore/dataset/whc001/),
  [Man and the Biosphere Programme (mab001)](https://data.unesco.org/explore/dataset/mab001/)
- 🏢 Buildings: OpenStreetMap / Overture Maps footprints
- 🌲 Canopy: ETH Global Sentinel-2 10 m canopy height
- ⛰️ Terrain: FABDEM / Copernicus DEM via Google Earth Engine
- 🌦️ Weather: nearest EPW (Ladybug Tools / EnergyPlus)

## 📊 Sites in this release

| site_key | name | country | category | quality |
|---|---|---|---|---|
{rows}

## 🔧 Reproduce

Generated with the open-source pipeline:
[unesco/heritage-3d-generator](https://github.com/unesco/heritage-3d-generator)

```bash
poetry run python unesco_data.py   # fetch UNESCO catalogs
poetry run python batch.py --pilot # generate + quality gate + analysis
poetry run python upload_hf.py     # publish to HF
```

## 📜 License & attribution

CC-BY-SA-4.0. Contains OpenStreetMap data © OpenStreetMap contributors (ODbL),
Overture Maps data (CDLA-Permissive), and derived Earth Engine products.
Please credit **UNESCO Data & AI** and the underlying data providers when reusing.

_Generated {datetime.now(timezone.utc).date().isoformat()} by the UNESCO Data & AI team._
"""


def rebuild_card_from_hub(repo: str, token: str):
    """Rebuild README.md + metadata.jsonl from per-site files already on the Hub.

    Needed after parallel shard jobs: each shard uploads only its own sites
    (with --no-card), so the final card must aggregate all shards server-side.
    """
    from huggingface_hub import hf_hub_download

    api = HfApi(token=token)
    files = api.list_repo_files(repo, repo_type="dataset")
    sites = []
    for f in sorted(files):
        parts = f.split("/")
        if len(parts) != 3 or parts[2] != "metadata.json":
            continue
        programme, site_dir, _ = parts
        site_path = hf_hub_download(repo, f, repo_type="dataset", token=token)
        metadata = json.loads(Path(site_path).read_text())
        quality = {"status": "unknown"}
        qf = f"{programme}/{site_dir}/quality.json"
        if qf in files:
            q_path = hf_hub_download(repo, qf, repo_type="dataset", token=token)
            quality = json.loads(Path(q_path).read_text())
        sites.append({"dir": Path(site_dir), "programme": programme,
                      "metadata": metadata, "quality": quality})
    if not sites:
        sys.exit(f"No site metadata found in {repo}")
    tmp = Path("output/.hf_upload")
    tmp.mkdir(exist_ok=True)
    (tmp / "metadata.jsonl").write_text(build_metadata_jsonl(sites))
    (tmp / "README.md").write_text(build_readme(sites))
    for name in ("metadata.jsonl", "README.md"):
        api.upload_file(path_or_fileobj=str(tmp / name), path_in_repo=name,
                        repo_id=repo, repo_type="dataset")
    print(f"🃏 Card rebuilt from {len(sites)} sites — "
          f"https://huggingface.co/datasets/{repo}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=DEFAULT_REPO,
                        help="HF dataset repo id (or set HF_DATASET_REPO)")
    parser.add_argument("--include-flagged", action="store_true")
    parser.add_argument("--preset", default="premium",
                        help="Only upload models generated at this preset (default: premium)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-card", action="store_true",
                        help="Skip README.md + metadata.jsonl (use for parallel "
                             "shards so they don't overwrite each other's card)")
    parser.add_argument("--rebuild-card", action="store_true",
                        help="Rebuild README.md + metadata.jsonl from the site "
                             "folders already on the Hub, then exit")
    args = parser.parse_args()

    token = os.environ.get("HF_TOKEN")
    if not token and not args.dry_run:
        sys.exit("HF_TOKEN not set — export a Hugging Face token with write access")

    if args.rebuild_card:
        rebuild_card_from_hub(args.repo, token)
        return

    sites = collect_sites(args.include_flagged, args.preset)
    if not sites:
        sys.exit(f"No quality-passed sites at preset '{args.preset}' in output/ — run batch.py first")

    print(f"📦 {len(sites)} site(s) eligible for upload to {args.repo}:")
    total_bytes = 0
    for s in sites:
        files = [p for p in s["dir"].iterdir()
                 if p.suffix in UPLOAD_SUFFIXES and p.is_file()]
        size = sum(p.stat().st_size for p in files)
        total_bytes += size
        print(f"   {s['programme']}/{s['dir'].name} "
              f"({len(files)} files, {size / 1e6:.1f} MB, {s['quality']['status']})")
    print(f"   Total: {total_bytes / 1e6:.1f} MB")

    if args.dry_run:
        return

    api = HfApi(token=token)
    api.create_repo(args.repo, repo_type="dataset", private=True, exist_ok=True)
    print(f"✅ Repo ready: https://huggingface.co/datasets/{args.repo} (private)")

    for s in sites:
        path_in_repo = f"{s['programme']}/{s['dir'].name}"
        print(f"⬆️  Uploading {path_in_repo} ...")
        api.upload_folder(folder_path=str(s["dir"]), path_in_repo=path_in_repo,
                          repo_id=args.repo, repo_type="dataset",
                          ignore_patterns=["*.h5", "*.inx", "*.edb"])

    # Root-level index + dataset card (skipped for parallel shards)
    if args.no_card:
        print("⏭️  --no-card: skipping README.md/metadata.jsonl "
              "(rebuild later with --rebuild-card)")
        return
    tmp = Path("output/.hf_upload")
    tmp.mkdir(exist_ok=True)
    (tmp / "metadata.jsonl").write_text(build_metadata_jsonl(sites))
    (tmp / "README.md").write_text(build_readme(sites))
    for name in ("metadata.jsonl", "README.md"):
        api.upload_file(path_or_fileobj=str(tmp / name), path_in_repo=name,
                        repo_id=args.repo, repo_type="dataset")
    print(f"🎉 Done — https://huggingface.co/datasets/{args.repo}")


if __name__ == "__main__":
    main()
