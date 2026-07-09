# Agent Implementation Plan - Phase 1: SAR Data Preprocessing

This plan defines the technical specifications, mathematical operations, and verification checkpoints for implementing Phase 1 (SAR Preprocessing) in Python using Google Earth Engine (GEE).

---

## 1. Objective
Produce normalized, border-noise-cleaned, and speckle-filtered Sentinel-1 GRD backscatter coefficients (VV and VH) in decibel (dB) scale.

---

## 2. Inputs & Outputs

* **Input**: 
  * Sentinel-1 GRD Image (`COPERNICUS/S1_GRD`).
  * Mode: Interferometric Wide (IW).
  * Polarization: Dual-band VV + VH.
* **Output**: 
  * GEE `ee.Image` object with bands `['VV', 'VH', 'angle']`.
  * **Critical Projection Constraint**: The preprocessing stage **must not** call `.reproject()` or `.setDefaultProjection()` unless explicitly required. The native Sentinel-1 projection and scale must be strictly preserved to prevent processing errors and result alterations.

---

## 3. Detailed Algorithmic Steps

### 3.1 Single Source of Truth
* **Constraint**: The existing implementation in [preprocessing.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/preprocessing.py) is the **single source of truth** for this phase.
* **Action**: Refactor or use the code directly. **Do not** rewrite the preprocessing functions or the Refined Lee filter from scratch. Reuse the published implementation exactly to avoid inventing variants.

### 3.2 Border Noise Removal (remove_border_noise)
* Sentinel-1 border noise primarily consists of low-intensity scan-edge artifacts.
* **Action**:
  1. Mask out invalid pixels using the incidence angle. Do not hardcode the IW angle range ($30.6^\circ$ to $45.9^\circ$) in the core function; retrieve it from `config.py` or derive it directly from the image's metadata properties.
  2. The intensity thresholds ($VV \le -30.0\text{ dB}$, $VH \le -35.0\text{ dB}$) are backscatter intensity filters, not border noise filters. Use them only as an optional, secondary constraint to prevent removing valid deep water areas (which naturally exhibit very low backscatter). Rely primarily on the metadata border masks or incidence angle mask.

### 3.3 Radiometric & Geometric Corrections
* GEE's Sentinel-1 collection is already radiometrically calibrated and orthorectified (terrain corrected) using the SRTM DEM.
* **Action**: Document in the code comments why additional manual Range-Doppler Terrain Correction (RDTC) is not required. **Do not** duplicate or write manual terrain correction scripts.

### 3.4 Decibel Conversion & Filtering (refined_lee_filter)
* Filter execution must be carried out in the **linear power domain** to maintain radiometric scaling.
* **Action**: Reuse `refined_lee_filter` in [preprocessing.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/preprocessing.py), which converts to power scale, applies the directional MMSE filter, converts back to dB scale, and preserves the `angle` band.

---

## 4. Quality Control & Assertions

* **Expected Reference Ranges (Not Hard Assertions)**:
  * Because backscatter values can shift based on acquisition conditions (season, wind, water surface roughness, or incidence angle), do not use hard thresholds to halt execution.
  * **Action**: Calculate the spatial mean of backscatter over the reference validation polygons for water and land (defined in `config.py` or training dataset).
  * **Expected range check**:
    * Water reference polygons are expected to exhibit $VV$ around $-15.0\text{ dB}$ or lower, and $VH$ around $-22.0\text{ dB}$ or lower, depending on local conditions.
    * Land reference polygons are expected to exhibit $VV$ around $-10.0\text{ dB}$ or higher.
  * **Logging**: If calculated means fall outside these ranges, log a warning indicating a potential classification variance, but do not stop execution.

* **Hard Failure Check (NaN/Infinity)**:
  * Check that the output image does not contain invalid/NaN pixels. If any are detected, trigger the Checkpoint Failure Policy and stop execution.

---

## 5. Definition of Done (DoD)

- [ ] **All functions implemented**: Preprocessing, border noise removal, and Refined Lee filtering are executed using the single source of truth.
- [ ] **No runtime errors**: Preprocessing runs and compiles without errors.
- [ ] **HTML generated**: Standalone HTML map sheet showing the preprocessed S1 VV overlay is generated, containing:
  * LayerControl
  * Legend
  * Scale Bar
  * North Arrow
  * Coordinate popup
- [ ] **Checkpoint PASS**: Validation reference check is executed and logged (warnings logged if outside expected ranges). No NaN/Inf pixels exist in the final output.
- [ ] **Checkpoint Failure Policy Applied**: Execution stops immediately if NaN/Inf pixels or unhandled runtime errors are encountered.
- [ ] **Report & Logs written**: Preprocessing parameters, metadata angle limits, and processing duration are logged.
- [ ] **Ready for next phase**: Cleaned Sentinel-1 composite is returned as an `ee.Image` stack with projection and scale preserved.
