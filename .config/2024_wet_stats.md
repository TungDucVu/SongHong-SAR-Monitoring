# SongHong Shoreline Run Stats (2024 WET)

- **Execution Date**: 2026-07-27 06:32:38
- **Execution Runtime**: 26m 3s (1563.96 seconds)
- **Year / Season**: 2024 / WET

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 24.74 m
- **Median (P50) Error**: 11.04 m
- **RMSE**: 45.82 m
- **Hausdorff Distance**: 373.38 m
- **95th Percentile (P95)**: 121.79 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 12157
  - Mean Error: 33.16 m
  - Median Error: 15.55 m
  - RMSE: 54.83 m
  - Hausdorff: 189.32 m
  - P95: 149.24 m
- **Reach 2 (Middle)**:
  - Points: 22129
  - Mean Error: 28.69 m
  - Median Error: 16.15 m
  - RMSE: 51.16 m
  - Hausdorff: 373.38 m
  - P95: 126.44 m
- **Reach 3 (Lower)**:
  - Points: 14106
  - Mean Error: 11.27 m
  - Median Error: 4.68 m
  - RMSE: 22.50 m
  - Hausdorff: 153.16 m
  - P95: 37.42 m
