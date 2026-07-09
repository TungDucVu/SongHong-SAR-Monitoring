# Agent Implementation Plan - Phase 6: Shoreline Cleaning (Graph Optimization)

This plan defines the technical specifications, mathematical operations, and verification checkpoints for implementing Phase 6 (Shoreline Cleaning) in Python.

---

## 1. Objective
Build a topological graph from raw shoreline vector lines, prune dead-end spurs, collapse closed loops, and snap endpoints to form a continuous, clean shoreline network.

---

## 2. Inputs & Outputs

* **Input**: 
  * Unsmoothed raw shoreline vector line layer from Phase 5.
* **Output**: 
  * Cleaned, continuous shoreline vector line layer (FeatureCollection of LineStrings).

---

## 3. Detailed Algorithmic Steps

### 6.1 Graph Assembly
* **Action**: Convert the input polylines into a network graph.
  * In Python: Use `NetworkX` or `momepy` to construct a spatial network of nodes (vertices/junctions) and edges (line segments).
  * Nodes are generated at line endpoints and intersections. Edges preserve the coordinate paths of the polylines.

### 6.2 Dead-end Spur Pruning & Loop Collapsing
* Raw vector shorelines often contain small, hanging dead-end spurs (due to minor noise at the water-sand boundary) or tiny loops (around small sand pockets).
* **Action**:
  1. Identify "spur" edges: Edges connected to a node of degree 1 (dead end).
  2. Prune spurs that are shorter than a calibrated threshold length:
     $$\text{Length}(\text{edge}) < L_{\text{prune}}$$
  3. Identify and collapse closed loops (cycles) that represent minor interior holes.
  4. Perform pruning iteratively until no more spurs under the threshold remain.

### 6.3 Network Snapping & Merging
* Small gaps (caused by bridge shadow, pixel masking, or narrow gaps) can segment the shoreline.
* **Action**:
  1. Identify dangling endpoints (degree 1 nodes).
  2. Find pairs of endpoints that are within a calibrated snap distance threshold:
     $$\text{Distance}(\text{node}_a, \text{node}_b) < D_{\text{snap}}$$
  3. Merge/snap these nodes by adding a straight edge connecting them, or extending the lines to join, closing the gap.
  4. Retain the longest connected components of the graph and discard disconnected minor segments.

---

## 4. Implementation Details & Parametric Calibration

* **CRITICAL REQUIREMENT**: Do not hardcode fixed thresholds (like $500\text{m}$ pruning or $150\text{m}$ snapping) as constants in the core algorithm.
* **Action**: Design the cleaning functions to accept parameters dynamically:
  ```python
  def clean_shoreline_graph(shoreline_gdf, prune_threshold_m, snap_threshold_m):
      # NetworkX implementation ...
      return cleaned_gdf
  ```
  * This parameterization is required so that the thresholds can be calibrated empirically using validation reaches or optimized via sensitivity analysis grid search (in Chapter 4 experiments).

---

## 5. Quality Control & Assertions

* **Segment count check**:
  * Assert that the final number of disconnected shoreline segments for the entire Hanoi reach is minimized (**ideally $\le 5$ segments total**).
* **Dead-ends check**:
  * Verify that no short hanging lines ($< L_{\text{prune}}$) remain.
* **Topology integrity**:
  * Ensure that snapping doesn't bridge across the river to the opposite bank (cross-river snapping). The snapping threshold must be smaller than the minimum river width ($D_{\text{snap}} < W_{\text{river\_min}}$).
  * Snap distances should be kept proportional to GEE pixel resolution and local river width (e.g. 50m to 150m).

---

## 6. Definition of Done (DoD)

- [ ] **All functions implemented**: Graph assembly, spur pruning, cycle collapsing, and vertex snapping functions are fully written.
- [ ] **No runtime errors**: Code runs to completion without infinite loops or missing edge references.
- [ ] **HTML generated**: Standalone HTML map sheet showing the graph optimization overlay (raw vs cleaned segments) is generated, containing:
  * LayerControl
  * Legend (showing raw and cleaned lines)
  * Scale Bar
  * North Arrow
  * Coordinate popup
- [ ] **Checkpoint PASS**: The final segment count is $\le 5$ total, and no spurs $< L_{\text{prune}}$ remain. Snapping has not bridged opposite banks.
- [ ] **Checkpoint Failure Policy Applied**: If the final segment count is $> 5$ or cross-river snapping is detected, execution stops immediately and writes a failure log.
- [ ] **Report & Logs written**: The optimized pruning lengths, snapping distances, and final segment counts are logged.
- [ ] **Ready for next phase**: The cleaned vector shorelines are exported/passed to Phase 7.
