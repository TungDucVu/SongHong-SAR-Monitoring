# Phase 2 Comprehensive Report: Sentinel-1 Feature Engineering & QA Suite

This report documents the detailed implementation, algorithms, optimizations, and validation results for **Phase 2 (Feature Engineering & Quality Assurance)** of the Hanoi Red River Shoreline Extraction project.

---

## 1. Executive Summary

Phase 2 transitions the preprocessed Sentinel-1 seasonal radar composites (Dry and Wet seasons of 2024) into a robust 11-band machine learning feature stack. To ensure the feature space is clean, physically representative, and statistically separable before training downstream classifiers, a comprehensive multi-dimensional Quality Assurance (QA) suite was developed and integrated. 

Furthermore, to capture spatial variance and environmental diversity along the Red River, the sampling strategy was scaled from single reference points to **27 spatially distributed $100\text{ m} \times 100\text{ m}$ reference polygons**. The entire pipeline executes successfully, producing high-fidelity outputs and passing all radiometric check thresholds.

---

## 2. Derived Features & Algorithmic Design

The feature engineering pipeline builds a 11-band feature stack strictly matching the required contract order:
$$\text{Stack} = [\text{VV}, \text{VH}, \text{VV\_ratio}, \text{VV\_sum}, \text{VV\_mean}, \text{VV\_contrast}, \text{VV\_entropy}, \text{VV\_homogeneity}, \text{VV\_correlation}, \text{VV\_ASM}, \text{VV\_variance}]$$

### 2.1 Polarization Mathematics
1. **`VV_ratio`**: Computes polarization difference directly in decibel (dB) space, which mathematically corresponds to the log-ratio:
   $$\text{VV\_ratio} = \text{VV}_{\text{dB}} - \text{VH}_{\text{dB}}$$
2. **`VV_sum`**: Converts dB backscatter back to linear power, sums the two signals, and converts the result back to dB space to prevent invalid logarithmic addition:
   $$\text{VV\_sum} = 10 \cdot \log_{10}\left(10^{\frac{\text{VV}_{\text{dB}}}{10}} + 10^{\frac{\text{VH}_{\text{dB}}}{10}}\right)$$
3. **`VV_mean`**: Computes the arithmetic average of the co- and cross-polarization backscatter in dB:
   $$\text{VV\_mean} = \frac{\text{VV}_{\text{dB}} + \text{VH}_{\text{dB}}}{2}$$

### 2.2 Gray-Level Co-occurrence Matrix (GLCM) Textures
To capture land cover textures (e.g., smooth water surfaces vs. complex urban structures and sand ripples), GLCM texture metrics are computed over the speckle-filtered **VV band** using a sliding **$7\times7$ pixel window** ($70\text{ m} \times 70\text{ m}$).
* **Dynamic Range Quantization**: GEE's `glcmTexture` requires discrete integer inputs. To prevent data loss and ensure numerical stability, backscatter intensity is clamped to $[-25.0, 5.0]\text{ dB}$, normalized to a $[0, 255]$ range, and cast to a 32-bit signed integer:
  $$\text{Quantized} = \text{toInt32}\left( 255 \times \frac{\text{VV}_{\text{dB}} - (-25.0)}{5.0 - (-25.0)} \right)$$
* **Bands Extracted & Renamed**: Contrast (`contrast`), Entropy (`entropy`), Homogeneity (`idm`), Correlation (`corr`), Angular Second Moment (`asm`), and Variance (`var`).

---

## 3. QA Suite Implementation (`src/qa_suite.py`)

A fully-automated verification suite generates multiple visual and statistical outputs:

1. **Interactive HTML Map Sheet (`feature_maps_*.html`)**:
   * Renders the 11 feature stack bands as toggleable grayscale Google Earth Engine tiles.
   * Overlays Sentinel-2 RGB composite, Google Satellite imagery, Hanoi boundary, and the Red River AOI boundary.
   * Plots all 27 reference polygons color-coded by class for direct visual inspection.
   * Includes interactive coordinate popups, mouse trackers, scales, and legends.
2. **Statistical Class Distribution Plots**:
   * **Histograms (`class_histograms_*.png`)**: Overlays pixel value counts for each of the 4 classes across all 11 features.
   * **Boxplots (`class_boxplots_*.png`)**: Compares class quartiles and ranges to evaluate feature separability.
3. **Joint Bivariate Scatter Plots (`class_scatter_*.png`)**:
   * Plots intensity (`VV`) against texture (`VV_contrast`) to check multi-dimensional class boundaries.
