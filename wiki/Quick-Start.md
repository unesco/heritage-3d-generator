# 🚀 Quick Start Guide

Generate your first UNESCO heritage site 3D model in 5 minutes!

## ⚡ 1-Minute Test

Once you have everything set up, test with Mont-Saint-Michel:

```bash
cd /path/to/xyto3d
poetry run python run.py test
```

**Expected output:**
```
🏰 Running in TEST MODE with Mont-Saint-Michel
📍 Coordinates: 48.63556, -1.51056
✅ Earth Engine initialized
🗺️  Zone size: 1000m x 1000m
🏗️  Generating 3D city model...
✅ Voxel city generation completed!
📦 Exporting OBJ file...
✅ OBJ file exported: Mont-Saint-Michel.obj
🎉 Success! Files generated in output/
```

## 🎯 View Your Model

### Online (Fastest)
1. Go to https://3dviewer.net/
2. Drag & drop `output/Mont-Saint-Michel.obj`
3. Explore your 3D model!

### macOS Preview
```bash
open output/Mont-Saint-Michel.obj
```

## 📝 Process Your Own Sites

### From CSV File
```bash
# Your UNESCO heritage sites CSV
poetry run python run.py whc001.csv 0

# Process different rows
poetry run python run.py your_sites.csv 5
```

### Single Site Test
Edit `.env` file:
```bash
# Test any coordinates
TEST_LAT=48.8584    # Eiffel Tower
TEST_LON=2.2945
TEST_NAME=Eiffel-Tower

# Then run
poetry run python run.py test
```

## ⚙️ Quick Customization

### For Speed (30 seconds)
```bash
# Edit .env
MESH_SIZE_METERS=10
ZONE_SIZE_METERS=500
```

### For Quality (5 minutes)
```bash
# Edit .env
MESH_SIZE_METERS=2
ZONE_SIZE_METERS=1000
BUILDING_SOURCE=Microsoft Building Footprints
```

## 🏛️ Example Heritage Sites

Try these coordinates in test mode:

```bash
# Machu Picchu, Peru
TEST_LAT=-13.1631
TEST_LON=-72.5450
TEST_NAME=Machu-Picchu

# Petra, Jordan
TEST_LAT=30.3285
TEST_LON=35.4444
TEST_NAME=Petra

# Angkor Wat, Cambodia
TEST_LAT=13.4125
TEST_LON=103.8670
TEST_NAME=Angkor-Wat

# Taj Mahal, India
TEST_LAT=27.1751
TEST_LON=78.0421
TEST_NAME=Taj-Mahal
```

## 📁 Output Files

After successful generation, you'll find:

```
output/
├── Mont-Saint-Michel.obj      # 3D model (main file)
├── Mont-Saint-Michel.mtl      # Material definitions
├── building.gpkg             # Building data
├── canopy_height.tif         # Tree height data
├── dem.tif                   # Terrain elevation
└── voxcity_data.pkl          # Processed voxel data
```

## 🔧 Common Quick Fixes

### Script Stops After "Voxcity data saved"
```bash
# Use debug export
poetry run python debug_export.py
```

### Permission Errors
```bash
# Re-authenticate
poetry run earthengine authenticate
poetry run earthengine set_project xyto3d
```

### No Buildings Visible
```bash
# Try different building source
BUILDING_SOURCE=Microsoft Building Footprints
```

### Model Too Blocky
```bash
# Increase resolution
MESH_SIZE_METERS=2
```

## 🎨 3D Viewing Options

### Free Desktop Software
```bash
# Blender (professional)
brew install --cask blender

# MeshLab (lightweight)
brew install --cask meshlab
```

### Online Viewers
- **3dviewer.net** - Drag & drop, instant viewing
- **Sketchfab.com** - Upload for sharing
- **Clara.io** - Online 3D editor

## 📊 Typical Processing Times

| Site Type | Mesh Size | Zone Size | Time | Detail |
|-----------|-----------|-----------|------|--------|
| Small monument | 5m | 500m | 1 min | Good |
| Historic center | 2m | 1000m | 5 min | Excellent |
| Large complex | 2m | 2000m | 10 min | Excellent |
| Landscape site | 5m | 5000m | 15 min | Good |

## 🚨 When Things Go Wrong

### Check the basics:
```bash
# 1. Are you in the right directory?
pwd  # Should show: .../xyto3d

# 2. Is Earth Engine working?
poetry run earthengine ls

# 3. Are environment variables loaded?
cat .env

# 4. Try the debug script
poetry run python debug_export.py
```

### Still stuck?
Check the [Troubleshooting Guide](Troubleshooting.md) for detailed solutions.

## 🎯 Next Steps

1. **Master the basics** with Mont-Saint-Michel
2. **Try your own coordinates** using test mode
3. **Process your CSV data** with heritage sites
4. **Optimize parameters** using the [Parameter Tuning Guide](Parameter-Tuning.md)
5. **Explore advanced features** in [Advanced Configuration](Advanced-Configuration.md)

## 💡 Pro Tips

- **Always test with small zones first** before going large
- **Different regions need different data sources** - see [Regional Optimization](Regional-Optimization.md)
- **Save successful configurations** for similar sites
- **Use online viewers** for quick preview, desktop software for detailed work

---
Happy 3D modeling! 🏛️✨
