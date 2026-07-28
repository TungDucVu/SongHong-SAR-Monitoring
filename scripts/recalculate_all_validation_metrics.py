"""
Recalculate exact 3-reach validation metrics across all 20 seasons (2017-2026)
using exact KD-Tree distance between S1 Random Forest shoreline and S2 reference shoreline.
"""

import os
import sys
import glob
import pandas as pd
import geopandas as gpd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.shoreline import validate_shoreline

def recalculate_metrics():
    print("=============================================================")
    print(" RECALCULATING ALL VALIDATION METRICS (2017 - 2026)")
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
                
            if os.path.exists(s1_file) and os.path.exists(s2_file):
                try:
                    s1_gdf = gpd.read_file(s1_file)
                    s2_gdf = gpd.read_file(s2_file)
                    
                    val_stats = validate_shoreline(s1_gdf, s2_gdf)
                    
                    mean_e = val_stats.get('mean_dist_m', 0.0)
                    med_e = val_stats.get('median_dist_m', 0.0)
                    rmse_e = val_stats.get('rmse_dist_m', 0.0)
                    p95_e = val_stats.get('p95_dist_m', 0.0)
                    h_e = val_stats.get('hausdorff_dist_m', 0.0)
                    
                    rec = {
                        'Year': yr,
                        'Season': ssn.upper(),
                        'Mean_Error_m': mean_e,
                        'Median_Error_m': med_e,
                        'RMSE_m': rmse_e,
                        'P95_Error_m': p95_e,
                        'Hausdorff_m': h_e,
                        'Status': 'SUCCESS'
                    }
                    records.append(rec)
                    
                    # Update local CSV
                    stats_dir = os.path.join(season_dir, "stats")
                    os.makedirs(stats_dir, exist_ok=True)
                    csv_path = os.path.join(stats_dir, f"validation_statistics_{yr}_{ssn}.csv")
                    pd.DataFrame([rec]).to_csv(csv_path, index=False)
                    print(f"  [OK] {yr} {ssn.upper()}: Mean={mean_e:.2f}m | Median={med_e:.2f}m | RMSE={rmse_e:.2f}m | P95={p95_e:.2f}m")
                except Exception as e:
                    print(f"  [ERROR] {yr} {ssn.upper()} error: {e}")
            else:
                print(f"  ⚠️ {yr} {ssn.upper()} files missing.")

    if records:
        df = pd.DataFrame(records)
        print("\n=============================================================")
        print(" CONSOLIDATED 10-YEAR VALIDATION SUMMARY (2017 - 2026)")
        print("=============================================================")
        print(df.to_string(index=False))
        
        # Save master multiyear report
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

if __name__ == "__main__":
    recalculate_metrics()
