# 🎨 3D Viewing Tools Guide

Complete guide to viewing and working with your 3D heritage site models.

## 🌐 Online Viewers (Recommended for Quick Preview)

### 1. 3D Viewer (3dviewer.net) ⭐ **Best for Beginners**
- **URL**: https://3dviewer.net/
- **Pros**: Instant viewing, drag & drop, no signup required
- **Cons**: Basic features only
- **How to use**:
  1. Open https://3dviewer.net/
  2. Drag your `.obj` file into the browser
  3. Use mouse to rotate, zoom, pan

**Perfect for:** Quick quality checks, sharing screenshots

### 2. Sketchfab ⭐ **Best for Sharing**
- **URL**: https://sketchfab.com/
- **Pros**: Professional presentation, sharing, annotations
- **Cons**: Requires free account, upload limits
- **How to use**:
  1. Create free account at Sketchfab
  2. Upload your `.obj` file
  3. Configure lighting and materials
  4. Share with UNESCO team

**Perfect for:** Professional presentations, public sharing

### 3. Clara.io
- **URL**: https://clara.io/
- **Pros**: Full 3D editor in browser, collaborative
- **Cons**: Limited free tier, complex interface
- **How to use**:
  1. Sign up for free account
  2. Upload and edit your model
  3. Apply textures and lighting

**Perfect for:** Advanced editing, team collaboration

## 🖥️ Desktop Software

### 1. Blender ⭐ **Best Overall**
```bash
# Install on macOS
brew install --cask blender
```

**Features:**
- ✅ Professional 3D modeling suite
- ✅ Advanced rendering capabilities
- ✅ Animation and simulation
- ✅ Completely free and open source
- ✅ Extensive documentation

**How to import OBJ:**
1. Open Blender
2. Delete default cube (Select > Delete)
3. File > Import > Wavefront (.obj)
4. Navigate to your `output/` folder
5. Select your `.obj` file

**Pro tips:**
- Use `Numpad 7` for top view
- Use `Numpad 1` for front view
- Use `Numpad 3` for side view
- Mouse wheel to zoom
- Middle mouse to rotate

### 2. MeshLab ⭐ **Best for Analysis**
```bash
# Install on macOS
brew install --cask meshlab
```

**Features:**
- ✅ Specialized for 3D mesh analysis
- ✅ Measurement tools
- ✅ Quality assessment
- ✅ Lightweight and fast
- ✅ Academic/research focused

**How to use:**
1. Open MeshLab
2. File > Import Mesh
3. Select your `.obj` file
4. Use View > Show Layer Panel for details

**Perfect for:** Measuring heritage sites, quality analysis

### 3. Rhino 3D (Commercial)
```bash
# 90-day free trial available
# Download from: https://www.rhino3d.com/
```

**Features:**
- ✅ Professional CAD software
- ✅ Precision modeling tools
- ✅ Architectural focus
- ✅ Excellent file format support

**Perfect for:** Architectural analysis, precision work

### 4. macOS Built-in Tools

#### Preview (Basic viewing)
```bash
# Quick preview
open output/Mont-Saint-Michel.obj
```
- ✅ Instant opening
- ✅ Basic rotation and zoom
- ❌ Limited features

#### Finder Quick Look
```bash
# In Finder, select .obj file and press Spacebar
```

## 📱 Mobile Viewing

### iOS Apps
- **MeshLab Mobile** - Free, basic viewing
- **UsdView** - Advanced USD format support
- **3D Viewer** - Simple OBJ viewing

### Android Apps
- **Online 3D Viewer** - Web-based, works in mobile browser
- **Sketchfab** - Mobile app available

## 🎮 VR/AR Viewing

### Desktop VR
1. **Blender VR** - View in virtual reality
2. **SteamVR** - Some 3D viewers support VR
3. **Mozilla Hubs** - Upload for web-based VR

### AR (iOS/Android)
1. Convert OBJ to USDZ format
2. Use AR Quick Look (iOS) or ARCore (Android)
3. Place heritage sites in real world!

## 🔧 Advanced Viewing Techniques

### Material Enhancement in Blender
```python
# Blender Python script for automatic material setup
import bpy

# Set up realistic materials for heritage sites
material = bpy.data.materials.new(name="Stone")
material.use_nodes = True
material.node_tree.nodes["Principled BSDF"].inputs[7].default_value = 0.8  # Roughness
material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.7, 0.6, 0.5, 1.0)  # Stone color
```

### Lighting for Heritage Sites
1. **Sun Lamp** - Simulate natural daylight
2. **Area Lights** - Soft shadows for architecture
3. **HDRI Environment** - Realistic sky lighting

### Camera Angles for Documentation
- **Aerial View** - Overview of site context
- **Ground Level** - Human perspective
- **Detail Shots** - Architectural features
- **Cross Sections** - Internal structure

## 📊 Quality Assessment Tools

### Mesh Analysis in MeshLab
1. **Filters > Quality Measures > Compute Topological Measures**
2. **Filters > Quality Measures > Per Vertex Quality Function**
3. **View > Show Quality Histogram**

### Blender Analysis
1. **Edit Mode > Mesh > Clean Up > Degenerate Dissolve**
2. **Overlays > Mesh Analysis > Check topology**
3. **Statistics panel** for vertex/face count

## 🎨 Rendering for Presentations

### Blender Cycles Rendering
```
# Recommended settings for heritage sites:
- Samples: 1000+ for final renders
- Denoising: OptiX or OpenImageDenoise
- Film > Filter: Blackman-Harris (sharper)
- Color Management: Filmic, High Contrast
```

### Post-Processing
1. **Adobe Photoshop** - Professional editing
2. **GIMP** - Free alternative
3. **Blender Compositor** - Built-in node-based editing

## 📏 Measurement and Documentation

### Measuring in Blender
1. **Add-ons > MeasureIt** - Dimension lines
2. **N Panel > View > Annotations** - Add notes
3. **Units > Metric** - Real-world measurements

### Generating Technical Drawings
1. **Blender FreeStyle** - Line art generation
2. **Orthographic views** - Technical projections
3. **Scale references** - Add human figures, cars

## 🔄 File Format Conversions

### From OBJ to Other Formats
```bash
# Using Blender command line
blender --background --python convert_script.py

# Using MeshLab
meshlabserver -i input.obj -o output.ply
```

### Popular Formats for Heritage Sites
- **PLY** - Point cloud data
- **STL** - 3D printing
- **GLTF** - Web viewing
- **USDZ** - AR viewing (iOS)
- **FBX** - Game engines, Unity

## 💡 Pro Tips

### Performance Optimization
1. **Decimate modifier** in Blender - Reduce polygon count
2. **LOD models** - Multiple detail levels
3. **Texture atlasing** - Combine materials

### Collaboration Workflows
1. **Git LFS** - Version control for large files
2. **Shared cloud storage** - Dropbox, Google Drive
3. **Sketchfab teams** - Online collaboration

### Documentation Standards
1. **Scale bars** - Always include size reference
2. **North arrows** - Orientation reference
3. **Metadata** - Date, coordinates, data sources
4. **Multiple views** - Plan, elevation, perspective

## 🚀 Next Level: Interactive Models

### Web-based 3D Viewers
```html
<!-- Three.js example -->
<script src="https://threejs.org/build/three.min.js"></script>
<script src="https://threejs.org/examples/js/loaders/OBJLoader.js"></script>
```

### Unity/Unreal Integration
1. Import OBJ files
2. Add interactive features
3. VR/AR experiences
4. Educational content

---
*Choose the tool that matches your expertise level and use case. Start with online viewers, then move to desktop software for advanced work.*