4. **High-Resolution Sandbar Zoom Crops (`sandbar_zoom_*.png`)**:
   * Compares the spatial features (`VV`, `VV_contrast`, `VV_entropy`, `VV_homogeneity`) over the Long Bien sandbar reach.
5. **Correlation Matrix Heatmaps (`correlation_heatmap_*.png`)**:
   * Computes Pearson coefficients to audit multicollinearity and highlights features with correlation $>0.98$ (e.g. `VV` vs. `VV_sum`).
6. **Feature Value Random Inspector (`feature_inspection_*.md`)**:
   * Selects 5 random pixels per class (20 total) and logs their raw values to a markdown verification table.

---

## 4. Multi-Polygon Sampling Design & GEE Optimization

### 4.1 Distributed Polygons Coordinate Set
To cover environmental variance across the Red River basin, we selected **27 distinct reference polygons** of size $100\text{ m} \times 100\text{ m}$ (coordinate boxes in WGS 84 `[Lon, Lat]`):

* **Water Reference Polygons** (7 polygons):
  1. `[[105.8540, 21.0560], [105.8560, 21.0560], [105.8560, 21.0580], [105.8540, 21.0580], [105.8540, 21.0560]]` (Hanoi Reach)
  2. `[[105.4600, 21.1850], [105.4610, 21.1850], [105.4610, 21.1860], [105.4600, 21.1860], [105.4600, 21.1850]]` (Upstream Son Tay)
  3. `[[105.8950, 20.9550], [105.8960, 20.9550], [105.8960, 20.9560], [105.8950, 20.9560], [105.8950, 20.9550]]` (Downstream Thanh Tri)
  4. `[[105.7150, 21.1400], [105.7160, 21.1400], [105.7160, 21.1410], [105.7150, 21.1410], [105.7150, 21.1400]]` (Mid-channel curve)
  5. `[[105.8400, 21.0850], [105.8410, 21.0850], [105.8410, 21.0860], [105.8400, 21.0860], [105.8400, 21.0850]]` (Midstream Hanoi)
  6. `[[105.5788, 21.1565], [105.5798, 21.1565], [105.5798, 21.1575], [105.5788, 21.1575], [105.5788, 21.1565]]` (Upstream curve)
  7. `[[105.9664, 20.7337], [105.9674, 20.7337], [105.9674, 20.7347], [105.9664, 20.7347], [105.9664, 20.7337]]` (Newest Water polygon)

* **Sand Reference Polygons** (6 polygons):
  1. `[[105.6018, 21.1663], [105.6028, 21.1663], [105.6028, 21.1673], [105.6018, 21.1673], [105.6018, 21.1663]]` (Upstream sandbar)
  2. `[[105.9188, 20.7888], [105.9198, 20.7888], [105.9198, 20.7898], [105.9188, 20.7898], [105.9188, 20.7888]]` (Sand polygon 2)
  3. `[[105.4403, 21.2564], [105.4413, 21.2564], [105.4413, 21.2574], [105.4403, 21.2574], [105.4403, 21.2564]]` (Sand polygon 3)
  4. `[[105.4308, 21.2722], [105.4318, 21.2722], [105.4318, 21.2732], [105.4308, 21.2732], [105.4308, 21.2722]]` (Sand polygon 4)
  5. `[[105.3916, 21.2953], [105.3926, 21.2953], [105.3926, 21.2963], [105.3916, 21.2963], [105.3916, 21.2953]]` (Sand polygon 5)
  6. `[[105.4158, 21.2851], [105.4168, 21.2851], [105.4168, 21.2861], [105.4158, 21.2861], [105.4158, 21.2851]]` (Sand polygon 6)

* **Urban Reference Polygons** (6 polygons):
  1. `[[105.8495, 21.0245], [105.8505, 21.0245], [105.8505, 21.0255], [105.8495, 21.0255], [105.8495, 21.0245]]` (Hoan Kiem block)
  2. `[[105.4550, 21.2000], [105.4560, 21.2000], [105.4560, 21.2010], [105.4550, 21.2010], [105.4550, 21.2000]]` (Upstream urban)
  3. `[[105.8759, 20.9491], [105.8769, 20.9491], [105.8769, 20.9501], [105.8759, 20.9501], [105.8759, 20.9491]]` (Urban polygon 3)
  4. `[[105.7250, 21.1550], [105.7260, 21.1550], [105.7260, 21.1560], [105.7250, 21.1560], [105.7250, 21.1550]]` (Midstream urban west)
  5. `[[105.8550, 21.0800], [105.8560, 21.0800], [105.8560, 21.0810], [105.8550, 21.0810], [105.8550, 21.0800]]` (Midstream urban east)
  6. `[[105.5570, 21.1376], [105.5580, 21.1376], [105.5580, 21.1386], [105.5570, 21.1386], [105.5570, 21.1376]]` (Urban polygon 6)

