# SongHong Shoreline Run Stats (2025 WET)

- **Execution Date**: 2026-07-27 07:22:10
- **Execution Runtime**: 24m 47s (1487.63 seconds)
- **Year / Season**: 2025 / WET

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 23.77 m
- **Median (P50) Error**: 10.49 m
- **RMSE**: 45.50 m
- **Hausdorff Distance**: 355.67 m
- **95th Percentile (P95)**: 124.68 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 12162
  - Mean Error: 36.93 m
  - Median Error: 17.33 m
  - RMSE: 59.41 m
  - Hausdorff: 186.38 m
  - P95: 149.85 m
- **Reach 2 (Middle)**:
  - Points: 21276
  - Mean Error: 25.89 m
  - Median Error: 13.70 m
  - RMSE: 49.38 m
  - Hausdorff: 355.67 m
  - P95: 119.96 m
- **Reach 3 (Lower)**:
  - Points: 13866
  - Mean Error: 8.98 m
  - Median Error: 4.52 m
  - RMSE: 15.03 m
  - Hausdorff: 151.52 m
  - P95: 25.12 m
