# Final Shoreline Extraction Plan (Phase 3 Outline)

This document formalizes the publication-grade pipeline for extracting the Red River shoreline from Sentinel-1 SAR imagery. The pipeline focuses on the **geometric shared boundary between Water and Sand polygons**, ensuring topological correctness and multi-temporal stability.

> [!NOTE]
> **Note on Outputs**: No raster GeoTIFF (.tif) file exports are required for this pipeline. All calculations are executed programmatically, and final outputs are visualized and validated directly via interactive HTML (Folium) maps.

---

## 1. Overall Pipeline Workflow

The pipeline is strictly dedicated to the algorithm for extracting the final shoreline. Comprehensive evaluations, sensitivity studies, and uncertainty analyses are conducted separately in the experimental section of the thesis/paper.

```text
Sentinel-1 GRD
        │
        ▼
SAR Preprocessing
        │
        ▼
Feature Engineering
        │
        ▼
Random Forest Classification
        │
        ▼
Classification Refinement
        │
        ▼
Water–Sand Shared Boundary Extraction
        │
        ▼
Shoreline Graph Cleaning
        │
        ▼
Chaikin Smoothing
        │
        ▼
Douglas–Peucker Simplification
        │
        ▼
Final Quality Control and Shoreline Validation
        │
        ▼
Final Research-Grade Shoreline
```

---

## 2. Phase-by-Phase Technical Specifications & Checkpoints

### Phase 1: SAR Data Preparation (Preprocessing)
Produces normalized, speckle-filtered backscatter coefficients.
* **Sub-phase 1.1: Orbit & Noise Calibration**: Apply Orbit File and perform Thermal Noise Removal to calibrate sub-swaths.
* **Sub-phase 1.2: Border Masking**: Remove low-intensity anomalies at the scan edges.
* **Sub-phase 1.3: Radiometric & Geometric Corrections**:
  * Perform Radiometric Calibration to obtain $\sigma^0$ or $\gamma^0$.
  * Apply Range-Doppler Terrain Correction (RDTC) using DEM to fix geometric layover/foreshortening.
* **Sub-phase 1.4: Decibel Conversion & Filtering**: Convert to dB scale and apply an edge-preserving **Refined Lee Filter (7×7)** to suppress speckle noise without blurring boundaries.
* > **CHECKPOINT 1**: Verify backscatter values over deep water (VV $\le -15\text{ dB}$, VH $\le -22\text{ dB}$). Visually inspect for edge blurring or sub-swath stitching errors.

### Phase 2: Feature Engineering (Feature Stack)
Constructs a 10–12 band stack to improve land-cover separability.
* **Sub-phase 2.1: Derived Polarizations**:
  * Polarizations: $VV$, $VH$.
  * Arithmetic Bands: $VV_{\text{ratio}} = VV_{\text{dB}} - VH_{\text{dB}}$ (representing the linear ratio $VV/VH$ in log-scale), $VV + VH$, and $\text{Mean}(VV, VH)$.
* **Sub-phase 2.2: GLCM Texture Analysis** (5×5 or 7×7 window):
  * Contrast, Entropy, Homogeneity, Correlation, ASM, and Variance.
* > **CHECKPOINT 2**: Verify there are no NaN or Inf values in the derived band layers. Ensure GLCM Contrast accurately highlights land/water and sandbar boundaries.

### Phase 3: Random Forest Classification
Classifies the feature stack into five key surface classes.
* **Sub-phase 3.1: Land Cover Classes**:
  * Water, Sand, Vegetation, Built-up, and Others.
* **Sub-phase 3.2: Sampling Strategy**:
  * **Calibration Baseline**: Training and validation samples will be collected and calibrated using the **2024 Dry and Wet season composites first** to establish a robust model baseline before scaling to other years.
  * Balanced stratified sampling (70/30 Train/Test split) and independent polygon-based validation.
* > **CHECKPOINT 3**: Report per-class Precision, Recall, and F1-score for all classes, with a particular focus on the dynamic Sand class (target F1-score for Sand $\ge 75\%$, calibrated empirically). Relying solely on Overall Accuracy (OA) or Kappa coefficient is avoided since easier classes (Water, Vegetation) skew results.

### Phase 4: Classification Refinement
Post-processes the raster mask to isolate clean water/sand corridors.
* **Sub-phase 4.1: Pixel Filtering**: Apply a Majority Filter to clear out isolated salt-and-pepper noise.
* **Sub-phase 4.2: Morphological Operations**: Apply morphological filtering using a **disk-shaped structuring element** (to ensure isotropic shape preservation and prevent orientation bias):
  * **Morphological Opening (Disk radius = 2 pixels / 20m)**: Breaks thin artificial bridges, removes small noise components, and disconnects irrelevant channels.
  * **Morphological Closing (Disk radius = 3 pixels / 30m)**: Fills micro-holes, ponds, or small sand cracks inside larger features.
* **Sub-phase 4.3: Connected Components**: Keep only the main river channel corridor:
  * Identify the connected component representing the active Red River corridor using connectivity and spatial constraints.
  * Optionally retain secondary channel components if they intersect within a maximum distance (e.g., 500m) of the digitized river centerline.
  * Eliminate all other disconnected waterbodies (such as inland aquaculture ponds, urban lakes, and minor agricultural canals) that do not belong to the active river system.
* > **CHECKPOINT 4**: Verify that the water component count dropped by $\ge 95\%$. Visually inspect that inland lakes/ponds outside the dykes are completely masked.

