# 🌍 Regional Optimization Guide

Optimize VoxCity settings for different continents and heritage site types.

## 🗺️ Quick Regional Settings

### 🇪🇺 Europe
```bash
# Best data sources for European heritage sites
BUILDING_SOURCE=EUBUCCO
LAND_COVER_SOURCE=OpenStreetMap
CANOPY_HEIGHT_SOURCE=High Resolution 1m Global Canopy Height Maps
DEM_SOURCE=FABDEM
```

### 🇺🇸 North America
```bash
# Optimized for US/Canada
BUILDING_SOURCE=Microsoft Building Footprints
LAND_COVER_SOURCE=ESRI 10m Annual Land Cover
CANOPY_HEIGHT_SOURCE=High Resolution 1m Global Canopy Height Maps
DEM_SOURCE=USGS 3DEP 1m DEM
```

### 🌏 Asia
```bash
# Best coverage for Asian sites
BUILDING_SOURCE=Overture
LAND_COVER_SOURCE=Dynamic World V1
CANOPY_HEIGHT_SOURCE=High Resolution 1m Global Canopy Height Maps
DEM_SOURCE=FABDEM
```

### 🌍 Africa
```bash
# Reliable sources for African heritage sites
BUILDING_SOURCE=OpenStreetMap
LAND_COVER_SOURCE=ESA World Cover 10m 2021
CANOPY_HEIGHT_SOURCE=ETH Global Sentinel-2 10m
DEM_SOURCE=FABDEM
```

### 🌎 South America
```bash
# Optimized for South American sites
BUILDING_SOURCE=OpenStreetMap
LAND_COVER_SOURCE=Dynamic World V1
CANOPY_HEIGHT_SOURCE=High Resolution 1m Global Canopy Height Maps
DEM_SOURCE=FABDEM
```

### 🇦🇺 Oceania
```bash
# Best for Australia/Pacific islands
BUILDING_SOURCE=Microsoft Building Footprints
LAND_COVER_SOURCE=Dynamic World V1
CANOPY_HEIGHT_SOURCE=High Resolution 1m Global Canopy Height Maps
DEM_SOURCE=Australian 5M DEM  # Australia only
```

## 🏛️ Heritage Site Type Optimization

### Historic City Centers
```bash
# Focus on detailed buildings
BUILDING_SOURCE=EUBUCCO  # Europe
# or Microsoft Building Footprints  # North America
MESH_SIZE_METERS=2
ZONE_SIZE_METERS=1500
```

**Examples:** Prague, Edinburgh, Quebec City

### Archaeological Sites
```bash
# Emphasize terrain and landscape
DEM_SOURCE=USGS 3DEP 1m DEM  # US sites
# or FABDEM  # Global
LAND_COVER_SOURCE=ESA World Cover 10m 2021
MESH_SIZE_METERS=3
ZONE_SIZE_METERS=2000
```

**Examples:** Machu Picchu, Petra, Angkor Wat

### Natural Heritage Sites
```bash
# Prioritize vegetation and topography
CANOPY_HEIGHT_SOURCE=High Resolution 1m Global Canopy Height Maps
DEM_SOURCE=FABDEM
LAND_COVER_SOURCE=Dynamic World V1
MESH_SIZE_METERS=5
ZONE_SIZE_METERS=5000
```

**Examples:** Yellowstone, Great Barrier Reef, Serengeti

### Coastal/Island Sites
```bash
# Capture land-water interface accurately
DEM_SOURCE=DeltaDTM  # Best for coastal areas
LAND_COVER_SOURCE=Dynamic World V1
ZONE_SIZE_METERS=2000  # Capture full island context
```

**Examples:** Mont-Saint-Michel, Galápagos, Venice

### Mountain/Highland Sites
```bash
# High-resolution terrain critical
DEM_SOURCE=USGS 3DEP 1m DEM  # US mountains
# or FABDEM  # Global mountains
MESH_SIZE_METERS=3
ZONE_SIZE_METERS=3000
```

**Examples:** Machu Picchu, Mount Fuji, Dolomites

## 📊 Country-Specific Recommendations

### 🇫🇷 France
```bash
# Excellent data coverage
BUILDING_SOURCE=EUBUCCO
DEM_SOURCE=RGE Alti  # 1m resolution for France
LAND_COVER_SOURCE=OpenStreetMap
```
**Great for:** Palace of Versailles, Mont-Saint-Michel, Carcassonne

