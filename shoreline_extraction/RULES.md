# Shoreline Pipeline Coding Rules & Standards

**Methodology Version**: 1.0 (Locked - Do not modify)

This document establishes strict rules, guidelines, and constraints for implementing the shoreline extraction pipeline. Every coding agent must adhere to these standards to ensure scientific rigor, performance, and correctness.

---

## 1. Core Implementation Constraints

### A. No Algorithm Redesign
* **Rule**: Never redesign the approved methodology. Implement only. If a better or alternative algorithm is found, report it in writing but **do not** replace or modify the pipeline structure.

### B. No Interface or Contract Changes
* **Rule**: Do not rename public functions, module names, output file names, or interface contracts without prior approval.

### C. No Code Duplication
* **Rule**: Shared utilities (such as date parsing, spatial coordinate conversions, or GEE authentication wrappers) must be placed in `src/utils.py`. Do not duplicate implementations across script files.

### D. Mandatory Logging
* **Rule**: Every phase and module execution must implement comprehensive logging.
* **Action**: Logs must record:
  * Input/output parameters and thresholds used.
  * Precise execution time for major steps.
  * Errors, warnings, and checkpoint results.

### E. Checkpoint Failure Policy
* **Rule**: If any phase checkpoint or validation check fails:
  1. **STOP** execution immediately.
  2. Write a detailed failure report to the log file documenting the parameters and metrics that caused the failure.
  3. **Do not** attempt to automatically patch, bypass, or rewrite the pipeline design to force execution.

---

## 2. Google Earth Engine (GEE) Standards

### A. Avoid Client-Side Loops over Collections
* **Rule**: Never use client-side Python `for` loops to iterate over `ee.ImageCollection` or `ee.FeatureCollection`.
* **Action**: Always use `.map()` or `.reduce()` to execute operations on the GEE server.

### B. No `.getInfo()` Calls in Processing Functions
* **Rule**: Do not call `.getInfo()` on GEE objects inside loops, mapping functions, or core pipeline steps.
* **Action**: Only use `.getInfo()` or printing for final validation outputs or debugging at the outer-most script level.

### C. Consistent Projections and Scale
* **Rule**: Always specify `scale=10` and `crs="EPSG:32648"` when performing GEE operations like `reduceRegions`, `reduceToVectors`, or sampling.
* **Action**: Do not rely on default projections, as GEE will default to Web Mercator (`EPSG:3857`) at varying scales, causing major area and distance errors.

---

## 3. Python Vector & Geometry Standards

### A. Vectorize Spatial Operations
* **Rule**: Use vector-oriented operations via `geopandas` and `shapely`. Avoid nested iterators over row geometries where possible.

### B. Handle Geometry Validity
* **Rule**: Always assert or fix geometry validity before intersection or difference operations.
* **Action**: Use `geom.buffer(0)` or `shapely.validation.make_valid(geom)` to clean up self-intersecting loops and slivers.

### C. Distance Calculations in Metric CRS
* **Rule**: All distance measurements (e.g. snapping distances, pruning lengths, RMSE offsets) must be computed in a metric projection (`EPSG:32648` / UTM Zone 48N).
* **Action**: Never calculate Euclidean distances on coordinates in WGS 84 geographic coordinates (`EPSG:4326` / degrees).

---

## 4. Configuration & Parameter Tuning

### A. No Hardcoded Magic Numbers
* **Rule**: Do not hardcode parameters like filter window sizes, morphological radii, snapping distances, or pruning lengths inside implementation modules.
* **Action**: Define all parameters in `src/config.py` and import them.

### B. Dynamic Function Signatures
* **Rule**: Core functions in `src/shoreline.py` must accept parameter arguments with default values derived from `src/config.py`.
* **Example**:
  ```python
  def extract_shoreline(water_mask, sand_mask, open_radius=SHORELINE_OPEN_SIZE, snap_dist=SHORELINE_SNAP_DISTANCE):
      ...
  ```

---

## 5. Visualizations & Outputs

### A. No GeoTIFF exports (.tif)
* **Rule**: The pipeline **must not** generate or save local `.tif` images or submit export tasks to Google Drive.
* **Action**: Carry out all raster processing on GEE or in memory, and export final results as lightweight vectors (GeoJSON/Shapefile) or interactive map sheets.

### B. Every Phase Must Output an HTML Map
* **Rule**: Every phase must export a local HTML map showing its main input/output overlays, to satisfy the visual verification rule.

### C. Leaflet/Folium Map Standards
* **Rule**: Every exported HTML map sheet (e.g. `outputs/shoreline_qc_sheet.html`) must contain the following interface elements:
  * **LayerControl**: To toggle backgrounds (S2, S1 VV) and overlays.
  * **Legend**: Visual guide for class labels and line styles.
  * **Scale Bar**: To measure local physical distances.
  * **North Arrow**: For standard geographic orientation.
  * **Coordinate Popup**: Click-to-query coordinate coordinates for error reporting.

---

## 6. Definition of Done (DoD)

Before completing a phase, the implementation agent must satisfy the following Checklist:
- [ ] **All functions implemented**: All sub-phase modules are coded, documented with docstrings, and match the specified mathematical rules.
- [ ] **No runtime errors**: Scripts run from start to finish without warnings/exceptions.
- [ ] **HTML generated**: Visualization maps are exported with all required interactive elements.
- [ ] **Checkpoint PASS**: All validation check metrics (e.g. F1 sand, component reduction, Hausdorff distance) meet the target values.
- [ ] **Report & Logs written**: Parameters, execution times, and error profiles are saved to logs.
- [ ] **Ready for next phase**: Outputs are stored in the correct directory, matching the expected format for the subsequent phase.
