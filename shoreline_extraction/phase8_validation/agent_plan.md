# Agent Implementation Plan - Phase 8: Final Quality Control and Shoreline Validation

This plan defines the technical specifications, mathematical operations, and verification checkpoints for implementing Phase 8 (Validation & Quality Control) in Python.

---

## 1. Objective
Validate the spatial accuracy of the extracted shoreline against reference data using geometric metrics, and construct an interactive quality control sheet for visual expert verification.

---

## 2. Inputs & Outputs

* **Input**: 
  * Smoothed and simplified final shoreline vector layer from Phase 7.
  * Reference high-resolution validation shorelines (digitized from Sentinel-2 optical imagery or field survey datasets).
  * Raw Sentinel-1 VV backscatter image and classification raster overlay.
* **Output**: 
  * Quantitative validation report containing positional error metrics (Mean, RMSE, Hausdorff).
  * Interactive HTML map (Folium/Leaflet) representing the validation visual sheet.

---

## 3. Detailed Algorithmic Steps

### 8.1 Shoreline Positional Accuracy Metrics
* Do not rely on pixel classification metrics (F1/IoU) to evaluate the linear boundary. Use distance-based geometric validation:
* **Action**:
  1. For each vertex in the extracted shoreline ($L_e$), find the minimum Euclidean distance to the reference shoreline ($L_r$).
  2. Compute:
     * **Mean Distance**: Average offset error.
     * **RMSE (Root Mean Square Error)**: Standard variance of the positional offset:
       $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N d_i^2}$$
     * **Hausdorff Distance**: Maximum local spatial deviation between the two lines:
       $$d_H(L_e, L_r) = \max \left( \max_{p \in L_e} \min_{q \in L_r} ||p-q||, \max_{q \in L_r} \min_{p \in L_e} ||p-q|| \right)$$
     * **95th Percentile Distance**: Eliminates extreme outliers to find the reliable upper bound of error.
  3. Log these metrics in a final validation report.

### 8.2 Interactive QC Sheet (Folium Map)
* **Action**: Build a Python script to compile and export an interactive HTML map for visual inspection:
  1. **Basemaps**:
     * True-color optical reference (Sentinel-2).
     * Raw Sentinel-1 VV intensity (greyscale).
  2. **Overlays**:
     * Classification Raster layer (with an opacity/transparency slider) to verify Water and Sand class boundaries.
     * Raw Shared Boundary (dashed red line).
     * Final Smoothed Shoreline (solid green or cyan line).
  3. **Mandatory Map Interface Controls**:
     * **LayerControl**: Toggle basemaps and vector layers.
     * **Legend**: Custom HTML legend describing classification classes and line styles.
     * **Scale Bar**: To measure local distances.
     * **North Arrow**: For standard geographic orientation.
     * **Coordinate Popup**: Enable click-to-query coordinate popup on the map for easy error coordinates reporting.
  4. **Visual Inspection Routing**:
     * Embed markers at specific coordinates (bridges: Nhật Tân, Thăng Long, Chương Dương, Vĩnh Tuy) and active sandbar points.
     * Allow experts to pan downstream from Sơn Tây to Phú Xuyên.
     * If a local deviation exceeds **$30\text{ m}$**, the system should facilitate logging coordinates for manual training polygon correction or parameter tuning.

---

## 4. Implementation Details

* Use `geopandas` and `shapely` for vector distance metrics.
* Use `folium` for HTML map generation. Add `folium.plugins.ImageOverlay` or GEE TileLayers for rasters.
* Example Folium structure:
  ```python
  import folium
  from folium.plugins import MeasureControl, MousePosition
  
  m = folium.Map(location=[21.04, 105.86], zoom_start=12)
  # Add tile layers
  folium.TileLayer('openstreetmap').add_to(m)
  
  # Add coordinate popups & mouse position
  folium.LatLngPopup().add_to(m)
  MousePosition().add_to(m)
  
  # Add scale bar
  folium.Figure().add_child(m) # if standalone figure controls are needed
  
  # Add vector layers
  folium.GeoJson(raw_shoreline_geojson, name="Raw Shared Boundary", style_function=lambda x: {'color': 'red', 'dashArray': '5, 5'}).add_to(m)
  folium.GeoJson(smooth_shoreline_geojson, name="Final Shoreline", style_function=lambda x: {'color': 'cyan'}).add_to(m)
  folium.LayerControl().add_to(m)
  m.save("outputs/shoreline_qc_sheet.html")
  ```

---

## 5. Quality Control & Assertions

* **RMSE limit**: Ensure the final shoreline RMSE is within acceptable bounds of Sentinel-1 resolution (ideally **$\le 15\text{ m}$** in stable test reaches).
* **HTML file output**: Assert that the Folium script runs successfully and exports a standalone, browser-viewable `shoreline_qc_sheet.html` inside the `outputs` directory.

---

## 6. Definition of Done (DoD)

- [ ] **All functions implemented**: Accuracy metric calculation functions and Folium map compiling code are fully written.
- [ ] **No runtime errors**: Scripts run and complete without warnings or exceptions.
- [ ] **HTML generated**: Standalone map sheet contains LayerControl, Legend, Scale Bar, North Arrow, and Click Coordinate Popup.
- [ ] **Checkpoint PASS**: Validation RMSE meets the required $\le 15\text{ m}$ threshold on reference verification reaches.
- [ ] **Report & Logs written**: Accuracy metrics (RMSE, Mean, Hausdorff, 95th Percentile) and execution parameters are saved to the log file.
- [ ] **Ready for next phase**: final publication-grade vector shapefile and QC HTML sheet are exported and ready for experimental evaluation.
