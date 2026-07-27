# SongHong Shoreline Run Stats (2017 DRY)

- **Execution Date**: 2026-07-26 23:56:40
- **Execution Runtime**: 25m 37s (1537.57 seconds)
- **Year / Season**: 2017 / DRY

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 29.55 m
- **Median (P50) Error**: 10.53 m
- **RMSE**: 54.64 m
- **Hausdorff Distance**: 369.59 m
- **95th Percentile (P95)**: 149.67 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 11928
  - Mean Error: 48.10 m
  - Median Error: 19.59 m
  - RMSE: 73.78 m
  - Hausdorff: 189.43 m
  - P95: 150.43 m
- **Reach 2 (Middle)**:
  - Points: 22092
  - Mean Error: 32.78 m
  - Median Error: 15.16 m
  - RMSE: 58.00 m
  - Hausdorff: 369.59 m
  - P95: 149.68 m
- **Reach 3 (Lower)**:
  - Points: 14086
  - Mean Error: 8.78 m
  - Median Error: 4.00 m
  - RMSE: 17.59 m
  - Hausdorff: 151.67 m
  - P95: 26.61 m
