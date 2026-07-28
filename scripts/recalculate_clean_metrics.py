"""
Clean Fast Recalculation of All 20 Seasons Validation Metrics (2017 - 2026)
Saves results into CSVs and Master Markdown Summary Reports.
"""

import os
import sys
import numpy as np
import geopandas as gpd
import pandas as pd
from scipy.spatial import cKDTree

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

def extract_pts(gdf):
    pts = []
    for geom in gdf.geometry:
        if geom is None or geom.is_empty: continue
        if geom.geom_type == 'LineString':
            pts.extend(list(geom.coords))
        elif geom.geom_type == 'MultiLineString':
            for line in geom.geoms: pts.extend(list(line.coords))
    return pts

def compute_metrics(s1_file, s2_file):
    if not os.path.exists(s1_file) or not os.path.exists(s2_file):
        return None
    try:
        s1_gdf = gpd.read_file(s1_file).to_crs("EPSG:32648")
        s2_gdf = gpd.read_file(s2_file).to_crs("EPSG:32648")
        
        s1_pts = np.array(extract_pts(s1_gdf))
        s2_pts = np.array(extract_pts(s2_gdf))
        
        if len(s1_pts) == 0 or len(s2_pts) == 0:
            return None
            
        tree = cKDTree(s2_pts)
        dists, _ = tree.query(s1_pts)
        
        return {
            'N_s1': len(s1_pts),
            'N_s2': len(s2_pts),
            'Mean': float(np.mean(dists)),
            'Median': float(np.percentile(dists, 50)),
            'RMSE': float(np.sqrt(np.mean(dists**2))),
            'P75': float(np.percentile(dists, 75)),
            'P95': float(np.percentile(dists, 95)),
            'Hausdorff': float(np.max(dists))
        }
    except Exception as e:
        print(f"Error computing metrics for {s1_file}: {e}")
        return None

def main():
    print("=============================================================")
    print(" RECALCULATING ALL 20-SEASON VALIDATION METRICS (2017 - 2026)")
    print("=============================================================")
    
    records = []
    
    for yr in range(2017, 2027):
        for ssn in ['dry', 'wet']:
            season_dir = os.path.join(PROJECT_ROOT, "outputs", str(yr), f"{yr}_{ssn}")
            s1_file = os.path.join(season_dir, f"shoreline_{yr}_{ssn}_final.geojson")
            s2_file = os.path.join(season_dir, f"shoreline_{yr}_{ssn}_s2_ref.geojson")
            
            if not os.path.exists(s1_file):
                s1_file = os.path.join(PROJECT_ROOT, "outputs", "others", f"shoreline_{yr}_{ssn}_final.geojson")
            if not os.path.exists(s2_file):
                s2_file = os.path.join(PROJECT_ROOT, "data", f"s2_ref_shoreline_{yr}_{ssn}.geojson")
                
            m = compute_metrics(s1_file, s2_file)
            if m is not None:
                rec = {
                    'Year': yr,
                    'Season': ssn.upper(),
                    'Mean_Error_m': round(m['Mean'], 2),
                    'Median_Error_m': round(m['Median'], 2),
                    'RMSE_m': round(m['RMSE'], 2),
                    'P95_Error_m': round(m['P95'], 2),
                    'Hausdorff_m': round(m['Hausdorff'], 2),
                    'Status': 'SUCCESS'
                }
                records.append(rec)
                
                # Update CSV
                stats_dir = os.path.join(season_dir, "stats")
                os.makedirs(stats_dir, exist_ok=True)
                csv_path = os.path.join(stats_dir, f"validation_statistics_{yr}_{ssn}.csv")
                pd.DataFrame([rec]).to_csv(csv_path, index=False)
                print(f"  [OK] {yr} {ssn.upper()}: Median={m['Median']:.2f}m | Mean={m['Mean']:.2f}m | RMSE={m['RMSE']:.2f}m | P95={m['P95']:.2f}m")
            else:
                print(f"  [WARN] Could not calculate {yr} {ssn.upper()}")
                
    if records:
        df = pd.DataFrame(records)
        
        # Save master multiyear summary reports
        rep_md = "# Báo Cáo Tổng Hợp Trích Xuất Đường Bờ Chuỗi Thời Gian (2017 – 2026)\n\n"
        rep_md += "Bảng tổng hợp chỉ số kiểm chứng vị trí (Positional Validation Metrics) cho 20 mùa (10 năm × 2 mùa) đối chiếu trực tiếp với dữ liệu tham chiếu Sentinel-2 MNDWI:\n\n"
        rep_md += "| Năm (Year) | Mùa (Season) | Mean Error (m) | Median Error (m) | RMSE (m) | P95 Error (m) | Hausdorff (m) | Trạng Thái |\n"
        rep_md += "| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
        for _, r in df.iterrows():
            rep_md += f"| {r['Year']} | **{r['Season']}** | {r['Mean_Error_m']:.2f} | {r['Median_Error_m']:.2f} | **{r['RMSE_m']:.2f}** | {r['P95_Error_m']:.2f} | {r['Hausdorff_m']:.2f} | {r['Status']} |\n"
            
        with open(os.path.join(PROJECT_ROOT, "outputs", "REPORT", "multiyear_shoreline_summary_report.md"), "w", encoding="utf-8") as f:
            f.write(rep_md)
        with open(os.path.join(PROJECT_ROOT, "docs", "multiyear_shoreline_summary_report.md"), "w", encoding="utf-8") as f:
            f.write(rep_md)
            
        print("\n[SUCCESS] Master summary report updated successfully!")

if __name__ == "__main__":
    main()
