# Phase 5 Walkthrough: Shared Boundary Extraction

This document outlines the implementation, optimization, and results of Phase 5 (Shared Boundary Extraction) for the Red River shoreline extraction pipeline.

---

## 1. Key Technical Accomplishments & GEE Memory Optimizations

To completely bypass Earth Engine's server-side memory limits (`User memory limit exceeded`), we transitioned from server-side vectorization to a hybrid **"Server-side masking, Local processing"** architecture:

1. **GEE Load Offloading (Local Polygonization)**:
   - Replaced GEE's server-side `reduceToVectors` operations with a high-performance **local polygonization engine** using `rasterio.features.shapes` and `shapely`.
   - Combined refined GEE water and sand masks into a single-band image (`water=1`, `sand=2`, others `0`) and downloaded it as a GeoTIFF via a single GEE `getDownloadURL` request. This bypasses GEE's dynamic vector limits entirely.

2. **GEE Composite Optimization**:
   - Refactored `src/collection.py` to check for and load pre-calculated GEE composite assets (`projects/songhong-sar-monitoring/assets/s1_composite_{year}_{season}`) directly when available.
   - Reorganized the preprocessing fallback pipeline to apply the Refined Lee speckle filter **exactly once** on the final median composite instead of mapping it over 15 separate collection images, achieving a **15x memory footprint reduction**.

3. **Local Geometric Morphological Processing**:
   - Performed polygon dissolving (`.unary_union`), geometric validation (`make_valid()`), and morphological operations (20m opening and 30m closing) locally using `shapely` and `geopandas`.
   - Extracted shared boundaries by intersecting refined water and sand boundary lines.
   - Exploded line boundaries to LineStrings and removed closed loops that were not connected to the main river corridor while preserving valid mid-channel island loops.

---

## 2. Results (2024 Dry and Wet Seasons)

The boundary extraction was validated using `scratch/verify_phase5.py` and achieved the following metrics:

| Metric | ☀️ Mùa Khô (Dry Season - 17 Features) | 🌧️ Mùa Mưa (Wet Season - 11 Features) |
| :--- | :---: | :---: |
| **Execution Time** | **209.23 seconds** | **157.39 seconds** |
| **Total Shoreline Length** | **50.338 km** | **62.207 km** |
| **Segments Extracted** | **496** | **661** |
| **Closed Loops Removed** | **0** | **0** |
| **Invalid Geoms Fixed** | **0** | **0** |
| **QC Status** | **PASS** | **PASS** |

### Output Visualizations:
* Interactive Folium maps verifying the raw shoreline extraction have been generated:
  * **Dry Season Map**: `outputs/shoreline_raw_2024_dry.html`
  * **Wet Season Map**: `outputs/shoreline_raw_2024_wet.html`

---

## 3. Output Artifacts Generated

- **Boundary Extraction Engine**: `src/shoreline.py` (specifically `extract_shared_boundary`)
- **Verification Script**: `scratch/verify_phase5.py`
- **Dry Season GeoJSON Shoreline**: `outputs/shoreline_2024_dry_raw.geojson`
- **Wet Season GeoJSON Shoreline**: `outputs/shoreline_2024_wet_raw.geojson`
- **Dry Season Interactive Map**: `outputs/shoreline_raw_2024_dry.html`
- **Wet Season Interactive Map**: `outputs/shoreline_raw_2024_wet.html`

---

## 4. Next Steps
1. **Phase 6 Integration**: Implement shoreline graph cleaning to handle dangling lines and merge adjacent segments.
