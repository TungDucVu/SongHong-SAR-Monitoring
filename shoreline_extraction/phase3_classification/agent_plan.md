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
  * Maximum class probability map (values `[0.0 - 1.0]`, representing classifier confidence/probability of the winning class).
  * Classification assessment metrics (Precision, Recall, F1-score per class, full Confusion Matrix).
  * Feature Importance ranking (numerical scores for all bands).

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

### 3.4 Model Training & Tuning
* **Reproducibility**: Use a set of explicit, predefined random seeds (e.g., `[42, 52, 62, 72, 82]`) to run model training iterations.
* **Sequential Hyperparameter Tuning**: To avoid computationally expensive full grid searches in GEE, optimize parameters sequentially:
  * **Stage 1 (Trees)**: Tune `numberOfTrees` over `[100, 200, 300]` (keeping other parameters at GEE defaults). Select the best configuration based on validation F1-score.
  * **Stage 2 (Split Variables)**: Tune `variablesPerSplit` (e.g., GEE default vs. alternative values) using the best number of trees from Stage 1.
  * **Stage 3 (Bag Fraction / Leaf Size)**: Tune `bagFraction` (e.g., `[0.5, 0.7, 1.0]`) or `minLeafPopulation` using the settings from Stages 1 and 2.
* Train the final `ee.Classifier.smileRandomForest` using the sequentially selected optimal hyperparameters.

---

## 4. GEE/Python Implementation Details

* Use `image.sampleRegions()` to extract GEE feature tables from training polygons.
* **Feature Importance**: Retrieve feature importance rankings using `.explain()` on the trained GEE classifier object. Save these scores (e.g., for VV, VH, VV_ratio, VV_contrast, etc.) as a text report and/or plot to verify feature utility.
* **Probability Map**: Generate a **Maximum Class Probability Map** (values ranging from 0.0 to 1.0) representing the classifier's confidence/probability for the predicted winning class. This is critical for QC'ing borderline/uncertain areas.
* Apply classification:
  * Hard labels: `classified = image.select(features).classify(trained_rf)`
  * Probability/confidence: Generate the maximum probability value across all classes (e.g., by running classification in `'PROBABILITY'` mode or getting class probability list outputs and selecting the max value).

---

## 5. Quality Control & Checkpoints

* **Avoid Over-Reliance on OA/Kappa**: Do not rely on Overall Accuracy or Kappa coefficient, as they are skewed by the easily classified classes (Water, Vegetation).
* **Per-Class Metrics & Confusion Matrix**:
  * Extract the 5x5 Confusion Matrix from the 30% test split.
  * Calculate **Precision**, **Recall**, and **F1-score** for each class.
  * **No Hard F1 Threshold**: Do not abort/stop the pipeline based on an arbitrary F1 score threshold (e.g., Sand F1 $\ge 75\%$). F1 values are highly dependent on seasonal features, polygon selection, and model tuning.
  * **Error Analysis**: If performance for Sand or any other class is low, inspect the saved Confusion Matrix to identify which classes are being confused (e.g., Sand mixed with Built-up or Bare Soil). Use this insight to adjust feature bands or add targeted training polygons, but continue running the pipeline.
* **Visual Inspection**: Ensure bridge structures (built-up) are not misclassified as sand, and sandbars are not completely missed. Check the classification probability map to identify areas of low certainty.
* **Post-Classification QC & Area Statistics Sanity Check**:
  * Calculate the percentage of the total AOI area occupied by each of the 5 classes:
    * **Water** (Expected baseline: ~32%)
    * **Sand** (Expected baseline: ~11%)
    * **Vegetation**
    * **Built-up** (Expected baseline: ~14%)
    * **Others**
  * If the classified area statistics differ dramatically from realistic baselines (e.g., Sand class exceeds 40-45% of the total AOI), this flags an obvious classification failure. Log this anomaly clearly in the pipeline run output so that the user is alerted to inspect the training polygons or feature stacks.

---

## 6. Definition of Done (DoD)

- [x] **All functions implemented**: Random forest training, sequential hyperparameter tuning, feature sampling, feature importance extraction, and image classification/maximum probability mapping are fully written.
- [x] **No runtime errors**: Scripts run and complete without GEE query execution errors.
- [x] **HTML generated**: Standalone HTML map sheet showing the classification raster overlay is generated, containing:
  * LayerControl
  * Legend (showing color blocks for all 5 land cover classes)
  * Scale Bar
  * North Arrow
  * Coordinate popup
- [x] **Report & Logs written**: 
  * Accuracy metrics (Precision, Recall, F1 per class, and the full 5x5 Confusion Matrix) saved to files.
  * Feature Importance scores saved as a ranking table.
  * Optimal hyperparameters and random seeds logged.
  * Area statistics (percentage coverage per class) computed and logged.
- [x] **Ready for next phase**: Classified image and maximum class probability map are ready as GEE `ee.Image` objects or local datasets.

---

## 7. Optimized Hyperparameters & Results (2024 Final)

Following a series of experiments (renaming classes, updating training polygons to 4 target classes: Water, Sand, Built-up, Vegetation, 70/30 split, and performing feature selection on VH textures), the optimal seasonal configurations are chosen as follows:

### A. 2024 DRY Composite (17-Feature Model)
* **Feature Stack**: 17 bands (VV, VH, VV_ratio, VV_sum, VV_mean, 8 VV textures, 6 VH textures)
* **Optimized Hyperparameters**:
  * `numberOfTrees`: 300
  * `variablesPerSplit`: 3
  * `bagFraction`: 0.5
* **Accuracy Metrics**:
  * **Overall Accuracy**: **65.48%** (Improved by +10.70% from baseline)
  * **Kappa Coefficient**: **0.5237**
  * **Macro F1-score**: **0.6993**
  * **Per-Class F1-scores**: 
    * Water: **0.9291**
    * Sand: **0.6875**
    * Built-up: **0.6372**
    * Vegetation: **0.5433**

### B. 2024 WET Composite (11-Feature Model)
* **Feature Stack**: 11 bands (VV, VH, VV_ratio, VV_sum, VV_mean, 8 VV textures only)
* **Optimized Hyperparameters**:
  * `numberOfTrees`: 100
  * `variablesPerSplit`: None (Default)
  * `bagFraction`: 1.0
* **Accuracy Metrics**:
  * **Overall Accuracy**: **64.39%** (Improved by +15.28% from baseline)
  * **Kappa Coefficient**: **0.5099**
  * **Macro F1-score**: **0.6738**
  * **Per-Class F1-scores**: 
    * Water: **0.8355**
    * Sand: **0.6800**
    * Built-up: **0.6217**
    * Vegetation: **0.5580**


