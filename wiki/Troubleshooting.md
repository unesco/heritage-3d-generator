# 🚨 Troubleshooting Common VoxCity Errors

## 🔍 Error: `cannot access local variable 'image' where it is not associated with a value`

### What it means:
This is a VoxCity library bug that occurs when trying to access certain canopy height data sources, particularly "High Resolution Canopy Height Maps" sources.

### Quick Fix:
```bash
# Use PREVIEW quality (most reliable)
poetry run python main.py test --quality preview

# Or switch to reliable ETH canopy data
poetry run python quality_config.py apply standard
```

### Manual Fix:
Edit your `.env` file and change:
```bash
# From problematic source:
CANOPY_HEIGHT_SOURCE=High Resolution 1m Global Canopy Height Maps

# To reliable source:
CANOPY_HEIGHT_SOURCE=ETH Global Sentinel-2 10m Canopy Height (2020)
```

### Alternative: Disable Canopy Data
```bash
# Set to empty to disable canopy data entirely
CANOPY_HEIGHT_SOURCE=
```

---

## 🔍 Error: `cannot access local variable 'land_cover_classes' where it is not associated with a value`

### What it means:
VoxCity library bug with certain land cover data sources, especially ESRI Land Cover.

### Quick Fix:
```bash
# Use PREVIEW quality
poetry run python main.py test --quality preview

# Or apply standard configuration
poetry run python quality_config.py apply standard
```

### Manual Fix:
Edit your `.env` file:
```bash
# From problematic source:
LAND_COVER_SOURCE=ESRI Land Cover

# To reliable source:
LAND_COVER_SOURCE=OpenStreetMap
```

---

## 🔧 General Troubleshooting Steps

### 1. Use Reliable Quality Presets
```bash
# Most reliable (30-60 seconds)
poetry run python main.py test --quality preview

# Balanced and reliable (2-4 minutes)
poetry run python main.py test --quality standard
```

### 2. Validate Installation
```bash
poetry run python setup.py --validate
```

### 3. Check Earth Engine Authentication
```bash
poetry run earthengine authenticate
poetry run earthengine set_project coordinates3d-generator
```

### 4. Reset to Reliable Configuration
```bash
# Apply tested, working configuration
poetry run python quality_config.py apply standard
```

---

## 📊 Reliability Rankings

### Most Reliable Data Sources:
1. **Buildings**: `OpenStreetMap` ✅
2. **Land Cover**: `OpenStreetMap` ✅  
3. **Canopy**: `ETH Global Sentinel-2 10m Canopy Height (2020)` ✅
4. **Terrain**: `FABDEM` ✅

### Problematic Sources to Avoid:
1. **Land Cover**: `ESRI Land Cover` ❌
2. **Canopy**: `High Resolution 1m Global Canopy Height Maps` ❌
3. **Buildings**: `Microsoft Building Footprints` ⚠️ (region-dependent)
4. **Terrain**: `DeltaDTM` ⚠️ (slower, sometimes fails)

---

## 🎯 Recommended Workflow

```bash
# 1. Always start with PREVIEW for testing
poetry run python main.py test --quality preview

# 2. If successful, try STANDARD for production
poetry run python main.py test --quality standard

# 3. For high quality, use PREMIUM (uses reliable sources)
poetry run python main.py <site_id> --quality premium
```

---

## 📞 Getting Help

If you encounter errors not covered here:

1. **Check the error message** for keywords like:
   - `land_cover_classes` → Use OpenStreetMap land cover
   - `image` + `not associated` → Switch canopy source
   - `Earth Engine` → Re-authenticate

2. **Try fallback workflow**:
   ```bash
   poetry run python main.py test --quality preview
   ```

3. **Check project status**:
   ```bash
   poetry run python setup.py --validate
   ```

The system has comprehensive fallback logic that should automatically handle most errors by switching to reliable data sources.
