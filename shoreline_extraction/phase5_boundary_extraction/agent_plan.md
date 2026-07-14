# Agent Implementation Plan - Phase 5: Water Exterior Boundary Shoreline Extraction

This plan defines the technical specifications, mathematical operations, and verification checkpoints for implementing Phase 5 (Water Exterior Boundary Shoreline Extraction) in Python.

---

## 1. Objective
Extract the topological outer boundary representing the exterior boundary of the main water corridor, producing a raw continuous shoreline without relying on the water-sand interface intersection.

---

## 2. Inputs & Outputs

* **Input**: 
  * Refined binary Water raster mask from Phase 4.
* **Output**: 
  * Unsmoothed raw Shoreline vector polyline layer saved as `outputs/shoreline_raw.geojson`.
  * **Coordinate Reference System (CRS)**: `EPSG:32648` (WGS 84 / UTM Zone 48N).

---

## 3. Detailed Algorithmic Steps

### 5.1 Polygonization & Downloading
* **Action**: Convert the refined GEE raster mask of Water into vector polygons.
  * In GEE: Use `reduceToVectors` at native 10m scale (`scale=10`, `geometryType='polygon'`).
  * Download the resulting `FeatureCollection` via `.getInfo()` and load locally into a GeoPandas GeoDataFrame:
    * `water_gdf` (initially in `EPSG:4326`).
  * Reproject the layer immediately to the metric projection `EPSG:32648` (UTM 48N).

### 5.2 Dissolving (Unioning)
* **Action**: Dissolve individual polygons to handle single main corridors.
  * Apply `unary_union` on the geometry arrays of `water_gdf` to create a single, clean consolidated geometry:
    * $W_{\text{union}} = \text{unary\_union}(water\_gdf.geometry)$

### 5.3 Geometry Validation & Cleaning
* **Action**: Ensure the consolidated geometry is topologically valid before boundary extraction.
  * Apply Shapely's `make_valid()` and `buffer(0)` on $W_{\text{union}}$ to resolve self-intersections or duplicate vertex slivers:
    * $W_{\text{clean}} = \text{make\_valid}(W_{\text{union}}.\text{buffer}(0))$
  * Filter out and discard any empty geometries.

### 5.4 Exterior Boundary Extraction & Explosion
* **Action**: Extract the exterior boundary of the clean, dissolved water geometry.
  1. For the main water polygon `W_clean` (or if it is a MultiPolygon, for each constituent polygon), extract the `exterior` boundary coords as a LineString.
  2. Discard any short artifact segments (< 5.0m).

---

## 4. Python Implementation Details

* Local execution with Shapely & GeoPandas:
  ```python
  import geopandas as gpd
  from shapely.validation import make_valid

  # 1. Load and reproject to EPSG:32648
  water_gdf = gpd.GeoDataFrame.from_features(water_geojson, crs="EPSG:4326").to_crs("EPSG:32648")
  sand_gdf = gpd.GeoDataFrame.from_features(sand_geojson, crs="EPSG:4326").to_crs("EPSG:32648")

  # 2. Dissolve
  water_union = water_gdf.geometry.unary_union
  sand_union = sand_gdf.geometry.unary_union

  # 3. Validate
  water_clean = make_valid(water_union.buffer(0))
  sand_clean = make_valid(sand_union.buffer(0))

  # 4. Extract shared boundary
  raw_boundary = water_clean.boundary.intersection(sand_clean.buffer(0.1))

  # 5. Explode into LineStrings
  lines = []
  if raw_boundary.geom_type == 'LineString':
      lines.append(raw_boundary)
  elif raw_boundary.geom_type == 'MultiLineString':
      lines.extend(list(raw_boundary.geoms))
  elif raw_boundary.geom_type == 'GeometryCollection':
      for geom in raw_boundary.geoms:
          if geom.geom_type == 'LineString':
              lines.append(geom)
          elif geom.geom_type == 'MultiLineString':
              lines.extend(list(geom.geoms))
  ```

---

## 5. Quality Control & Assertions

* **Closed Loop Constraint**:
  * Identify and **remove closed loop segments that are NOT connected to the main river corridor** (e.g., isolated inland waterbodies or ponds that were not fully pruned in Phase 4).
  * Closed loops around valid mid-channel sand islands **must be preserved** as they represent correct physical shorelines.
* **Non-sandbar bank exclusion**:
  * Verify that shorelines are not generated along concrete embankment walls (e.g. urban Hanoi shoreline with no sand) or heavily vegetated banks.
* **Geometry validation**:
  * Assert that no empty geometries or null values are saved to the output GeoJSON.

---

## 6. Definition of Done (DoD)

- [ ] **All functions implemented**: Polygonization, dissolving, geometry validation, shared boundary intersection, and line explosion are fully coded.
- [ ] **No runtime errors**: Vector operations run without raising topology exceptions.
- [ ] **HTML generated**: Standalone HTML map sheet showing the raw unsmoothed shoreline vector polyline is generated, containing:
  * LayerControl
  * Legend (showing the raw shoreline line style)
  * Scale Bar
  * North Arrow
  * Coordinate popup
- [ ] **Checkpoint PASS**: Invalid geometries are successfully resolved, and all output layers are in `EPSG:32648`.
- [ ] **Report & Logs written**: Log metrics to output files:
  * Run time.
  * Total raw shoreline length (in meters).
  * Number of invalid geometries fixed.
  * Number of closed loops removed.
  * Number of shoreline segments.
- [ ] **Ready for next phase**: The raw unsmoothed shoreline vector polyline layer is exported as a GeoJSON (`outputs/shoreline_raw.geojson`) in `EPSG:32648`.