### 🇺🇸 United States
```bash
# Best-in-class data sources
BUILDING_SOURCE=Microsoft Building Footprints
DEM_SOURCE=USGS 3DEP 1m DEM
LAND_COVER_SOURCE=ESRI 10m Annual Land Cover
```
**Great for:** Grand Canyon, Yellowstone, Independence Hall

### 🇬🇧 United Kingdom
```bash
# High-quality government data
BUILDING_SOURCE=EUBUCCO
DEM_SOURCE=England 1m Composite DTM  # England only
LAND_COVER_SOURCE=OpenStreetMap
```
**Great for:** Stonehenge, Tower of London, Edinburgh Castle

### 🇯🇵 Japan
```bash
# Specialized Japanese data available
BUILDING_SOURCE=Overture
LAND_COVER_SOURCE=OpenEarthMap Japan  # Japan-specific
CANOPY_HEIGHT_SOURCE=High Resolution 1m Global Canopy Height Maps
```
**Great for:** Mount Fuji, Kyoto temples, Hiroshima

### 🇩🇪 Germany
```bash
# EUBUCCO has excellent German coverage
BUILDING_SOURCE=EUBUCCO
LAND_COVER_SOURCE=OpenStreetMap
DEM_SOURCE=FABDEM
```
**Great for:** Cologne Cathedral, Neuschwanstein, Berlin Museums

### 🇮🇹 Italy
```bash
# Rich architectural heritage
BUILDING_SOURCE=EUBUCCO
LAND_COVER_SOURCE=OpenStreetMap
MESH_SIZE_METERS=2  # High detail for architecture
```
**Great for:** Colosseum, Venice, Florence, Vatican

## 🌐 Data Source Coverage Maps

### EUBUCCO Coverage
- ✅ **Excellent:** Germany, Netherlands, France, UK
- ✅ **Good:** Italy, Spain, Eastern Europe
- ❌ **Not available:** Outside Europe

### Microsoft Building Footprints Coverage
- ✅ **Excellent:** USA, Canada, Australia
- ✅ **Good:** Europe, parts of Asia
- ⚠️ **Limited:** Africa, South America

### USGS 3DEP DEM Coverage
- ✅ **Excellent:** United States (1m resolution)
- ❌ **Not available:** Outside USA

### High Resolution Canopy Height Coverage
- ✅ **Global coverage** (2009-2020 data)
- ✅ **1m resolution worldwide**
- ⚠️ **Data quality varies** by region

## 🎯 Site-Specific Success Stories

### Mont-Saint-Michel, France
```bash
BUILDING_SOURCE=EUBUCCO
MESH_SIZE_METERS=2
ZONE_SIZE_METERS=1000
```
**Result:** Excellent detail of abbey architecture and tidal causeway

### Machu Picchu, Peru
```bash
BUILDING_SOURCE=OpenStreetMap
DEM_SOURCE=FABDEM
MESH_SIZE_METERS=3
ZONE_SIZE_METERS=2000
```
**Result:** Clear terracing and mountain context

### Angkor Wat, Cambodia
```bash
BUILDING_SOURCE=Overture
LAND_COVER_SOURCE=Dynamic World V1
CANOPY_HEIGHT_SOURCE=High Resolution 1m Global Canopy Height Maps
ZONE_SIZE_METERS=3000
```
**Result:** Temple complex with surrounding forest

### Petra, Jordan
```bash
BUILDING_SOURCE=OpenStreetMap
DEM_SOURCE=FABDEM
LAND_COVER_SOURCE=ESA World Cover 10m 2021
MESH_SIZE_METERS=3
```
**Result:** Rocky terrain and carved facades

### Great Wall of China
```bash
BUILDING_SOURCE=OpenStreetMap
DEM_SOURCE=FABDEM
ZONE_SIZE_METERS=5000
MESH_SIZE_METERS=5
```
**Result:** Wall following mountain ridges

## 🚨 Regional Challenges & Solutions

### Europe: Data Richness Overload
**Challenge:** Too many high-quality options
**Solution:** Start with EUBUCCO, fall back to OpenStreetMap

