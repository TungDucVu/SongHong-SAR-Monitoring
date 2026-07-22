# REACH 1 OPTIMIZATION EVALUATION REPORT

This report evaluates the localized accuracy improvements for Reach 1 (Upper) after implementing the Final Execution Plan:
1. **Phase 1-2 (Self-Supervised Labeling & Hard Negative Mining)**: Dynamically generated 4-class reference maps on 2021 Sentinel-2 composites using local Otsu thresholding on MNDWI and BSI. Samples were drawn with a 70/30 boundary bias to force the RF model to learn the water-sand interface.
2. **Phase 3 (Topographic & Temporal Stack)**: Extended features to include HAND (Height Above Nearest Drainage), SRTM Slope, and seasonal variance/P10 bands.

## 1. Summary of Results (Reach 1)

### Dry Season (2024)
| Method | Points | Mean (m) | Median (m) | RMSE (m) | Hausdorff (m) | P95 (m) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Global RF, Single-Date)** | 21779 | 125.61 | 23.59 | 253.28 | 1267.96 | 654.43 |
| **Local RF + Temporal (Composite)** | 15780 | 114.58 | 70.82 | 168.74 | 584.68 | 389.76 |
| **Final Plan (Otsu + Hard Mining)** | 13586 | 21.92 | 7.64 | 42.93 | 307.77 | 106.63 |

### Wet Season (2024)
| Method | Points | Mean (m) | Median (m) | RMSE (m) | Hausdorff (m) | P95 (m) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Global RF, Single-Date)** | 21839 | 34.79 | 12.83 | 76.76 | 605.47 | 142.18 |
| **Local RF + Temporal (Composite)** | 15841 | 95.41 | 45.70 | 147.59 | 614.19 | 374.10 |
| **Final Plan (Otsu + Hard Mining)** | 14517 | 23.13 | 5.46 | 47.07 | 328.35 | 139.79 |

## 2. Key Findings & Discussion
- **Hard Negative Boundary Sampling (70/30)** significantly improved classification edge definition by forcing the RF trees to split near the sandbar-water interface.
- **HAND (Height Above Nearest Drainage)** effectively suppressed false-positive water predictions on elevated structures and hill shadows in the upper reach.
## 3. Interactive Spatial Error Maps
- **Dry Season Map**: [reach1_optimized_error_map_2024_dry.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/reach1_optimized_error_map_2024_dry.html)
- **Wet Season Map**: [reach1_optimized_error_map_2024_wet.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/reach1_optimized_error_map_2024_wet.html)
