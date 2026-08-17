# UNESCO Heritage Sites 3D Generator

> Generate detailed 3D models of UNESCO World Heritage Sites and Biosphere Reserves using Google Earth Engine and VoxCity 1.6 — quality-gated and published to Hugging Face

[![UNESCO Data & AI](https://img.shields.io/badge/UNESCO-Data%20%26%20AI-0077B6?logo=united-nations&logoColor=white)](https://github.com/unesco)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**[Complete Wiki & Guides](wiki/README.md)** | **[Quick Start](wiki/Quick-Start.md)** | **[Parameter Tuning](wiki/Parameter-Tuning.md)**

## 🌍 End-to-End Pipeline (new)

Fetch the full UNESCO catalogs, batch-generate quality-gated 3D models, and publish to a private Hugging Face dataset:

```bash
# 1. Fetch site catalogs (WHC whc001 + MAB mab001 → data/sites.csv, ~2,040 sites)
poetry run python unesco_data.py

# 2. Batch generate (pilot: 5 WHC + 5 MAB, premium quality, resume-safe)
poetry run python batch.py --pilot

# 3. Upload quality-passed models to HF (HF_TOKEN with write access)
export HF_TOKEN=hf_...
export HF_DATASET_REPO=your-username/heritage-3d-models
poetry run python upload_hf.py            # add --dry-run to preview
```

Every generated site is checked by an automated **quality gate** (`quality_gate.py`):
models with degenerate geometry, missing terrain, or missing buildings (for
Cultural/Mixed sites) are **failed** and never uploaded; models built from
degraded fallback data sources are **flagged** for manual review.

Each site directory contains `model.obj`/`model.mtl` (voxel), `model.glb`
(web-friendly voxel, Y-up, colored), `model_smooth.glb` (non-voxel hybrid:
triangulated DEM terrain + LOD1 building prisms), a `preview.png` for visual
inspection, `metadata.json` (provenance + generation config), `quality.json`
(metrics + status), and the **analysis layers** described below.

## ☀️ Analysis Layers — useful, not just beautiful

Every model is more than a render: it ships with **environmental simulation
layers** computed on the voxel grid (`analysis.py`, on by default — skip with
`--no-analysis`):

| Layer | Files | What it tells you |
|-------|-------|-------------------|
| ☀️ **Solar irradiance** (solstice noon) | `solar_solstice_noon.png/.npz` | Instantaneous sun exposure (W/m²), Jun 21 12:00 |
| 📆 **Solar irradiance** (solstice day) | `solar_solstice_day.png/.npz` | Cumulative daily exposure (Wh/m²·day), Jun 21 |
| 🌳 **Green View Index** | `green_index.png/.npz` | Vegetation visible at pedestrian level (0–1) |
| 🌤️ **Sky View Index** | `sky_index.png/.npz` | Sky openness from the ground (0–1) |

Solar layers use the **nearest EPW weather file** (auto-downloaded); view
indices use a 1.5 m viewpoint height. PNGs are ready-made maps with colorbars;
`.npz` files hold the raw grids for your own analysis:

```python
import numpy as np
solar = np.load("output/whc/252_taj_mahal/solar_solstice_day.npz")["grid"]
```

Use cases: ☀️ solar-panel potential & heat-stress hotspots, 🌳 greenery/wellbeing
assessment, 🌤️ canyon-effect & daylight studies, 🌡️ microclimate pre-screening
for ENVI-met runs.

To (re)compute analysis layers for already-generated sites without
re-generating the models:

```bash
poetry run python backfill_analysis.py
```

Prerequisite: Earth Engine authentication (`poetry run earthengine authenticate`,
project ID via `EE_PROJECT_ID` in `.env` — copy `.env.example` and set your own
GEE project id; `.env` is git-ignored).

### 🤗 Running on Hugging Face Jobs (optional)

`submit_hf_job.sh` runs the whole pipeline on HF Jobs infrastructure (code
bundle → batch → upload, EE credentials passed as job secrets). All account-
specific values are environment-driven — see the header of the script:
`HF_TOKEN`, `HF_DATASET_REPO`, `EE_PROJECT_ID`, optional `HF_JOB_NAMESPACE`
(org billing). Note: HF Jobs is pay-as-you-go.

## ✨ Quality Preset System

Choose from **4 optimized quality levels** for different use cases:

| Quality | Coverage | Detail | Time | Use Case |
|---------|----------|--------|------|----------|
| **🚀 PREVIEW** | 0.25 km² | 10m voxels | 30-60s | Quick location testing |
| **⚖️ STANDARD** | 0.56 km² | 5m voxels | 2-4 min | General documentation |
| **🏆 PREMIUM** | 1.0 km² | 3m voxels | 8-15 min | Important heritage sites |
| **💎 ULTIMATE** | 1.44 km² | 2m voxels | 20-45 min | Critical preservation |

## 🚀 Quick Start

```bash
# 1. Install dependencies
poetry install --no-root

# 2. Setup with quality presets (interactive)
poetry run python setup.py

# 3. Generate your first model
poetry run python main.py test
```

## 📖 Usage Examples

### Basic Usage
```bash
# Interactive mode with quality selection
poetry run python main.py

# Quick test (Mont-Saint-Michel)
poetry run python main.py test

# Specific site by key (whc:<id_no> or mab:<mab_id>)
poetry run python main.py whc:274      # Machu Picchu
poetry run python main.py mab:USYe1976 # Yellowstone - Grand Teton
```

### Quality Preset Usage
```bash
# Use specific quality preset
poetry run python main.py --quality preview   # Fast preview
poetry run python main.py --quality standard  # Balanced (default)
poetry run python main.py --quality premium   # High quality
poetry run python main.py --quality ultimate  # Maximum quality

# Site + Quality combination
poetry run python main.py whc:274 --quality ultimate  # Machu Picchu in max quality
```

### Information Commands
```bash
# List available quality presets
poetry run python main.py --list-quality

# Show detailed preset information
poetry run python main.py --quality-details premium

# Quality system CLI
poetry run python quality_config.py
```

## 🛠️ Setup & Configuration

### First Time Setup
```bash
# Interactive setup with quality preset selection
poetry run python setup.py

# Or apply specific preset directly
poetry run python setup.py --preset standard

# Validate installation
poetry run python setup.py --validate
```

### Earth Engine Setup (One-time)
```bash
poetry run earthengine authenticate
poetry run earthengine set_project <your-gee-project-id>
```

## 🗂️ Project Structure

```
heritage-3d-generator/
├── main.py                         # 🎯 Single-site CLI (site key, row number, or 'test')
├── pipeline.py                     # 🏗️ Shared generation core (VoxCity 1.6, fallback chain)
├── analysis.py                     # ☀️ Solar irradiance + Green/Sky View Index layers
├── backfill_analysis.py            # 🔁 Recompute analysis layers for existing sites
├── batch.py                        # 📦 Batch runner (pilot / selected / all, resume-safe)
├── quality_gate.py                 # 🎯 Quality metrics, pass/flag/fail, preview PNG
├── smooth_export.py                # 🏙️ Smooth GLB export (DEM terrain + LOD1 buildings)
├── regen_smooth.py                 # 🔁 Re-export smooth GLBs after exporter improvements
├── upload_hf.py                    # 🤗 Publish passed models + dataset card to HF
├── unesco_data.py                  # 🌍 Fetch whc001 + mab001 catalogs (Huwise API)
├── submit_hf_job.sh                # ☁️ Run the pipeline on HF Jobs (optional)
├── quality_config.py               # 🎯 Quality configuration system
├── setup.py                        # 🛠️ Setup and validation script
├── data/
│   ├── unesco_heritage_sites.csv   # 🏛️ Legacy 10-site database
│   └── sites.csv                   # 🌍 Normalized catalog (generated, git-ignored)
├── output/                         # 📁 Per-site dirs: OBJ/GLB/smooth GLB, preview, metadata
├── wiki/                           # 📚 Complete documentation
├── .env.example                    # ⚙️ Config template (copy to git-ignored .env)
└── pyproject.toml                  # 📦 Poetry dependencies
```

## 🎯 Quality Preset Details

### 🚀 PREVIEW
- **Purpose**: Quick location testing, site exploration
- **Coverage**: 500m × 500m (0.25 km²)
- **Resolution**: 10m voxels (2,500 total)
- **Time**: 30-60 seconds
- **Data Sources**: Basic OpenStreetMap + FABDEM

### ⚖️ STANDARD (Default)
- **Purpose**: General UNESCO documentation, presentations
- **Coverage**: 750m × 750m (0.56 km²)
- **Resolution**: 5m voxels (22,500 total)
- **Time**: 2-4 minutes
- **Data Sources**: OpenStreetMap + ETH Canopy + FABDEM

### 🏆 PREMIUM
- **Purpose**: Important heritage site documentation, research
- **Coverage**: 1000m × 1000m (1.0 km²)
- **Resolution**: 3m voxels (111,111 total)
- **Time**: 8-15 minutes
- **Data Sources**: OSM + ESRI Land Cover + High-res Canopy + FABDEM

### 💎 ULTIMATE
- **Purpose**: Critical heritage preservation, academic research
- **Coverage**: 1200m × 1200m (1.44 km²)
- **Resolution**: 2m voxels (360,000 total)
- **Time**: 20-45 minutes
- **Data Sources**: Microsoft Buildings + ESRI + High-res Canopy + DeltaDTM

## 🎨 Viewing Results

### Online Viewers
- **3D Viewer**: https://3dviewer.net/ (drag & drop .obj file)
- **Sketchfab**: Upload for sharing and embedding

### Desktop Software
- **macOS**: `open output/Site_Name.obj`
- **Blender**: File > Import > Wavefront (.obj)
- **Rhino**: Professional 3D modeling
- **MagicaVoxel**: Voxel editing and visualization

### Generated Files
```
output/<programme>/<site>/
├── model.obj / model.mtl          # 3D model geometry (voxel)
├── model.glb                      # Web-friendly voxel GLB (Y-up, colored)
├── model_smooth.glb               # Smooth hybrid: DEM terrain + LOD1 buildings
├── preview.png                    # 3D render for quick inspection
├── solar_solstice_noon.png/.npz   # ☀️ Instantaneous irradiance (W/m²)
├── solar_solstice_day.png/.npz    # ☀️ Cumulative daily irradiance (Wh/m²·day)
├── green_index.png/.npz           # 🌳 Green View Index (0–1)
├── sky_index.png/.npz             # 🌤️ Sky View Index (0–1)
├── metadata.json                  # Provenance + generation config
├── quality.json                   # Quality-gate metrics + status
└── voxcity.INX                    # ENVI-MET simulation file (opt-in --envimet)
```

## 🏛️ UNESCO Heritage Sites Database

| ID | Site | Country | Type | Year |
|----|------|---------|------|------|
| 0 | Galápagos Islands | 🇪🇨 Ecuador | Natural | 1978 |
| 1 | Mont-Saint-Michel and its Bay | 🇫🇷 France | Cultural | 1979 |
| 2 | Palace and Park of Versailles | 🇫🇷 France | Cultural | 1979 |
| 3 | Historic Sanctuary of Machu Picchu | 🇵🇪 Peru | Mixed | 1983 |
| 4 | Petra | 🇯🇴 Jordan | Cultural | 1985 |
| 5 | Angkor | 🇰🇭 Cambodia | Cultural | 1992 |
| 6 | Taj Mahal | 🇮🇳 India | Cultural | 1983 |
| 7 | Historic Centre of Rome | 🇮🇹 Italy | Cultural | 1980 |
| 8 | Yellowstone National Park | 🇺🇸 USA | Natural | 1978 |
| 9 | Memphis and its Necropolis | 🇪🇬 Egypt | Cultural | 1979 |

## 🔧 Advanced Configuration

### Manual Quality Settings (.env)
```bash
# Zone parameters
ZONE_SIZE_METERS=750        # Coverage area (500-1200m)
MESH_SIZE_METERS=5          # Voxel size (2-10m)

# Data sources (quality hierarchy)
BUILDING_SOURCE=OpenStreetMap                    # or Microsoft Building Footprints
LAND_COVER_SOURCE=OpenStreetMap                  # or ESRI Land Cover
CANOPY_HEIGHT_SOURCE=ETH Global Sentinel-2 10m  # or High Resolution 1m Global
DEM_SOURCE=FABDEM                                # or DeltaDTM
DEM_INTERPOLATION=true                           # Enhanced terrain processing
```

### Custom Presets
Create your own quality preset by modifying `quality_config.py`:
```python
custom = QualityConfig(
    name="CUSTOM",
    description="🎯 Your custom configuration",
    zone_size=800,     # Custom coverage
    mesh_size=4,       # Custom resolution
    # ... other parameters
)
```

## 🚨 Troubleshooting

### Common Issues
1. **Earth Engine Authentication**:
   ```bash
   poetry run earthengine authenticate
   poetry run earthengine set_project <your-gee-project-id>
   ```

2. **Quality System Not Available**:
   - Ensure `quality_config.py` exists
   - Run `poetry run python setup.py --validate`

3. **Generation Failures**:
   - Try lower quality preset: `--quality preview`
   - Check Earth Engine quotas
   - Verify internet connection

4. **Performance Issues**:
   - Use PREVIEW preset for testing
   - Reduce zone size in .env
   - Increase mesh size for faster generation

## 📊 Performance Comparison

| Quality | Voxels | File Size | RAM Usage | Recommended For |
|---------|--------|-----------|-----------|-----------------|
| PREVIEW | 2.5K | ~1MB | Low | Testing, exploration |
| STANDARD | 22.5K | ~5MB | Medium | Documentation, sharing |
| PREMIUM | 111K | ~15MB | High | Research, analysis |
| ULTIMATE | 360K | ~50MB | Very High | Archive, critical work |

## 🔒 Secrets & Sanitization

This repo is safe for public release by design:

- **No credentials in the repo** — `HF_TOKEN`, `EE_PROJECT_ID`, `HF_DATASET_REPO`
  are read from the environment / `.env` (git-ignored; use `.env.example` as template)
- **Earth Engine credentials** stay in `~/.config/earthengine/` and are only ever
  passed as HF Job secrets at submit time (never written to the repo)
- `.gitignore` covers `.env`, outputs, caches, fetched catalogs, secret-file
  patterns, and journal PDFs (copyright)
- UNESCO site coordinates come from the **public** data.unesco.org API —
  no internal endpoints anywhere

## 🤝 Contributing

This project supports UNESCO's mission of World Heritage preservation through digital documentation.

### Development
```bash
# Clone and setup
git clone https://github.com/unesco/heritage-3d-generator.git
cd heritage-3d-generator
poetry install --no-root

# Test changes
poetry run python setup.py --validate
poetry run python main.py test --quality preview
```

### Adding New Sites
1. Add coordinates to `data/unesco_heritage_sites.csv`
2. Test with PREVIEW quality first
3. Update documentation

## 📝 Technical Details

- **VoxCity Version**: 1.6.2 (new object-based API: `get_voxcity()` returns a `VoxCity` dataclass)
- **Python**: 3.12+
- **Dependencies**: Rich, Pandas, Earth Engine API, Tenacity, Hugging Face Hub, Requests
- **Export Formats**: OBJ (+MTL), GLB (voxel + smooth hybrid), ENVI-MET (INX, opt-in via `--envimet`)
- **Analysis Layers**: solar irradiance (EPW-based), Green/Sky View Index (PNG + raw `.npz`)
- **Data Sources**: OpenStreetMap, Google Earth Engine, ESRI, Microsoft
- **Site Catalogs**: UNESCO data.unesco.org (Huwise API) — whc001 (1,244 sites) + mab001 (797 sites)
- **Quality Gate**: automated metrics + pass/flag/fail before any HF publication
- **Fallback Logic**: 7-strategy automatic source switching on failures

## 🌟 Features

- ✅ **Quality Preset System**: 4 optimized configurations
- ✅ **Analysis Layers**: solar irradiance, Green/Sky View Index out of the box
- ✅ **Interactive UI**: Rich console with progress bars
- ✅ **Robust Generation**: Automatic fallback on failures
- ✅ **Multiple Exports**: OBJ, GLB (voxel + smooth), ENVI-MET, colored models
- ✅ **Heritage Catalog**: 2,000+ sites from UNESCO open data (whc001 + mab001)
- ✅ **Quality Gate**: automated pass/flag/fail before any publication
- ✅ **Easy Setup**: Automated configuration and validation

## License

This project is licensed under the [MIT License](LICENSE).

---

*Generated with ❤️ for UNESCO World Heritage preservation by the UNESCO Data & AI Team*

**🎯 Ready to create your first 3D heritage model?**
```bash
poetry run python main.py --quality standard
```