### Africa: Limited Building Data
**Challenge:** Sparse building footprint data
**Solution:** 
```bash
BUILDING_SOURCE=OpenStreetMap
# Use larger mesh size to capture general forms
MESH_SIZE_METERS=5
# Focus on landscape context
ZONE_SIZE_METERS=2000
```

### Remote Islands: Connectivity Issues
**Challenge:** Large data downloads, slow internet
**Solution:**
```bash
# Use faster data sources
CANOPY_HEIGHT_SOURCE=ETH Global Sentinel-2 10m
BUILDING_SOURCE=OpenStreetMap
# Smaller zones
ZONE_SIZE_METERS=500
```

### Mountain Regions: Terrain Accuracy
**Challenge:** Standard DEMs may lack detail
**Solution:**
```bash
# Use highest available DEM resolution
DEM_SOURCE=USGS 3DEP 1m DEM  # US
# or FABDEM  # Global
# Smaller mesh for terrain detail
MESH_SIZE_METERS=2
```

### Urban Heritage: Building Height Accuracy
**Challenge:** Generic building heights
**Solution:**
```bash
# Use AI-derived building heights
BUILDING_SOURCE=Microsoft Building Footprints
# or EUBUCCO  # Europe
# High resolution for architectural detail
MESH_SIZE_METERS=2
```

## 🗺️ Coordinate System Considerations

### Polar Regions
- **Challenge:** Coordinate distortion near poles
- **Solution:** Use smaller zones, verify coordinates

### Pacific Islands
- **Challenge:** Date line crossing
- **Solution:** Ensure coordinates are consistent (all positive or negative longitude)

### Equatorial Regions
- **Advantage:** Minimal coordinate distortion
- **Recommendation:** Standard settings work well

## 📈 Performance by Region

### Fastest Processing Regions
1. **North America** - Excellent data infrastructure
2. **Western Europe** - High-quality preprocessed data
3. **Australia** - Good coverage, less density

### Slower Processing Regions
1. **Dense Asian cities** - High building density
2. **Amazon rainforest** - Complex vegetation
3. **Himalayan regions** - Complex terrain

## 🛠️ Regional Debugging Tips

### Europe
```bash
# If EUBUCCO fails, try OpenStreetMap
BUILDING_SOURCE=OpenStreetMap
```

### North America
```bash
# If USGS DEM unavailable, fallback to FABDEM
DEM_SOURCE=FABDEM
```

### Asia
```bash
# If building data sparse, increase mesh size
MESH_SIZE_METERS=5
```

### Africa
```bash
# Focus on landscape, not buildings
ZONE_SIZE_METERS=2000
MESH_SIZE_METERS=5
```

## 🌍 Climate Zone Considerations

### Tropical Regions
- **High vegetation:** Use high-res canopy data
- **Frequent clouds:** May affect satellite data quality
- **Monsoon areas:** Consider seasonal variations

### Arid Regions
- **Sparse vegetation:** ETH 10m canopy sufficient
- **Clear skies:** Excellent satellite data quality
- **Terrain focus:** Prioritize high-res DEM

### Temperate Regions
- **Balanced approach:** Standard settings work well
- **Seasonal vegetation:** Consider data capture timing
- **Good infrastructure:** Multiple data source options

### Arctic/Antarctic
- **Limited data:** Use OpenStreetMap, FABDEM
- **Coordinate issues:** Verify projection accuracy
- **Simple settings:** Basic resolution sufficient

## 💡 Pro Tips by Region

### European Heritage Sites
- Always try EUBUCCO first for buildings
- Use OpenStreetMap for detailed land cover
- Consider seasonal tourism impact on data

### American Heritage Sites
- Microsoft Building Footprints are very accurate
- USGS DEMs are world-class where available
- State-level data variations exist

### Asian Heritage Sites
- Overture Maps often best for building coverage
- OpenEarthMap Japan excellent for Japanese sites
- Consider monsoon season data artifacts

### African Heritage Sites
- Focus on natural landscape features
- Building data may be incomplete
- FABDEM provides good terrain baseline

### Remote/Island Sites
- Test with small zones first
- May need multiple attempts for data download
- Consider time zone for processing

---
*Remember: These are starting recommendations. Always test and adjust based on your specific heritage site characteristics!*
