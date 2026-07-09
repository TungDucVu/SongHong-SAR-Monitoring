# Agent Implementation Plan - Phase 3: Random Forest Classification

This plan defines the technical specifications, mathematical operations, and verification checkpoints for implementing Phase 3 (Random Forest Classification) in Python using Google Earth Engine (GEE).

---

## 1. Objective
Train a Random Forest classifier using GEE and classify the 10–12 band feature stack into five land-cover classes (Water, Sand, Vegetation, Built-up, Others).

---

## 2. Inputs & Outputs

* **Input**: 
  * Feature stack GEE Image from Phase 2.
  * Training Polygons GeoJSON/Asset (`training_polygons.geojson`).
  * 2024 Dry and Wet season composites (for baseline calibration).
* **Output**: 
  * Classified raster GEE Image with values `[1, 2, 3, 4, 5]`.
  * Classification assessment metrics (Precision, Recall, F1-score per class, with focus on Sand).

---

## 3. Detailed Algorithmic Steps

### 3.1 Class definitions
* 1: **Water** (Rivers, channels)
* 2: **Sand** (Bại cát, sandbars, dry and wet sands)
* 3: **Vegetation** (Agriculture, trees, bushes)
* 4: **Built-up** (Cities, bridges, roads)
* 5: **Others** (Bare soil, shadows, etc.)

### 3.2 Calibration Baseline
* **Action**: Prioritize training on the **2024 Dry and Wet season composites** first to establish a robust model baseline.
  1. Load the 2024 Dry and Wet composites.
  2. Extract pixel values intersecting with `training_polygons.geojson` polygons.

### 3.3 Sampling Strategy
* **Stratified Sampling**: Ensure balanced representation of all 5 classes.
* **Train/Test Split**: 
  * Split training samples into 70% for model training and 30% for independent testing.
  * Split should be done at the polygon/group level (spatial block split) where possible to avoid spatial autocorrelation biasing the test scores.

### 3.4 Model Training
* Train `ee.Classifier.smileRandomForest` with parameter:
  * `numberOfTrees`: 200 (defined as `RF_NUM_TREES` in `src/config.py`).
  * Feature variables: All bands in the stack.

---

## 4. GEE/Python Implementation Details

* Use `image.sampleRegions()` to extract GEE feature tables from training polygons.
* Save the trained classifier GEE object or model parameters so that it can be applied to other years (2015-2024).
* Apply classification:
  `classified = image.select(features).classify(trained_rf)`

---

## 5. Quality Control & Checkpoints

* **Avoid Over-Reliance on OA/Kappa**: Do not rely on Overall Accuracy or Kappa coefficient, as they are skewed by the easily classified classes (Water, Vegetation).
* **Per-Class Metrics Check**:
  * Extract the confusion matrix from the 30% test split.
  * Calculate **Precision**, **Recall**, and **F1-score** for each class.
  * **F1-score for Sand Class MUST be $\ge 75\%$**. If it is lower, inspect confusion matrix for mixing (typically between Sand and Built-up or Bare Soil) and add targeted training polygons.
* **Visual Inspection**: Ensure bridge structures (built-up) are not misclassified as sand, and sandbars are not completely missed.

---

## 6. Definition of Done (DoD)

- [ ] **All functions implemented**: Random forest training, feature sampling, and image classification are fully written.
- [ ] **No runtime errors**: Scripts run and complete without GEE query execution errors.
- [ ] **HTML generated**: Standalone HTML map sheet showing the classification raster overlay is generated, containing:
  * LayerControl
  * Legend (showing color blocks for all 5 land cover classes)
  * Scale Bar
  * North Arrow
  * Coordinate popup
- [ ] **Checkpoint PASS**: Test split evaluation calculates precision, recall, and F1-score for each class. F1-score for Sand is $\ge 75\%$.
- [ ] **Checkpoint Failure Policy Applied**: If the F1-score for Sand is below $75\%$, execution stops immediately and writes a failure log.
- [ ] **Report & Logs written**: Accuracy metrics (Mean & Std over 10 seeds / 5-fold CV) and parameters (trees, bands used) are saved to log files.
- [ ] **Ready for next phase**: Classified image is ready as a GEE `ee.Image` or local NumPy array.
