# SongHong Shoreline Run Stats (2020 WET)

- **Execution Date**: 2026-07-27 03:05:11
- **Execution Runtime**: 26m 43s (1603.51 seconds)
- **Year / Season**: 2020 / WET

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 23.04 m
- **Median (P50) Error**: 9.05 m
- **RMSE**: 45.03 m
- **Hausdorff Distance**: 364.83 m
- **95th Percentile (P95)**: 131.10 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 11672
  - Mean Error: 28.58 m
  - Median Error: 11.62 m
  - RMSE: 50.87 m
  - Hausdorff: 187.85 m
  - P95: 149.30 m
- **Reach 2 (Middle)**:
  - Points: 22377
  - Mean Error: 27.12 m
  - Median Error: 11.80 m
  - RMSE: 50.83 m
  - Hausdorff: 364.83 m
  - P95: 139.85 m
- **Reach 3 (Lower)**:
  - Points: 13507
  - Mean Error: 11.49 m
  - Median Error: 4.18 m
  - RMSE: 24.92 m
  - Hausdorff: 154.84 m
  - P95: 40.71 m
