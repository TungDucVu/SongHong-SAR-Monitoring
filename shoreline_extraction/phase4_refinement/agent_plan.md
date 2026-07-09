# Agent Implementation Plan - Phase 4: Classification Refinement

This plan defines the technical specifications, mathematical operations, and verification checkpoints for implementing Phase 4 (Classification Refinement) in Python.

---

## 1. Objective
Post-process the classified raster mask to suppress pixel-level noise, break thin artificial connections, fill micro-holes, and isolate the active river corridor.

---

## 2. Inputs & Outputs

* **Input**: 
  * Classified raster GEE Image from Phase 3.
  * Active river centerline vector layer (for spatial routing).
* **Output**: 
  * Cleaned binary Water and Sand raster masks representing only the active Red River system.

---

## 3. Detailed Algorithmic Steps

### 4.1 Pixel-level Noise Removal (Majority Filter)
* **Action**: Apply a local majority filter (e.g., 3x3 window) using GEE's focal reducer:
  `focal_mode(radius=1.5, kernelType='square')`
  * This eliminates single-pixel misclassifications (salt-and-pepper noise).

### 4.2 Morphological Operations (Disk Structuring Element)
* Standard morphological operations with square or cross kernels cause orientation bias. To prevent this, use a **disk-shaped structuring element** (to ensure isotropic shape preservation):
* **Action**:
  1. **Morphological Opening (Disk radius = 2 pixels / 20m)**:
     * Formula: $\text{Opening}(A, B) = (A \ominus B) \oplus B$ (erosion followed by dilation).
     * Breaks thin artificial bridge connections, removes small noise components, and disconnects irrelevant narrow channels.
  2. **Morphological Closing (Disk radius = 3 pixels / 30m)**:
     * Formula: $\text{Closing}(A, B) = (A \oplus B) \ominus B$ (dilation followed by erosion).
     * Fills micro-holes, internal ponds, or dry cracks within larger sandbars and water bodies.
  3. Implement in GEE using `focal_min` and `focal_max` with a custom circle/disk kernel.

### 4.3 Connected Components (Active River Corridor Extraction)
* Do not keep just the "largest connected component," as complex junctions or split channels might be disconnected.
* **Action**:
  1. Perform connected component analysis on the Water mask (`ee.Image.connectedComponents`).
  2. Identify the connected component(s) representing the **active Red River corridor** using both connectivity and spatial constraints (e.g. overlap with the river centerline or distance $\le 500\text{m}$ to the centerline).
  3. Eliminate all disconnected inland water bodies (aquaculture ponds, municipal lakes, minor irrigation canals) that do not belong to the active river corridor.
  4. Perform the same connectivity-routing constraint on the Sand mask to keep only sandbars that touch the active river corridor.

---

## 4. GEE/Python Implementation Details

* Use `ee.Kernel.circle(radius)` to create the disk-shaped structuring elements.
* Set thresholds in config:
  * `SHORELINE_OPEN_SIZE = 2`
  * `SHORELINE_CLOSE_SIZE = 3`
* Use `connectedComponents` with `maxSize` to handle GEE memory constraints.

---

## 5. Quality Control & Assertions

* **Water component reduction**:
  * Assert that the total number of disconnected water patches drops by **$\ge 95\%$** after applying the active corridor connectivity constraint.
* **Visual check**:
  * Verify that municipal lakes (e.g., West Lake/Hồ Tây) and aquaculture ponds outside the dyke are completely masked out.
  * Ensure the main flow of the Red River is continuous and not broken at bridge crossings (e.g., Nhật Tân, Thăng Long).
* **Disk kernel validation**: Check that the boundary corners of large sandbars are rounded and do not show staircase square edges.

---

## 6. Definition of Done (DoD)

- [ ] **All functions implemented**: Majority filter, morphological opening/closing (disk), and connected component corridor routing are fully coded.
- [ ] **No runtime errors**: Refinement processes execute without errors or memory allocation overflow.
- [ ] **HTML generated**: Standalone HTML map sheet showing the refined Water and Sand masks overlay is generated, containing:
  * LayerControl
  * Legend (showing Water and Sand classes)
  * Scale Bar
  * North Arrow
  * Coordinate popup
- [ ] **Checkpoint PASS**: The water component count drops by $\ge 95\%$ after processing. Visual inspection confirms municipal lakes and isolated ponds are completely masked.
- [ ] **Checkpoint Failure Policy Applied**: If the component count reduction is less than $95\%$, execution stops immediately and writes a failure log.
- [ ] **Report & Logs written**: Parameters (disk radius, component areas, snap limits) and execution statistics are logged.
- [ ] **Ready for next phase**: Cleaned binary Water and Sand masks are exported/passed to Phase 5.
