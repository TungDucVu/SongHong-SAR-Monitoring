# REACH 2 & 3 OPTIMIZATION EVALUATION REPORT (STANDARD BASELINE - NO BRIDGE INTERVENTIONS)

This report evaluates the accuracy metrics for **Reach 2 (Middle Reach - Hanoi Urban Corridor)** and **Reach 3 (Lower Reach - Agricultural Plain)** using the standard **Global Random Forest Model** without any bridge polygon intervention scripts. Starting point is **Latitude: 21.1528 N, Longitude: 105.5415 E** (68.04 km along the centerline).

---

## 1. Summary of Results (Reach 2 & 3 - 2024 Dry Season)

| Reach Segment | Points Checked | Mean Error (m) | Median Error (m) | RMSE (m) | Hausdorff Max (m) | P95 (m) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Reach 2 (Middle Reach - Hanoi)** | 20,507 | **30.28** | **19.84** | **52.28** | 354.25 | **117.39** |
| **Reach 3 (Lower Reach - Delta)** | 13,901 | **12.21** | **6.40** | **19.56** | 170.98 | **38.27** |
| **Combined Reach 2 & 3 Total** | **34,408** | **25.21** | **15.20** | **43.53** | **354.25** | **92.84** |

---

## 2. Model Configuration
- Pure data-driven extraction based on Sentinel-1 SAR backscatter classification and S2 active channel constraints ($150\text{ m}$ buffer).
- All custom bridge polygon processing functions (`fill_manual_bridges_with_water`, `fix_bridge_interfering_shoreline`, etc.) have been completely removed.

---

## 3. Output Assets
- **Final GeoJSON Output**: [outputs/shoreline_2024_dry_final.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/shoreline_2024_dry_final.geojson)
- **S2 Reference GeoJSON**: [outputs/shoreline_2024_dry_s2_ref.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/shoreline_2024_dry_s2_ref.geojson)
- **Unified Hybrid Map (All Reaches)**: [outputs/map/hybrid_shoreline_map_2024_dry.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map/hybrid_shoreline_map_2024_dry.html)
