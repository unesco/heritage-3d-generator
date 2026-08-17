# ☀️ Analysis Layers

> Every generated model ships with **environmental simulation layers** —
> because a heritage digital twin should be *useful*, not just beautiful.

Computed automatically by `analysis.py` at the end of each site generation
(on by default; skip with `--no-analysis`). Failures are logged and never
fatal to the pipeline.

## 📊 The four layers

| Layer | Files | Units | What it tells you |
|-------|-------|-------|-------------------|
| ☀️ **Solar irradiance — solstice noon** | `solar_solstice_noon.png/.npz` | W/m² (instantaneous) | Sun exposure at Jun 21 12:00 — shading of facades & ground |
| 📆 **Solar irradiance — solstice day** | `solar_solstice_day.png/.npz` | Wh/m²·day (cumulative) | Total daily solar potential, Jun 21 05:00–21:00 |
| 🌳 **Green View Index (GVI)** | `green_index.png/.npz` | 0–1 | Share of the pedestrian's view occupied by vegetation |
| 🌤️ **Sky View Index (SVI)** | `sky_index.png/.npz` | 0–1 | Sky openness from ground level (canyon effect) |

All layers are computed on the voxel grid at **1.5 m viewpoint height**
(pedestrian level). Solar simulations account for tree transmittance
(`tree_k=0.6`, `tree_lad=1.0`).

## 🌦️ Weather data (EPW)

Solar layers use the **nearest EPW weather file**, auto-downloaded from the
Ladybug Tools / EnergyPlus database (`download_nearest_epw=True`). The EPW
file and its metadata JSON are cached in `output/` for reuse.

## 🗺️ Outputs

- **PNG** — color-mapped map with colorbar, ready for reports and slides
- **NPZ** — raw numpy grid (`np.load(...)["grid"]`) for your own analysis:

```python
import numpy as np
import matplotlib.pyplot as plt

solar = np.load("output/whc/252_taj_mahal/solar_solstice_day.npz")["grid"]
gvi   = np.load("output/whc/252_taj_mahal/green_index.npz")["grid"]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].imshow(solar, cmap="magma"); axes[0].set_title("☀️ Wh/m²·day")
axes[1].imshow(gvi, cmap="viridis", vmin=0, vmax=1); axes[1].set_title("🌳 GVI")
plt.show()
```

## 🎯 Use cases

- ☀️ **Solar potential** — where could panels go without harming the site?
- 🌡️ **Heat-stress hotspots** — exposed plazas vs shaded courtyards
- 🌳 **Greenery & wellbeing** — GVI is a standard urban-forestry metric
- 🌤️ **Daylight & ventilation** — SVI reveals canyon effects in dense historic centres
- 🧪 **Microclimate pre-screening** — pick sub-zones before full ENVI-met runs

## ⚠️ Known caveats

- **Dense-canopy natural sites** (e.g. Mount Olympus): ground-level solar maps
  are near-black — physically correct forest shade, but low information.
  Look at canopy-top values in the `.npz` instead.
- **Solstice-only**: layers are computed for Jun 21 (northern summer). For
  southern-hemisphere sites this is *winter* — interpret accordingly, or
  recompute with a different date by editing `SOLSTICE` / `SOLSTICE_DAY`
  in `analysis.py`.
- Voxel resolution (3 m at PREMIUM) smooths fine facade details; irradiance
  values are grid-averaged.

## 🔁 Recomputing for existing sites

Without re-generating the models (uses VoxCity's disk cache):

```bash
poetry run python backfill_analysis.py
```

Skip analysis during generation (faster pilot runs):

```bash
poetry run python main.py whc:274 --no-analysis
poetry run python batch.py --pilot --no-analysis
```

---

*Back to [Wiki Home](README.md)*
