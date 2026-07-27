# SongHong Shoreline Run Stats (2022 WET)

- **Execution Date**: 2026-07-27 04:48:13
- **Execution Runtime**: 26m 11s (1571.80 seconds)
- **Year / Season**: 2022 / WET

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 21.46 m
- **Median (P50) Error**: 9.05 m
- **RMSE**: 42.33 m
- **Hausdorff Distance**: 348.32 m
- **95th Percentile (P95)**: 108.09 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 11547
  - Mean Error: 26.02 m
  - Median Error: 11.51 m
  - RMSE: 45.82 m
  - Hausdorff: 187.82 m
  - P95: 132.82 m
- **Reach 2 (Middle)**:
  - Points: 22178
  - Mean Error: 27.22 m
  - Median Error: 12.34 m
  - RMSE: 51.21 m
  - Hausdorff: 348.32 m
  - P95: 134.31 m
- **Reach 3 (Lower)**:
  - Points: 14013
  - Mean Error: 8.60 m
  - Median Error: 4.05 m
  - RMSE: 14.93 m
  - Hausdorff: 150.33 m
  - P95: 26.55 m
