# SongHong Shoreline Run Stats (2019 DRY)

- **Execution Date**: 2026-07-27 01:45:12
- **Execution Runtime**: 28m 7s (1687.65 seconds)
- **Year / Season**: 2019 / DRY

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 22.85 m
- **Median (P50) Error**: 9.05 m
- **RMSE**: 45.22 m
- **Hausdorff Distance**: 366.97 m
- **95th Percentile (P95)**: 142.50 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 11594
  - Mean Error: 32.65 m
  - Median Error: 13.12 m
  - RMSE: 56.53 m
  - Hausdorff: 189.90 m
  - P95: 149.92 m
- **Reach 2 (Middle)**:
  - Points: 21536
  - Mean Error: 26.52 m
  - Median Error: 11.94 m
  - RMSE: 50.56 m
  - Hausdorff: 366.97 m
  - P95: 149.14 m
- **Reach 3 (Lower)**:
  - Points: 14021
  - Mean Error: 9.12 m
  - Median Error: 4.07 m
  - RMSE: 17.49 m
  - Hausdorff: 152.69 m
  - P95: 29.35 m
