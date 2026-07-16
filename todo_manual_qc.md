# Tomorrow's Manual QC Checklist: Shoreline Validation Review

This document outlines the step-by-step tasks for manually quality controlling (QC) the Sentinel-1 extracted shorelines and Sentinel-2 validation outputs.

---

## 1. Visual Inspection of Interactive maps (Folium)

Open the following interactive HTML maps in a web browser (e.g., Chrome or Edge):
*   **Dry Season Error Map**: [`outputs/validation_error_map_2024_dry.html`](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/validation_error_map_2024_dry.html)
*   **Wet Season Error Map**: [`outputs/validation_error_map_2024_wet.html`](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/validation_error_map_2024_wet.html)
*   **Original QC Maps**:
    *   [`outputs/shoreline_qc_2024_dry.html`](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/shoreline_qc_2024_dry.html)
    *   [`outputs/shoreline_qc_2024_wet.html`](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/shoreline_qc_2024_wet.html)

### QC Tasks:
- [ ] **Check Bank Type Color-Coding**: Verify that the left bank is color-coded green (`#1abc9c`), the right bank is blue (`#3498db`), and islands are orange (`#e67e22`) on the Shoreline QC Maps.
- [ ] **Check Flow Arrows**: Confirm that purple centerline flow direction arrows correctly point downstream along the main Red River channel.
- [ ] **Overlay Google Satellite**: Switch the base layer to **Google Satellite** (top-right control) and verify that the extracted S1 shoreline matches the physical river banks.

---

## 2. Spatial Outliers Investigation (>100m error)

Load the outlier GeoJSON files into a GIS software (e.g., QGIS) or check the high-error markers (orange and red) on the interactive error maps.
*   **Dry Season Outliers**: `outputs/validation_outliers_2024_dry.geojson` (**9,739** points)
*   **Wet Season Outliers**: `outputs/validation_outliers_2024_wet.geojson` (**12,676** points)

### Focus Areas:
- [ ] **Dynamic Middle Sandbars**: Zoom into the sandbar structures in the center of the river channel (e.g., around coordinates `[21.08, 105.82]`). Verify if the errors are caused by physical sandbar migration or classification mismatch.
- [ ] **Flooded Agricultural Areas (Wet Season)**: Inspect the floodplains. Check if water-logged crops were classified as water in one sensor and land in another, causing large discrepancies.
- [ ] **Disconnected Channels**: Check near the AOI boundary for oxbow lakes or agricultural ponds that may have been disconnected or connected differently.

---

## 3. Verify Output Deliverables

Verify that the following files exist in the `outputs/` directory and have correct content:
- [ ] **CSV Statistics**:
    - `outputs/validation_statistics_2024_dry.csv`
    - `outputs/validation_statistics_2024_wet.csv`
- [ ] **CSV Buffer Accuracies**:
    - `outputs/buffer_accuracy_2024_dry.csv`
    - `outputs/buffer_accuracy_2024_wet.csv`
- [ ] **Validation Report**:
    - Open `outputs/validation_report.md` and read the scientific interpretation section.

---

## 4. GitHub Verification
*   [x] Verify that all code changes (`src/shoreline.py`, `scripts/extract_research_shoreline.py`) and initial checklist are committed and successfully merged to the `main` branch.

---

## 5. Update Project Documentation
*   [ ] **Document Refinement Upgrades**:
    *   Document the **manual bridge masking** workflow (decoupling from Overpass API, editing with `tools/digitize_bridges.html`).
    *   Document the **multi-criteria island filtering** (circularity threshold $\ge 0.8$, Sentinel-2 overlap threshold $\ge 0.5$).
    *   Document the **active learning hotspot bootstrapping** workflow (`scripts/expand_training_polys.py` querying S2 NDWI/NDVI/NDBI metrics to auto-expand training polygons).
    *   Update relevant phase-specific markdown files (e.g. `shoreline_extraction/MASTER_AGENT.md` or `shoreline_extraction/shoreline_extraction_plan.md`) with the final pipeline architecture.
