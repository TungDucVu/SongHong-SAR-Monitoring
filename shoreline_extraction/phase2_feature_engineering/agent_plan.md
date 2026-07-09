# Agent Implementation Plan - Phase 2: Feature Engineering (v1.1)

This plan defines the technical specifications, mathematical operations, and verification checkpoints for implementing Phase 2 (Feature Engineering) in Python using Google Earth Engine (GEE).

---

## 1. Objective
Construct a multi-band feature stack (11 bands) from preprocessed SAR data to maximize land-cover class separability (specifically for Water vs. Sand) with fixed order and robust texture scaling.

---

## 2. Inputs & Outputs

* **Input**: 
  * Preprocessed Sentinel-1 GEE Image from Phase 1 (containing bands `['VV', 'VH', 'angle']`).
* **Output**: 
  * Multi-band GEE Image stack containing exactly 11 bands in a fixed order with normalized scale.

---

## 3. Detailed Algorithmic Steps

### 3.1 Derived Polarizations
1. **`VV_ratio`** (Log-ratio / ratio in linear scale):
   Calculated by subtracting VH from VV in dB space (which mathematically equals log(VV/VH)):
   $$VV\_ratio = VV_{\text{dB}} - VH_{\text{dB}}$$
2. **`VV_sum`** (Power Summation back to dB scale):
   Do **NOT** add dB values directly. Convert both VV and VH back to linear power, sum them, and convert the result back to dB space:
   $$VV\_sum = 10 \cdot \log_{10}\left(10^{\frac{VV_{\text{dB}}}{10}} + 10^{\frac{VH_{\text{dB}}}{10}}\right)$$
   *GEE Implementation*:
   ```python
   vv_linear = ee.Image(10).pow(image.select('VV').divide(10))
   vh_linear = ee.Image(10).pow(image.select('VH').divide(10))
   vv_sum = vv_linear.add(vh_linear).log10().multiply(10).rename('VV_sum')
   ```
3. **`VV_mean`** (Arithmetic Mean of Log Backscatter):
   Arithmetic mean calculated directly in dB space:
   $$VV\_mean = \frac{VV_{\text{dB}} + VH_{\text{dB}}}{2}$$

### 3.2 GLCM Texture Analysis (on VV band)
To capture spatial variations between water (smooth) and sand/vegetation (rough), calculate gray-level co-occurrence matrix (GLCM) textures.
1. **Window Size**: 
   * Default window size: **7** (i.e. a $7\times7$ neighborhood).
   * Window size 5 is reserved strictly for sensitivity analysis.
2. **Dynamic Range Scaling**:
   Cast the float backscatter values to integers before passing to GEE's `glcmTexture` API. Clamp to $[-25, 5]\text{ dB}$ range, scale to $[0, 255]$ range, and cast to `toInt32()`:
   ```python
   scaled_vv = image.select('VV').clamp(-25, 5).unitScale(-25, 5).multiply(255).toInt32()
   ```
   > [!IMPORTANT]
   > The scaling strategy and bounds ([-25, 5] dB to [0, 255] integer range) must remain **identical** during model training, testing, and inference to prevent predictive bias.
3. **GLCM Textures Selected (6 bands)**:
   * **Contrast** (`VV_contrast`): Measures local intensity variation.
   * **Entropy** (`VV_entropy`): Measures randomness of pixel value distribution.
   * **Homogeneity** (`VV_homogeneity`): Measures similarity of pixel pairs.
   * **Correlation** (`VV_correlation`): Measures linear dependency of gray levels.
   * **ASM** (`VV_ASM`): Angular Second Moment (energy), measures uniform distribution.
   * **Variance** (`VV_variance`): Measures spread of local contrast.

---

## 4. Strict Band Order & Naming Contract

To prevent Random Forest classification mismatches, the output stack **MUST** contain exactly the following 11 bands in this exact sequence:

| Order | Band Name | Data Type | Description |
|---|---|---|---|
| 1 | `VV` | Float32 | Preprocessed VV Backscatter |
| 2 | `VH` | Float32 | Preprocessed VH Backscatter |
| 3 | `VV_ratio` | Float32 | Log-ratio ($VV_{\text{dB}} - VH_{\text{dB}}$) |
| 4 | `VV_sum` | Float32 | Linear sum converted back to dB |
| 5 | `VV_mean` | Float32 | Arithmetic mean of log-backscatter |
| 6 | `VV_contrast` | Float32 | GLCM Contrast ($7\times7$ window) |
| 7 | `VV_entropy` | Float32 | GLCM Entropy ($7\times7$ window) |
| 8 | `VV_homogeneity` | Float32 | GLCM Homogeneity ($7\times7$ window) |
| 9 | `VV_correlation` | Float32 | GLCM Correlation ($7\times7$ window) |
| 10 | `VV_ASM` | Float32 | GLCM Angular Second Moment ($7\times7$ window) |
| 11 | `VV_variance` | Float32 | GLCM Variance ($7\times7$ window) |

---

## 5. Quality Control & Assertions

* **No Infinite/NaN values**: Use GEE mask checks to ensure zero invalid pixels exist in the final band stack.
* **Band Signature Validation**: Print the following information to stdout for audit:
  * Band names
  * Band order
  * Band data types (e.g. Float32)
* **Feature Correlation Check**:
  * Sample 500 random pixels within the AOI.
  * Compute the Pearson/Spearman correlation matrix between all 11 bands.
  * **Warning Rule**: Log a `WARNING` if the correlation between any two distinct bands is $> 0.98$ (identifying redundant features).
* **Multi-Class Texture Validation**:
  * Sample mean GLCM Contrast values over three distinct reference land cover polygons:
    * **Water** (Expected Contrast: very low, smooth texture)
    * **Sand** (Expected Contrast: intermediate-high, granular texture)
    * **Urban** (Expected Contrast: very high, highly irregular texture)
  * Verify that texture values successfully increase class separability.

---

## 6. Definition of Done (DoD)

- [x] **All functions implemented**: Arithmetic indices extraction and normalized GLCM texture calculations are coded.
- [x] **No runtime errors**: Code compiles and executes without memory overflow errors on GEE.
- [x] **HTML generated**: Standalone HTML map sheet showing the `VV_contrast` layer overlay is generated, containing:
  * LayerControl
  * Legend
  * Scale Bar
  * North Arrow
  * Coordinate popup
- [x] **Checkpoint PASS**:
  * Output image contains exactly the 11 contract bands in the correct order.
  * Zero NaN/Inf pixels exist in the stack.
  * Feature correlation and multi-class texture verification (Water, Sand, Urban) are successfully logged.
- [x] **Checkpoint Failure Policy Applied**: If any hard check (e.g., band order mismatch or NaN values) fails, execution halts and logs a failure report.
- [x] **Report & Logs written**: Parameters (GLCM window size, scaling bounds) and execution times are documented.
- [x] **Ready for next phase**: The multi-band stack is returned as an `ee.Image` for classification input.
