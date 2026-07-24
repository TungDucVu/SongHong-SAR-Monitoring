# SongHong River Shoreline Validation Report (2024)

This report presents a publication-grade scientific validation and quantitative evaluation of the Sentinel-1 SAR-extracted river shorelines against the independent Sentinel-2 NDWI optical reference shorelines for the 2024 Dry and Wet seasons.

---

## 1. Methodology

The Sentinel-1 SAR shoreline was extracted using a Random Forest classification composite refined with topological morphological cleaning, smoothed using a resampled Chaikin algorithm (30m segment spacing, 3 iterations), and simplified via Douglas-Peucker (1.0m tolerance). 

To evaluate its positional accuracy, we compare it against an independent optical reference shoreline derived from Sentinel-2 NDWI composites (>0.0 threshold) processed for the same seasonal periods. Both the extracted SAR shoreline and the optical reference shoreline were resampled at 5.0m spacing to prevent vertex-density bias. A KD-Tree nearest-neighbor search was then executed to compute the minimum Euclidean distance from each SAR shoreline point to the closest optical reference point.

---

## 2. Tabulated Validation Statistics

The table below summarizes the positional error distribution metrics comparing the Sentinel-1 SAR-extracted shoreline with the Sentinel-2 optical reference shoreline.

| Metric | 2024 Dry Season | 2024 Wet Season |
| :--- | :---: | :---: |
| **Minimum Error (m)** | 0.00 | 0.00 |
| **Maximum Error (Hausdorff) (m)** | 354.25 | 376.48 |
| **Mean Error (m)** | 24.67 | 33.26 |
| **Median (P50) Error (m)** | 16.59 | 20.45 |
| **Standard Deviation (m)** | 33.98 | 43.14 |
| **Root Mean Square Error (RMSE) (m)** | 42.00 | 54.47 |
| **75th Percentile (P75) (m)** | 29.43 | 39.74 |
| **90th Percentile (P90) (m)** | 54.42 | 79.32 |
| **95th Percentile (P95) (m)** | 89.82 | 122.91 |
| **99th Percentile (P99) (m)** | 165.37 | 214.11 |

---

## 3. Buffer-Based Agreement

Buffer-based validation measures the percentage of the extracted SAR shoreline length that falls within a given distance buffer around the Sentinel-2 optical reference shoreline.

| Buffer Width (m) | 2024 Dry Season Coverage (%) | 2024 Wet Season Coverage (%) |
| :---: | :---: | :---: |
| **&le; 10 m** | 40.46% | 34.02% |
| **&le; 20 m** | 57.96% | 45.65% |
| **&le; 30 m** | 75.67% | 63.62% |
| **&le; 50 m** | 88.87% | 82.57% |
| **&le; 75 m** | 93.70% | 89.30% |
| **&le; 100 m** | 95.75% | 92.60% |

---

## 4. Spatial Error Maps & Outliers Interpretation

The spatial distribution of positional errors shows high geometric consistency along the main river banks, but reveals localized discrepancies in specific areas.

- **Dry Season Outliers (>100m)**: Identified **1965** outlier points.
- **Wet Season Outliers (>100m)**: Identified **3517** outlier points.

The interactive spatial error maps ([Dry Map](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/validation_error_map_2024_dry.html) and [Wet Map](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/validation_error_map_2024_wet.html)) reveal that the largest deviations occur primarily in:
1. **Dynamic Sandbars**: Shallow sandbars in the middle of the Red River exhibit significant changes in shape and water coverage between the acquisition dates of Sentinel-1 and Sentinel-2. These features are highly sensitive to small water level variations.
2. **Flooded Agricultural Zones & Floodplains**: During the wet season, agricultural fields adjacent to the river banks become flooded, creating backwaters and water-logged soils. The radar backscatter of Sentinel-1 and the NDWI values of Sentinel-2 respond differently to vegetation-water mixtures, leading to localized differences in boundary definition.
3. **Disconnected Side Channels & Ponds**: Minor oxbow lakes or agricultural ponds near the main river channel are sometimes included in the S2 NDWI mask but pruned from the topological S1 main water body due to lack of connection, or vice versa, causing large apparent discrepancies.

---

## 5. Scientific Interpretation

We interpret the Sentinel-2 NDWI shoreline as an independent optical reference shoreline. The comparisons show:
- **Good positional agreement** during the Dry season, with a median error of **16.59 m** and **88.87%** of the shoreline falling within the 50m buffer.
- **Moderate geometric consistency** during the Wet season, where the median error increases to **20.45 m** and **82.57%** of the shoreline falls within the 50m buffer.
- The increased discrepancy during the Wet season (RMSE of **54.47 m** compared to **42.00 m** in the Dry season) is physically consistent with seasonal river discharge swelling, flooding of shallow riverbanks, and increased turbidity, which impact both radar backscatter signatures and optical spectral response.
- The extreme Hausdorff distances (Dry: **354.25 m**, Wet: **376.48 m**) are not representative of general shoreline accuracy, but reflect localized temporal mismatch in transient sandbar configurations and disconnected aquaculture ponds near the boundaries of the AOI.

---

## 6. Reach-Wise Validation Analysis (2024)

### 2024 Dry Season Reach Performance

| Reach | Point Count | Mean Error (m) | Median Error (m) | RMSE (m) | Hausdorff (m) | P95 (m) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Reach 1** | 12169 | 31.52 | 19.96 | 47.02 | 189.64 | 117.86 |
| **Reach 2** | 20223 | 29.10 | 19.77 | 49.38 | 354.25 | 105.98 |
| **Reach 3** | 13798 | 12.14 | 6.16 | 19.49 | 170.77 | 37.75 |

### 2024 Wet Season Reach Performance

| Reach | Point Count | Mean Error (m) | Median Error (m) | RMSE (m) | Hausdorff (m) | P95 (m) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Reach 1** | 11830 | 37.95 | 23.62 | 57.78 | 266.19 | 128.60 |
| **Reach 2** | 21714 | 40.88 | 26.32 | 64.12 | 376.48 | 147.24 |
| **Reach 3** | 14011 | 17.49 | 7.25 | 29.68 | 193.10 | 54.50 |
