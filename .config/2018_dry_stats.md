# SongHong Shoreline Run Stats (2018 DRY)

- **Execution Date**: 2026-07-27 00:49:41
- **Execution Runtime**: 25m 24s (1524.31 seconds)
- **Year / Season**: 2018 / DRY

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 41.97 m
- **Median (P50) Error**: 9.76 m
- **RMSE**: 70.76 m
- **Hausdorff Distance**: 153.77 m
- **95th Percentile (P95)**: 149.38 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 0
  - Mean Error: 0.00 m
  - Median Error: 0.00 m
  - RMSE: 0.00 m
  - Hausdorff: 0.00 m
  - P95: 0.00 m
- **Reach 2 (Middle)**:
  - Points: 2182
  - Mean Error: 114.10 m
  - Median Error: 149.16 m
  - RMSE: 125.50 m
  - Hausdorff: 153.77 m
  - P95: 149.47 m
- **Reach 3 (Lower)**:
  - Points: 5589
  - Mean Error: 13.81 m
  - Median Error: 4.08 m
  - RMSE: 28.52 m
  - Hausdorff: 151.53 m
  - P95: 51.21 m