### Phase 5: Water–Sand Shared Boundary Extraction
Extracts the raw shoreline interface while preventing topological artifacts.
* **Sub-phase 5.1: Polygonization**: Convert the refined Water and Sand raster classes into vector polygons.
* **Sub-phase 5.2: Main Corridor Extraction**: Extract the shared boundary line strictly at the interface touching the main river corridor:
  $$\text{Shoreline} = \partial(\text{Main\_River\_Water\_Polygon}) \cap \partial(\text{Sand\_Polygon})$$
  * This topological filter extracts **only** the water-sand interfaces touching the main river channel. It discards isolated sandbar boundaries, internal holes (lake boundaries/polygon rings) inside sandbars, and island boundaries that do not connect to the main river flow.
* > **CHECKPOINT 5**: Ensure no closed loops or boundaries are generated along concrete embankments, vegetated banks, or inland ponds that do not contain sand.

### Phase 6: Shoreline Cleaning (Graph Optimization)
Fixes topological flaws in the vector lines.
* **Sub-phase 6.1: Graph Assembly**: Convert polylines into a network graph.
* **Sub-phase 6.2: Pruning**: Delete dead-end spurs and collapse closed loops.
* **Sub-phase 6.3: Network Merging**: Keep the longest connected network and snap adjacent endpoints to bridge gaps.
* > **CHECKPOINT 6**: Rather than selecting fixed thresholds (like pruning spurs $< 500\text{ m}$ or snapping $< 150\text{ m}$) arbitrarily, **parameters must be determined through empirical calibration using validation reaches or optimized via sensitivity analysis (grid search)**. Verify that the number of disconnected shoreline segments is minimized (ideally $\le 5$ segments total).

### Phase 7: Shoreline Smoothing & Simplification
Smooths and simplifies the lines for visualization and vector optimization.
* **Sub-phase 7.1: Chaikin Smoothing**:
  * Apply **Chaikin Smoothing** (2–3 iterations of corner-cutting to round pixelated corners) **BEFORE** applying **Douglas-Peucker Simplification**.
  * *Rationale*: Chaikin increases vertex density by interpolating and rounding the pixelated staircase steps of the raster-derived polyline. Douglas-Peucker (DP) is subsequently applied to reduce the vertex count by removing redundant collinear vertices along the smoothed path. This sequence ensures a physically plausible, curved shoreline without losing geometric shape.
* **Sub-phase 7.2: Douglas-Peucker Simplification**: Apply DP simplification with a small tolerance (2–5 m) to optimize vertex density.
* > **CHECKPOINT 7**: Confirm vertex count reduction of $\ge 60\%$ while keeping the maximum Hausdorff deviation between raw and smoothed lines approximately one pixel ($\approx 10\text{ m}$).

### Phase 8: Final Quality Control and Shoreline Validation
Verifies the final outputs against reference data using quantitative spatial metrics.
* **Sub-phase 8.1: Visual Overlay Check**: Overlay shorelines on the raw SAR composite and cloud-free Sentinel-2 imagery.
* **Sub-phase 8.2: Validation Metrics**: Compute shoreline-specific positional accuracy against high-resolution reference shorelines:
    * **Mean Distance**: Average offset between extracted and reference shorelines.
    * **Root Mean Square Error (RMSE)**: Standard metric for boundary offset variance.
    * **Hausdorff Distance**: Measures the maximum local deviation.
    * **95th Percentile Distance**: Represents the upper bound of positional error.
* **Sub-phase 8.3: Manual Quality Control (Interactive Overlay Sheet)**:
  * **Interactive Map Sheet (Leaflet/Folium)**:
    * Backgrounds: True-color optical (S2) and raw greyscale SAR ($VV$).
    * Opacity-controlled Classification Raster layer.
    * Line overlays: Raw unsmoothed boundary (red dashed) and smoothed final bank lines (green/cyan).
  * **Inspection Routine**:
    * Scan downstream from Son Tay to Phu Xuyen at zoom levels 14–16.
    * Pay special attention to bridge crossings (Japan, Thang Long, Chuong Duong) and active mid-channel sandbars.
    * If systematic errors exceed $30\text{ m}$, log coordinates, adjust snap/pruning parameters, add training samples, and retrain the classifier.

---

## 3. Thesis/Paper Structure: Chapter 4 – Experimental Evaluation

To maintain a clean separation between the core algorithm and its validation, the following analyses are moved to the experimental evaluation chapter of the thesis/paper:

### 4.1 Classification Accuracy
* Report 5-fold cross-validation results.
* Run the Random Forest model across 10 random seeds to calculate the Mean and Standard Deviation (Std) of Overall Accuracy, Precision, Recall, and F1-score (especially for the Sand class) to quantify model stability and classification uncertainty.

### 4.2 Shoreline Positional Accuracy
* Document Mean Distance, RMSE, Hausdorff Distance, and 95th Percentile metrics for the final extracted shorelines against high-resolution reference shorelines.

### 4.3 Parameter Sensitivity Analysis
* Justify pipeline parameter selections through grid search experiments:
  * Lee filter kernel size (5×5, 7×7, 9×9)
  * GLCM window size (3×3, 5×5, 7×7)
  * Graph snapping distance (50m, 100m, 150m)
  * Morphological opening and closing disk radii (e.g., 1–4 pixels)
* Quantify the resulting shoreline RMSE against reference validation reaches to identify the optimal parameter configuration.

### 4.4 Ablation Study
* Quantify the incremental improvements from each post-processing stage (Morphological Filters, Connected Component Corridor Extraction, Graph Cleaning, Smoothing) to verify their impact on topological correctness.

### 4.5 Multi-temporal Shoreline Analysis
* Evaluate shorelines extracted across different years (2020, 2021, 2022, 2023, 2024) to analyze historical morphological shifts and seasonal dynamics (Dry vs. Wet composites).
* Validate findings against gauge hydrological records (water levels and discharge rates).
