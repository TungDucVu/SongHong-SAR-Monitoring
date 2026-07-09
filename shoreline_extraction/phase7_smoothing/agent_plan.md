# Agent Implementation Plan - Phase 7: Shoreline Smoothing & Simplification

This plan defines the technical specifications, mathematical operations, and verification checkpoints for implementing Phase 7 (Smoothing & Simplification) in Python.

---

## 1. Objective
Apply corner-cutting smoothing to remove pixelation artifacts from the raw raster-derived lines, followed by Douglas-Peucker simplification to optimize vertex density for GIS processing.

---

## 2. Inputs & Outputs

* **Input**: 
  * Cleaned shoreline vector line layer from Phase 6.
* **Output**: 
  * Smoothed and simplified research-grade shoreline vector layer.

---

## 3. Detailed Algorithmic Steps

### 7.1 Vertex Density & Corner-Cutting (Chaikin's Algorithm)
* Raw raster boundaries exhibit $90^\circ$ pixelated staircase paths.
* **Action**:
  1. Apply **Chaikin's Corner-Cutting algorithm** to the coordinate sequence of each line segment.
  2. For each pair of vertices $(p_i, p_{i+1})$, replace the corner with two new vertices $q_i$ and $r_i$:
     $$q_i = \frac{3}{4}p_i + \frac{1}{4}p_{i+1}$$
     $$r_i = \frac{1}{4}p_i + \frac{3}{4}p_{i+1}$$
  3. Execute 2 to 3 iterations of this process.
  4. *Rationale*: Chaikin MUST be performed BEFORE simplification because it interpolates new points to round out the staircase corners, creating a physically plausible, curved shoreline.

### 7.2 Douglas-Peucker (DP) Simplification
* After Chaikin smoothing, the vertex count increases significantly. Many vertices along straight sections are redundant.
* **Action**:
  1. Apply the **Douglas-Peucker simplification algorithm** to the Chaikin-smoothed lines.
  2. Use a small distance tolerance $T$ (e.g., $1.0\text{ m}$ to $5.0\text{ m}$).
  3. The algorithm recursively subdivides the line and removes vertices that deviate from the chord line by less than $T$.
  4. *Rationale*: This reduces the coordinate file size and vertex count, optimizing it for GIS rendering without losing the smoothed geometry.

---

## 4. Implementation Details

* If executing locally: Use `shapely.simplify` for Douglas-Peucker. Chaikin's algorithm can be implemented via a simple python function iterating over coordinate lists:
  ```python
  def chaikin_smooth(coords, iterations=3):
      for _ in range(iterations):
          new_coords = [coords[0]]
          for i in range(len(coords) - 1):
              p0, p1 = coords[i], coords[i+1]
              q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
              r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])
              new_coords.extend([q, r])
          new_coords.append(coords[-1])
          coords = new_coords
      return coords
  ```

---

## 5. Quality Control & Assertions

* **Vertex Count Reduction**: 
  * Assert that the final simplified shoreline contains **$\ge 60\%$ fewer vertices** compared to the line immediately after the Chaikin smoothing phase.
* **Hausdorff Deviation Limit**: 
  * Calculate the maximum Hausdorff distance between the unsmoothed raw line (Phase 6) and the final smoothed/simplified line.
  * Assert that the deviation is **approximately one pixel ($\approx 10\text{ m}$)**. If the deviation is larger, reduce the DP tolerance $T$ or Chaikin iterations.
* **Topological Conservation**: Ensure that smoothing does not cause the line to intersect itself or cross over the river bank boundary.

---

## 6. Definition of Done (DoD)

- [ ] **All functions implemented**: Chaikin smoothing and Douglas-Peucker simplification algorithms are fully coded.
- [ ] **No runtime errors**: Line smoothing runs to completion without errors.
- [ ] **HTML generated**: Standalone HTML map sheet showing the smoothed shoreline vs the raw pixelated path is generated, containing:
  * LayerControl
  * Legend (showing raw and smoothed shorelines)
  * Scale Bar
  * North Arrow
  * Coordinate popup
- [ ] **Checkpoint PASS**: Vertex count is reduced by $\ge 60\%$ after DP simplification. The maximum Hausdorff deviation between raw and smoothed lines is approximately one pixel ($\approx 10\text{ m}$).
- [ ] **Checkpoint Failure Policy Applied**: If the vertex count reduction is $< 60\%$ or Hausdorff deviation $> 15\text{ m}$, execution stops immediately and writes a failure log.
- [ ] **Report & Logs written**: Chaikin iterations, DP tolerance, pre/post vertex counts, and Hausdorff metrics are logged.
- [ ] **Ready for next phase**: The final research-grade smoothed shoreline vector layer is exported/passed to Phase 8.
