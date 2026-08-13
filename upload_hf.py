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
                     preview.png, metadata.json, quality.json}
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

UPLOAD_SUFFIXES = {".obj", ".mtl", ".glb", ".png", ".json"}


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
    rows = "\n".join(
        f"| {s['metadata']['site_key']} | {s['metadata']['name']} | "
        f"{s['metadata']['country']} | {s['metadata']['category']} | "
        f"{s['quality']['status']} |"
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
pretty_name: UNESCO Heritage 3D Models
---

# UNESCO Heritage 3D Models

Voxel-based 3D models of UNESCO World Heritage sites and Biosphere Reserves,
generated with [VoxCity](https://github.com/kunifujiwara/VoxCity) from open
geospatial data (OpenStreetMap, ETH canopy, FABDEM terrain via Google Earth Engine).

Site coordinates and metadata come from UNESCO's open data portal:
- [World Heritage List (whc001)](https://data.unesco.org/explore/dataset/whc001/)
- [Man and the Biosphere Programme (mab001)](https://data.unesco.org/explore/dataset/mab001/)

Only models that **passed the automated quality gate** are published here
(building/terrain/land-cover plausibility checks; see each site's `quality.json`).

## Contents

- {n_whc} World Heritage sites, {n_mab} Biosphere Reserves
- Per site: `model.obj` + `model.mtl` (voxel geometry), `model.glb`
  (web-friendly voxel, Y-up, colored), `model_smooth.glb` (non-voxel hybrid:
  triangulated DEM terrain + LOD1 building prisms), `preview.png`,
  `metadata.json` (provenance + generation config), `quality.json` (metrics)
- `metadata.jsonl` at the root indexes all sites

| site_key | name | country | category | quality |
|---|---|---|---|---|
{rows}

_Generated {datetime.now(timezone.utc).date().isoformat()} by the UNESCO Data & AI team._
"""


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=DEFAULT_REPO,
                        help="HF dataset repo id (or set HF_DATASET_REPO)")
    parser.add_argument("--include-flagged", action="store_true")
    parser.add_argument("--preset", default="premium",
                        help="Only upload models generated at this preset (default: premium)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("HF_TOKEN")
    if not token and not args.dry_run:
        sys.exit("HF_TOKEN not set — export a Hugging Face token with write access")

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

    # Root-level index + dataset card
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