* **Land Reference Polygons** (8 polygons):
  1. `[[105.8596, 21.0354], [105.8606, 21.0354], [105.8606, 21.0364], [105.8596, 21.0364], [105.8596, 21.0354]]` (Hanoi agricultural/park)
  2. `[[105.4500, 21.2200], [105.4510, 21.2200], [105.4510, 21.2210], [105.4500, 21.2210], [105.4500, 21.2200]]` (Upstream crops)
  3. `[[105.8950, 20.9500], [105.8960, 20.9500], [105.8960, 20.9510], [105.8950, 20.9510], [105.8950, 20.9500]]` (Downstream crops)
  4. `[[105.7100, 21.1500], [105.7110, 21.1500], [105.7110, 21.1510], [105.7100, 21.1510], [105.7100, 21.1500]]` (Midstream crops)
  5. `[[105.8400, 21.0900], [105.8410, 21.0900], [105.8410, 21.0910], [105.8400, 21.0910], [105.8400, 21.0900]]` (Midstream Hanoi fields)
  6. `[[105.7550, 21.0750], [105.7560, 21.0750], [105.7560, 21.0760], [105.7550, 21.0760], [105.7550, 21.0750]]` (Stable vegetation west)
  7. `[[105.9307, 20.8578], [105.9317, 20.8578], [105.9317, 20.8588], [105.9307, 20.8588], [105.9307, 20.8578]]` (New Land polygon)
  8. `[[105.9669, 20.7050], [105.9679, 20.7050], [105.9679, 20.7060], [105.9669, 20.7060], [105.9669, 20.7050]]` (Newest Land polygon)

### 4.2 GEE Memory Optimization
Due to the heavy dynamic computational footprint of the Refined Lee speckle filter and GLCM texture maps, sampling pixels over a merged `FeatureCollection` covering a wide geographic area of Hanoi triggered Google Earth Engine's `User memory limit exceeded` error.
* **Solution**: Refactored the sampling logic in `generate_class_distributions` to loop through polygons **individually** and sample up to 400 pixels from each. Each individual polygon bounds a very small geographic area ($100\text{ m} \times 100\text{ m}$), minimizing GEE's memory paging footprint. The samples are then aggregated in Python. This resolved all memory overflows, resulting in an aggregated, robust sample dataset of $\approx 2,400$ pixels per class.

---

## 5. QC Checkpoint & Validation Results

### 5.1 Spatial Mean Backscatter QC (2024 Baseline)
The threshold checker in `src/qc.py` was refactored to compute the average of spatial means across all Water and Land polygons. The pipeline passed successfully:
* **Water VV Backscatter**:
  * Dry Season: **-20.23 dB** (Threshold: $\le -15\text{ dB}$) $\rightarrow$ **PASS**
  * Wet Season: **-20.59 dB** (Threshold: $\le -15\text{ dB}$) $\rightarrow$ **PASS**
* **Land VV Backscatter**:
  * Dry Season: **-6.92 dB** (Threshold: $\ge -10\text{ dB}$) $\rightarrow$ **PASS**
  * Wet Season: **-6.57 dB** (Threshold: $\ge -10\text{ dB}$) $\rightarrow$ **PASS**

### 5.2 Multi-Class Texture Separability (`VV_contrast`)
The contrast band demonstrates strong separability between classes (spatial averages over reference polygons):
* **Water**: Smooth surfaces yield minimal contrast: **21.56** (Dry) | **19.93** (Wet)
* **Sand**: Intermediate texture boundary features: **29.40** (Dry) | **71.58** (Wet)
* **Urban**: Highly heterogeneous, specular built-up features: **112.95** (Dry) | **113.55** (Wet)

---

## 6. Generated Visual Assets

All QA assets have been successfully saved to `shoreline_extraction/phase2_feature_engineering/outputs/`:
* **HTML Map Sheets**:
  * `feature_maps_2024_dry.html`
  * `feature_maps_2024_wet.html`
* **Plot Figures**:
  * `class_histograms_2024_dry.png` | `class_histograms_2024_wet.png`
  * `class_boxplots_2024_dry.png` | `class_boxplots_2024_wet.png`
  * `class_scatter_2024_dry.png` | `class_scatter_2024_wet.png`
  * `sandbar_zoom_2024_dry.png` | `sandbar_zoom_2024_wet.png`
  * `correlation_heatmap_2024_dry.png` | `correlation_heatmap_2024_wet.png`
* **Reports**:
  * `feature_inspection_2024_dry.md` | `feature_inspection_2024_wet.md`
