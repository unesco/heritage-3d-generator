# 🎯 UNESCO Heritage Sites 3D Generator - Command Cheat Sheet

*Project folder: `Coordinates3D_Generator`*

## 🚀 Quick Start Commands
```bash
# First time setup
poetry run python setup.py

# Generate Mont-Saint-Michel test
poetry run python main.py test
```

## 📖 Basic Commands
```bash
# Interactive mode (site selection + quality)
poetry run python main.py

# Specific heritage site by ID
poetry run python main.py 0    # Galápagos Islands
poetry run python main.py 1    # Mont-Saint-Michel
poetry run python main.py 2    # Palace of Versailles
poetry run python main.py 3    # Machu Picchu
poetry run python main.py 4    # Petra
poetry run python main.py 5    # Angkor
poetry run python main.py 6    # Taj Mahal
poetry run python main.py 7    # Historic Rome
poetry run python main.py 8    # Yellowstone
poetry run python main.py 9    # Egyptian Pyramids
```

## 🎯 Quality Presets

### Using Quality Presets
```bash
# Preview quality (30-60 seconds)
poetry run python main.py --quality preview

# Standard quality (2-4 minutes) - Default
poetry run python main.py --quality standard

# Premium quality (8-15 minutes)
poetry run python main.py --quality premium

# Ultimate quality (20-45 minutes)
poetry run python main.py --quality ultimate
```

### Site + Quality Combinations
```bash
# Machu Picchu in premium quality
poetry run python main.py 3 --quality premium

# Taj Mahal in ultimate quality
poetry run python main.py 6 --quality ultimate

# Quick Petra preview
poetry run python main.py 4 --quality preview
```

## ℹ️ Information Commands
```bash
# List all quality presets
poetry run python main.py --list-quality

# Show preset details
poetry run python main.py --quality-details standard
poetry run python main.py --quality-details premium

# Quality system CLI
poetry run python quality_config.py
```

## 🛠️ Setup & Maintenance
```bash
# Interactive setup with quality selection
poetry run python setup.py

# Apply specific preset to .env
poetry run python setup.py --preset premium

# Validate installation
poetry run python setup.py --validate

# Run test generation
poetry run python setup.py --test
```

## ⚙️ Earth Engine Setup (One-time)
```bash
# Authenticate with Google Earth Engine
poetry run earthengine authenticate

# Set project ID
poetry run earthengine set_project <your-gee-project-id>
```

## 📁 File Operations
```bash
# Generated models
ls output/

# View OBJ file (macOS)
open output/Site_Name.obj

# Quality reports
cat output/Site_Name_quality_report.txt
```

## 🎨 Viewing Results
- **Online**: https://3dviewer.net/ (drag & drop .obj file)
- **Blender**: File > Import > Wavefront (.obj)
- **Desktop**: Double-click .obj files

## 🚨 Troubleshooting
```bash
# If quality system not working
poetry run python setup.py --validate

# If Earth Engine fails
poetry run earthengine authenticate

# If generation fails, try lower quality
poetry run python main.py test --quality preview

# Force reliable configuration
poetry run python quality_config.py apply standard
```

## 📊 Quality Comparison Quick Reference

| Preset | Time | Coverage | Detail | Best For |
|--------|------|----------|--------|----------|
| PREVIEW | 30-60s | 0.25 km² | 10m | Testing, exploration |
| STANDARD | 2-4 min | 0.56 km² | 5m | Documentation, sharing |
| PREMIUM | 8-15 min | 1.0 km² | 3m | Research, presentations |
| ULTIMATE | 20-45 min | 1.44 km² | 2m | Archive, critical work |

## 🔄 Common Workflows

### Quick Test Workflow
```bash
poetry run python main.py test --quality preview
```

### Production Documentation
```bash
poetry run python main.py 3 --quality premium  # Machu Picchu
poetry run python main.py 6 --quality premium  # Taj Mahal
```

### Batch Processing Multiple Sites
```bash
# Navigate to project folder
cd Coordinates3D_Generator

# Process multiple sites
for site in 1 3 6 7; do
  poetry run python main.py $site --quality standard
done
```

---
*Quick reference for UNESCO Heritage Sites 3D Generation*
