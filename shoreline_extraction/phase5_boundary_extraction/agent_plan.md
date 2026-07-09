# Agent Implementation Plan - Phase 5: Water–Sand Shared Boundary Extraction

This plan defines the technical specifications, mathematical operations, and verification checkpoints for implementing Phase 5 (Water-Sand Shared Boundary Extraction) in Python.

---

## 1. Objective
Extract the topological contact line strictly representing the shared boundary between the active Red River corridor and sandbars, eliminating non-sandbank boundaries and closed loop artifacts.

---

## 2. Inputs & Outputs

* **Input**: 
  * Refined binary Water and Sand raster masks from Phase 4.
* **Output**: 
  * Unsmoothed raw Shoreline vector polyline layer (GeoJSON or GEE FeatureCollection).

---

## 3. Detailed Algorithmic Steps

### 5.1 Polygonization
* **Action**: Convert the refined raster masks of Water and Sand into vector polygons.
  * In GEE: Use `reduceToVectors` with a scale of 10m.
  * In local Python (if running locally): Use rasterio/shapely `features.shapes`.
  * Ensure polygons are simplified to remove redundant pixel-staircase vertices at this stage, but keep the topological structure intact.

### 5.2 Shared Boundary Intersection (Main Corridor Interface)
* Direct polygon intersection can generate outer boundary loops, isolated island loops, or internal holes inside sandbars that do not represent the active shoreline.
* **Action**:
  1. Identify the polygon representing the **Main active Red River Corridor** ($W_{\text{corridor}}$).
  2. Identify all Sand polygons ($S_i$).
  3. Extract the shared boundary line strictly at the interface where the active corridor touches a sandbank:
     $$\text{Shoreline} = \partial(W_{\text{corridor}}) \cap \partial(\bigcup S_i)$$
  * In vector terms: Calculate the intersection of the exterior boundary of the main water polygon with the exterior boundary of the sand polygons.
  * This topological filter:
    * **Extracts only** the active water-sand interface.
    * **Discards** boundaries along concrete embankments, vegetated banks, or built-up banks.
    * **Discards** boundaries of inland lake polygons or isolated ponds.
    * **Discards** internal rings (lake boundaries/holes) inside sandbars that do not touch the main river flow.

---

## 4. GEE/Python Implementation Details

* If using GEE:
  ```python
  # Get main water polygon geometry
  water_geom = water_polygon.geometry()
  sand_geom = sand_polygons.geometry()
  # Intersection of boundaries (lines)
  raw_shoreline = water_geom.boundary().intersection(sand_geom.boundary())
  ```
* If executing locally with Shapely:
  ```python
  # Find shared boundary between geometries
  shoreline = water_poly.exterior.intersection(sand_multi_poly)
  ```
* Ensure the resulting geometries are converted to a FeatureCollection of LineStrings (or MultiLineStrings).

---

## 5. Quality Control & Assertions

* **No Closed Loops check**: 
  * Assert that no closed, circular LineStrings exist in the final shoreline layer. All segments should be open lines representing active river-sand interfaces.
* **Non-sandbar bank exclusion**:
  * Verify that shorelines are not generated along concrete embankment walls (e.g. urban Hanoi shoreline with no sand) or heavily vegetated banks.
* **Geometry validation**:
  * Ensure the output geometries do not contain null coordinates or invalid self-intersecting geometries.

---

## 6. Definition of Done (DoD)

- [ ] **All functions implemented**: Raster-to-polygon conversion and shared boundary topological intersection logic are fully coded.
- [ ] **No runtime errors**: Vector operations run without raising topology exceptions (such as self-intersection or null geometry errors).
- [ ] **HTML generated**: Standalone HTML map sheet showing the raw unsmoothed shoreline vector polyline is generated, containing:
  * LayerControl
  * Legend (showing the raw shoreline line style)
  * Scale Bar
  * North Arrow
  * Coordinate popup
- [ ] **Checkpoint PASS**: No closed loops are generated, and shorelines along non-sand banks are excluded.
- [ ] **Checkpoint Failure Policy Applied**: If any closed loop is generated in the final output, execution stops immediately and writes a failure log.
- [ ] **Report & Logs written**: The number of extracted raw boundary segments, processing times, and potential topology errors are logged.
- [ ] **Ready for next phase**: The raw unsmoothed shoreline vector polyline layer is exported as a Shapefile or GeoJSON in UTM Zone 48N.
