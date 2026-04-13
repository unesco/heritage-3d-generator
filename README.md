# UNESCO Heritage Sites 3D Generator

> Generate detailed 3D models of UNESCO World Heritage Sites using Google Earth Engine and VoxCity

[![UNESCO Data & AI](https://img.shields.io/badge/UNESCO-Data%20%26%20AI-0077B6?logo=united-nations&logoColor=white)](https://github.com/unesco)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**[Complete Wiki & Guides](wiki/README.md)** | **[Quick Start](wiki/Quick-Start.md)** | **[Parameter Tuning](wiki/Parameter-Tuning.md)**

## ✨ New: Quality Preset System

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

# Specific site by ID
poetry run python main.py 4
```

### Quality Preset Usage
```bash
# Use specific quality preset
poetry run python main.py --quality preview   # Fast preview
poetry run python main.py --quality standard  # Balanced (default)
poetry run python main.py --quality premium   # High quality
poetry run python main.py --quality ultimate  # Maximum quality

# Site + Quality combination
poetry run python main.py 4 --quality premium  # Machu Picchu in high quality
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
poetry run earthengine set_project xyto3d
```

## 🗂️ Project Structure

```
Coordinates3D_Generator/
├── main.py                         # 🎯 Enhanced main script with quality presets
├── quality_config.py               # 🎯 Quality configuration system
├── setup.py                        # 🛠️ Setup and validation script
├── enhanced_export.py              # 🎨 Colored OBJ export
├── data/
│   └── unesco_heritage_sites.csv   # 🏛️ UNESCO sites database (10 sites)
├── output/                         # 📁 Generated 3D models (.obj, .mtl, reports)
├── wiki/                           # 📚 Complete documentation
├── .env                            # ⚙️ Configuration & quality settings
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
output/
├── Site_Name.obj                    # 3D model geometry
├── Site_Name.mtl                    # Materials definition
├── Site_Name_quality_report.txt     # Quality & technical specs
├── Site_Name_colored.obj            # Enhanced colored model (if available)
└── voxcity.INX                      # ENVI-MET simulation file
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
   poetry run earthengine set_project xyto3d
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

- **VoxCity Version**: 0.5.22
- **Python**: 3.12+
- **Dependencies**: Rich, Pandas, Earth Engine API, Tenacity
- **Export Formats**: OBJ, ENVI-MET (INX), Quality Reports
- **Data Sources**: OpenStreetMap, Google Earth Engine, ESRI, Microsoft
- **Fallback Logic**: Automatic source switching on failures

## 🌟 Features

- ✅ **Quality Preset System**: 4 optimized configurations
- ✅ **Interactive UI**: Rich console with progress bars
- ✅ **Robust Generation**: Automatic fallback on failures
- ✅ **Multiple Exports**: OBJ, ENVI-MET, colored models
- ✅ **Heritage Database**: 10 UNESCO World Heritage Sites
- ✅ **Quality Reports**: Detailed technical documentation
- ✅ **Easy Setup**: Automated configuration and validation

## License

This project is licensed under the [MIT License](LICENSE).

---

*Generated with ❤️ for UNESCO World Heritage preservation by the UNESCO Data & AI Team*

**🎯 Ready to create your first 3D heritage model?**
```bash
poetry run python main.py --quality standard
```