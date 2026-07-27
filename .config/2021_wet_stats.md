# SongHong Shoreline Run Stats (2021 WET)

- **Execution Date**: 2026-07-27 03:56:37
- **Execution Runtime**: 25m 54s (1554.95 seconds)
- **Year / Season**: 2021 / WET

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 17.41 m
- **Median (P50) Error**: 7.41 m
- **RMSE**: 36.40 m
- **Hausdorff Distance**: 363.03 m
- **95th Percentile (P95)**: 79.61 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 12316
  - Mean Error: 19.85 m
  - Median Error: 8.83 m
  - RMSE: 36.73 m
  - Hausdorff: 192.04 m
  - P95: 98.31 m
- **Reach 2 (Middle)**:
  - Points: 22228
  - Mean Error: 21.66 m
  - Median Error: 9.39 m
  - RMSE: 43.95 m
  - Hausdorff: 363.03 m
  - P95: 101.95 m
- **Reach 3 (Lower)**:
  - Points: 14031
  - Mean Error: 8.54 m
  - Median Error: 3.70 m
  - RMSE: 18.50 m
  - Hausdorff: 152.63 m
  - P95: 20.92 m
