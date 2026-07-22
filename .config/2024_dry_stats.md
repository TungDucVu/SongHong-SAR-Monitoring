# SongHong Shoreline Run Stats (2024 DRY)

- **Execution Date**: 2026-07-22 16:23:03
- **Execution Runtime**: 6m 16s (376.65 seconds)
- **Year / Season**: 2024 / DRY

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 25.21 m
- **Median (P50) Error**: 16.46 m
- **RMSE**: 43.53 m
- **Hausdorff Distance**: 354.25 m
- **95th Percentile (P95)**: 92.84 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 12169
  - Mean Error: 31.52 m
  - Median Error: 19.96 m
  - RMSE: 47.02 m
  - Hausdorff: 189.64 m
  - P95: 117.86 m
- **Reach 2 (Middle)**:
  - Points: 20507
  - Mean Error: 30.28 m
  - Median Error: 19.84 m
  - RMSE: 52.28 m
  - Hausdorff: 354.25 m
  - P95: 117.39 m
- **Reach 3 (Lower)**:
  - Points: 13901
  - Mean Error: 12.21 m
  - Median Error: 6.40 m
  - RMSE: 19.56 m
  - Hausdorff: 170.98 m
  - P95: 38.27 m
