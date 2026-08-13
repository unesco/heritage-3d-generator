#!/usr/bin/env python3
"""
🌍 UNESCO site catalog fetcher (Huwise/ODS Explore API v2.1)

Downloads the World Heritage List (whc001) and Man and the Biosphere (mab001)
datasets from data.unesco.org and normalizes them into a single sites table.

Usage:
    python unesco_data.py            # fetch + normalize, write data/sites.csv
    python unesco_data.py --stats    # show stats from existing data/sites.csv
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import requests

BASE_API = "https://data.unesco.org/api/explore/v2.1/catalog/datasets"
DATA_DIR = Path("data")

WHC_DATASET = "whc001"
MAB_DATASET = "mab001"

TIMEOUT = 120  # seconds, full CSV exports can be slow


def slugify(name: str, max_len: int = 60) -> str:
    """Filesystem/HF-safe slug from a site name."""
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
    return name[:max_len].strip("_") or "site"


def s(value) -> str:
    """Safe string: NaN/None -> ''."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def parse_coordinate_string(coord) -> Tuple[Optional[float], Optional[float]]:
    """Parse 'lat, lon' (Huwise geo_point_2d CSV format). Returns (lat, lon)."""
    if not isinstance(coord, str) or not coord.strip():
        return None, None
    parts = coord.split(",")
    if len(parts) != 2:
        return None, None
    try:
        lat, lon = float(parts[0].strip()), float(parts[1].strip())
    except ValueError:
        return None, None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None, None
    return lat, lon


def fetch_dataset_csv(dataset_id: str, out_path: Path) -> Path:
    """Download the full CSV export of a Huwise dataset."""
    url = f"{BASE_API}/{dataset_id}/exports/csv"
    print(f"⬇️  Downloading {dataset_id} from {url} ...")
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    print(f"   ✅ Saved {out_path} ({len(resp.content) / 1024:.0f} KB)")
    return out_path


def read_huwise_csv(path: Path) -> pd.DataFrame:
    """Huwise CSV exports are semicolon-delimited with a UTF-8 BOM."""
    return pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)


def normalize_whc(df: pd.DataFrame) -> pd.DataFrame:
    rows, skipped = [], 0
    for _, r in df.iterrows():
        lat, lon = parse_coordinate_string(r.get("coordinates"))
        id_no = s(r.get("id_no"))
        if lat is None or not id_no:
            skipped += 1
            continue
        rows.append({
            "site_key": f"whc:{id_no}",
            "name": s(r.get("name_en")),
            "programme": "WHC",
            "category": s(r.get("category")),
            "country": s(r.get("states_names")),
            "iso": s(r.get("iso_codes")),
            "lat": lat,
            "lon": lon,
            "year": s(r.get("date_inscribed"))[:4],
            "source_url": f"https://whc.unesco.org/en/list/{id_no}",
        })
    print(f"   WHC: {len(rows)} sites with valid coordinates ({skipped} skipped)")
    return pd.DataFrame(rows)


def normalize_mab(df: pd.DataFrame) -> pd.DataFrame:
    rows, skipped = [], 0
    for _, r in df.iterrows():
        lat, lon = parse_coordinate_string(r.get("coordinates"))
        mab_id = s(r.get("mab_id"))
        if lat is None or not mab_id:
            skipped += 1
            continue
        rows.append({
            "site_key": f"mab:{mab_id}",
            "name": s(r.get("title_en")),
            "programme": "MAB",
            "category": "Biosphere Reserve",
            "country": s(r.get("country_title_en")),
            "iso": s(r.get("iso2")),
            "lat": lat,
            "lon": lon,
            "year": s(r.get("date"))[:4],
            "source_url": s(r.get("url"))
                or "https://data.unesco.org/explore/dataset/mab001/",
        })
    print(f"   MAB: {len(rows)} sites with valid coordinates ({skipped} skipped)")
    return pd.DataFrame(rows)


def fetch_and_normalize() -> Path:
    DATA_DIR.mkdir(exist_ok=True)

    whc_raw = fetch_dataset_csv(WHC_DATASET, DATA_DIR / "whc001.csv")
    mab_raw = fetch_dataset_csv(MAB_DATASET, DATA_DIR / "mab001.csv")

    whc = normalize_whc(read_huwise_csv(whc_raw))
    mab = normalize_mab(read_huwise_csv(mab_raw))

    sites = pd.concat([whc, mab], ignore_index=True)
    out = DATA_DIR / "sites.csv"
    sites.to_csv(out, index=False)
    print(f"\n✅ Normalized catalog: {out} ({len(sites)} sites)")
    return out


def show_stats():
    path = DATA_DIR / "sites.csv"
    if not path.exists():
        sys.exit("data/sites.csv not found — run: python unesco_data.py")
    df = pd.read_csv(path)
    print(df.groupby(["programme", "category"]).size().to_string())
    print(f"\nTotal: {len(df)} sites")
    print(df["country"].value_counts().head(10).to_string())


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stats", action="store_true", help="Show stats from existing catalog")
    args = parser.parse_args()

    if args.stats:
        show_stats()
    else:
        fetch_and_normalize()


if __name__ == "__main__":
    main()
