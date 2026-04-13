# ⚙️ Parameter Tuning Guide

Balance quality vs speed for optimal 3D model generation.

## 🎯 Quality vs Speed Matrix

| Priority | Mesh Size | Zone Size | Processing Time | Detail Level | Use Case |
|----------|-----------|-----------|-----------------|--------------|----------|
| **Speed** | 10m | 500m | ~30 seconds | Low | Quick preview |
| **Balanced** | 5m | 1000m | ~2 minutes | Medium | General use |
| **Quality** | 2m | 1000m | ~5 minutes | High | Detailed analysis |
| **Maximum** | 1m | 2000m | ~15 minutes | Very High | Publication quality |

## ⚡ Speed Optimization

### Fast Preview Settings
```bash
# .env configuration for quick testing
ZONE_SIZE_METERS=500
MESH_SIZE_METERS=10
BUILDING_SOURCE=OpenStreetMap
```

**Benefits:**
- ✅ Very fast processing (~30 seconds)
- ✅ Good for testing coordinates
- ✅ Low data usage
- ❌ Limited detail
- ❌ May miss small buildings

### When to Use:
- Testing new heritage sites
- Batch processing many locations
- Internet bandwidth limitations
- Development/debugging

## 🎨 Quality Enhancement

### High-Detail Settings
```bash
# .env configuration for best quality
ZONE_SIZE_METERS=1000
MESH_SIZE_METERS=2
BUILDING_SOURCE=Microsoft Building Footprints
CANOPY_HEIGHT_SOURCE=High Resolution 1m Global Canopy Height Maps
DEM_SOURCE=USGS 3DEP 1m DEM  # For US sites
```

**Benefits:**
- ✅ Excellent detail (2m resolution)
- ✅ Accurate building heights
- ✅ High-quality vegetation data
- ❌ Slower processing (~5 minutes)
- ❌ Higher data usage

### When to Use:
- Final presentation models
- Research publications
- Detailed urban analysis
- Important heritage sites

## 📊 Parameter Impact Analysis

### Mesh Size Effects
```bash
MESH_SIZE_METERS=1   # 10,000x detail   (~15 min)
MESH_SIZE_METERS=2   # 2,500x detail    (~5 min)
MESH_SIZE_METERS=5   # 400x detail      (~2 min)
MESH_SIZE_METERS=10  # 100x detail      (~30 sec)
```

**Rule of thumb:** Halving mesh size = 4x more detail + 4x processing time

### Zone Size Effects
```bash
ZONE_SIZE_METERS=500   # 0.25 km²   Small site focus
ZONE_SIZE_METERS=1000  # 1 km²      Standard coverage  
ZONE_SIZE_METERS=2000  # 4 km²      Regional context
ZONE_SIZE_METERS=5000  # 25 km²     City-wide view
```

**Considerations:**
- Larger zones show more context but take longer
- Some heritage sites need large zones (e.g., landscape sites)
- Very large zones may hit Earth Engine quotas

## 🗺️ Data Source Performance

### Building Sources (Speed → Quality)
1. **OpenStreetMap** - Fastest, good coverage, variable quality
2. **Overture** - Fast, consistent quality, good global coverage
3. **Microsoft Building Footprints** - Medium speed, excellent accuracy
4. **EUBUCCO** - Slower, highest quality (Europe only)

### Canopy Sources (Speed → Quality)
1. **ETH Global Sentinel-2 10m** - Fast, 10m resolution
2. **High Resolution 1m Global Canopy Height Maps** - Slower, 1m resolution

## 🎛️ Recommended Configurations

### European Heritage Sites
```bash
BUILDING_SOURCE=EUBUCCO
LAND_COVER_SOURCE=OpenStreetMap
CANOPY_HEIGHT_SOURCE=High Resolution 1m Global Canopy Height Maps
DEM_SOURCE=FABDEM
MESH_SIZE_METERS=2
ZONE_SIZE_METERS=1000
```

### North American Sites
```bash
BUILDING_SOURCE=Microsoft Building Footprints
LAND_COVER_SOURCE=ESRI 10m Annual Land Cover
CANOPY_HEIGHT_SOURCE=High Resolution 1m Global Canopy Height Maps
DEM_SOURCE=USGS 3DEP 1m DEM
MESH_SIZE_METERS=2
ZONE_SIZE_METERS=1000
```

### Global/Remote Sites
```bash
BUILDING_SOURCE=OpenStreetMap
LAND_COVER_SOURCE=ESA World Cover 10m 2021
CANOPY_HEIGHT_SOURCE=ETH Global Sentinel-2 10m
DEM_SOURCE=FABDEM
MESH_SIZE_METERS=5
ZONE_SIZE_METERS=1000
```

## 🔧 Performance Tuning Tips

### 1. Start Small, Scale Up
```bash
# Test with fast settings first
MESH_SIZE_METERS=10
ZONE_SIZE_METERS=500

# Then increase quality if needed
MESH_SIZE_METERS=5
ZONE_SIZE_METERS=1000
```

### 2. Monitor Resource Usage
- Check your Google Earth Engine quotas
- Monitor internet bandwidth
- Watch CPU/memory usage during processing

### 3. Batch Processing Strategy
```bash
# Process multiple sites with balanced settings
MESH_SIZE_METERS=5
ZONE_SIZE_METERS=750
```

### 4. Site-Specific Optimization
- **Urban sites**: Prioritize building data quality
- **Natural sites**: Prioritize DEM and canopy quality
- **Coastal sites**: Ensure zone captures water features
- **Mountain sites**: Use high-resolution DEM

## 📈 Quality Indicators

### Good Results Show:
- ✅ Clear building outlines
- ✅ Proper terrain elevation
- ✅ Recognizable landmark features
- ✅ Smooth water surfaces
- ✅ Vegetation in appropriate areas

### Poor Results Show:
- ❌ Blocky, unrecognizable shapes
- ❌ Missing major buildings
- ❌ Flat or incorrect terrain
- ❌ Vegetation in water areas
- ❌ Missing height variation

## 🚀 Quick Commands

```bash
# Test new parameters
poetry run python run.py test

# Debug failed exports
poetry run python debug_export.py

# Check file sizes
ls -lh output/

# View results online
open https://3dviewer.net/
```

## 💡 Expert Tips

1. **Earth Engine Quotas**: Very large zones may hit daily limits
2. **Regional Data**: Some data sources work better in specific regions
3. **Processing Order**: VoxCity processes in this order: Land Cover → Buildings → Canopy → DEM → Export
4. **Failure Recovery**: If one data source fails, try fallback sources
5. **Memory Usage**: Very high resolution (1m mesh) may require more RAM

---
*Remember: The best parameters depend on your specific heritage site and use case!*
