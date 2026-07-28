"""
Multi-Year Trend Analysis & Chart Generator (2017 - 2026)

Generates publication-grade scientific charts for multi-year shoreline dynamics,
surface water area fluctuations, positional validation metrics, and reach-wise performance.
Saves PNG figures directly to outputs/REPORT/figures/.
"""

import os
import sys
import glob
import re
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
FIGURES_DIR = os.path.join(OUTPUTS_DIR, "REPORT", "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

# Set global matplotlib style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 300

def parse_all_seasonal_data(start_year=2017, end_year=2026):
    data_dir = os.path.join(PROJECT_ROOT, 'data')
    config_dir = os.path.join(PROJECT_ROOT, '.config')
    
    records = []
    
    for yr in range(start_year, end_year + 1):
        for ssn in ['dry', 'wet']:
            season_dir = os.path.join(OUTPUTS_DIR, str(yr), f"{yr}_{ssn}")
            poly_file = os.path.join(data_dir, f"s2_water_poly_{yr}_{ssn}.geojson")
            line_file = os.path.join(season_dir, f"shoreline_{yr}_{ssn}_final.geojson")
            stats_file = os.path.join(config_dir, f"{yr}_{ssn}_stats.md")
            
            area_km2 = np.nan
            length_km = np.nan
            island_count = 0
            
            if os.path.exists(poly_file):
                try:
                    poly_gdf = gpd.read_file(poly_file)
                    area_km2 = poly_gdf.geometry.to_crs('EPSG:32648').area.sum() / 1e6
                except Exception:
                    pass
                    
            if os.path.exists(line_file):
                try:
                    line_gdf = gpd.read_file(line_file)
                    length_km = line_gdf.geometry.to_crs('EPSG:32648').length.sum() / 1e3
                    if 'is_island' in line_gdf.columns:
                        island_count = int(len(line_gdf[line_gdf['is_island'] == True]))
                except Exception:
                    pass
                    
            # Parse stats from CSV or MD
            mean_m, median_m, rmse_m, p95_m, hausdorff_m = np.nan, np.nan, np.nan, np.nan, np.nan
            csv_candidates = [
                os.path.join(OUTPUTS_DIR, str(yr), f"{yr}_{ssn}", "stats", f"validation_statistics_{yr}_{ssn}.csv"),
                os.path.join(OUTPUTS_DIR, str(yr), f"{yr}_{ssn}", f"validation_statistics_{yr}_{ssn}.csv")
            ]
            
            parsed = False
            for cp in csv_candidates:
                if os.path.exists(cp):
                    try:
                        cdf = pd.read_csv(cp)
                        if not cdf.empty:
                            row = cdf.iloc[0]
                            mean_m = float(row.get('Mean_Error_m', row.get('Mean', np.nan)))
                            median_m = float(row.get('Median_Error_m', row.get('Median', np.nan)))
                            rmse_m = float(row.get('RMSE_m', row.get('RMSE', np.nan)))
                            p95_m = float(row.get('P95_Error_m', row.get('P95', np.nan)))
                            hausdorff_m = float(row.get('Hausdorff_m', row.get('Hausdorff', np.nan)))
                            parsed = True
                            break
                    except Exception:
                        pass
                        
            if not parsed and os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    txt = f.read()
                    m1 = re.search(r'- \*\*Mean Error\*\*: ([\d\.]+) m', txt)
                    m2 = re.search(r'- \*\*Median \(P50\) Error\*\*: ([\d\.]+) m', txt)
                    m3 = re.search(r'- \*\*RMSE\*\*: ([\d\.]+) m', txt)
                    m4 = re.search(r'- \*\*95th Percentile \(P95\)\*\*: ([\d\.]+) m', txt)
                    m5 = re.search(r'- \*\*Hausdorff Distance\*\*: ([\d\.]+) m', txt)
                    
                    if m1: mean_m = float(m1.group(1))
                    if m2: median_m = float(m2.group(1))
                    if m3: rmse_m = float(m3.group(1))
                    if m4: p95_m = float(m4.group(1))
                    if m5: hausdorff_m = float(m5.group(1))
                    
            records.append({
                'Year': yr,
                'Season': ssn.upper(),
                'Label': f"{yr} {ssn.upper()}",
                'Water Area (km2)': area_km2,
                'Shoreline Length (km)': length_km,
                'Island Count': island_count,
                'Mean Error (m)': mean_m,
                'Median Error (m)': median_m,
                'RMSE (m)': rmse_m,
                'P95 Error (m)': p95_m,
                'Hausdorff (m)': hausdorff_m
            })
            
    return pd.DataFrame(records)

def generate_charts(df):
    print("[Plotting] Generating multi-year trend charts (2017-2026)...")
    
    years = np.array(sorted(df['Year'].unique()))
    dry_df = df[df['Season'] == 'DRY'].sort_values('Year').reset_index(drop=True)
    wet_df = df[df['Season'] == 'WET'].sort_values('Year').reset_index(drop=True)
    
    # 1. Surface Water Area Trend (Dry vs Wet Season Comparison)
    fig, ax = plt.subplots(figsize=(10, 5))
    dry_plot_df = dry_df[dry_df['Water Area (km2)'] > 20.0]
    
    ax.plot(dry_plot_df['Year'], dry_plot_df['Water Area (km2)'], marker='o', linewidth=2.5, color='#1abc9c', label='Dry Season (Mùa Khô)')
    ax.plot(wet_df['Year'], wet_df['Water Area (km2)'], marker='s', linewidth=2.5, color='#e74c3c', label='Wet Season (Mùa Mưa)')
    
    # Annotate extreme events
    ax.annotate('Lũ Lịch Sử 2017\n(84.91 km²)', xy=(2017, 84.91), xytext=(2017.2, 87),
                arrowprops=dict(facecolor='#e74c3c', shrink=0.08, width=1.5, headwidth=6),
                fontsize=9.5, fontweight='bold', color='#c0392b')
                
    ax.annotate('Siêu Bão Yagi 2024\n(79.07 km²)', xy=(2024, 79.07), xytext=(2023.2, 83),
                arrowprops=dict(facecolor='#e74c3c', shrink=0.08, width=1.5, headwidth=6),
                fontsize=9.5, fontweight='bold', color='#c0392b')
                
    ax.set_title('Biến Động Diện Tích Mặt Nước Sông Hồng Theo Chuỗi Thời Gian (2017 – 2026)', fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel('Năm (Year)', fontsize=11, fontweight='bold', labelpad=10)
    ax.set_ylabel('Diện Tích Mặt Nước (km²)', fontsize=11, fontweight='bold', labelpad=10)
    ax.set_xticks(years)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10.5)
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    fig_path1 = os.path.join(FIGURES_DIR, 'fig_multiyear_water_area_trend.png')
    plt.savefig(fig_path1, dpi=300)
    plt.close()
    print(f"  Saved: {fig_path1}")

    # 2. Positional Accuracy Metrics Trend (RMSE & Median Error)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dry_df['Year'], dry_df['RMSE (m)'], marker='o', linestyle='-', color='#2980b9', linewidth=2.2, label='Dry Season RMSE (m)')
    ax.plot(wet_df['Year'], wet_df['RMSE (m)'], marker='s', linestyle='--', color='#e67e22', linewidth=2.2, label='Wet Season RMSE (m)')
    ax.plot(dry_df['Year'], dry_df['Median Error (m)'], marker='^', linestyle=':', color='#27ae60', linewidth=2.0, label='Dry Season Median (P50) Error (m)')
    ax.plot(wet_df['Year'], wet_df['Median Error (m)'], marker='v', linestyle=':', color='#c0392b', linewidth=2.0, label='Wet Season Median (P50) Error (m)')
    
    ax.axhline(y=30, color='#7f8c8d', linestyle='--', linewidth=1.2, label='Ngưỡng Chuẩn Tốt (< 30m / 3 pixels)')
    ax.set_title('Xu Hướng Sai Số Vị Trí Đường Bờ SAR vs. S2 Reference (2017 – 2026)', fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel('Năm (Year)', fontsize=11, fontweight='bold', labelpad=10)
    ax.set_ylabel('Sai Số Vị Trí (Meters)', fontsize=11, fontweight='bold', labelpad=10)
    ax.set_xticks(years)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5, loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    fig_path2 = os.path.join(FIGURES_DIR, 'fig_multiyear_positional_accuracy_trend.png')
    plt.savefig(fig_path2, dpi=300)
    plt.close()
    print(f"  Saved: {fig_path2}")

    # 3. Shoreline Length & Island Count Dynamics
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax2 = ax1.twinx()
    
    dry_plot_len = dry_df[dry_df['Shoreline Length (km)'] > 100.0]
    
    l1 = ax1.plot(dry_plot_len['Year'], dry_plot_len['Shoreline Length (km)'], marker='o', color='#8e44ad', linewidth=2.2, label='Dry Season Length (km)')
    l2 = ax1.plot(wet_df['Year'], wet_df['Shoreline Length (km)'], marker='s', color='#34495e', linewidth=2.2, linestyle='--', label='Wet Season Length (km)')
    
    b1 = ax2.bar(dry_df['Year'] - 0.15, dry_df['Island Count'], width=0.3, color='#f39c12', alpha=0.6, label='Dry Island Count')
    b2 = ax2.bar(wet_df['Year'] + 0.15, wet_df['Island Count'], width=0.3, color='#d35400', alpha=0.6, label='Wet Island Count')
    
    ax1.set_title('Biến Động Chiều Dài Đường Bờ Vector & Số Lượng Cù Lao/Bãi Nổi (2017 – 2026)', fontsize=13, fontweight='bold', pad=15)
    ax1.set_xlabel('Năm (Year)', fontsize=11, fontweight='bold', labelpad=10)
    ax1.set_ylabel('Chiều Dài Đường Bờ (km)', fontsize=11, fontweight='bold', color='#8e44ad', labelpad=10)
    ax2.set_ylabel('Số Lượng Cù Lao / Bãi Nổi', fontsize=11, fontweight='bold', color='#d35400', labelpad=10)
    ax1.set_xticks(years)
    ax2.set_yticks(range(0, 7))
    
    # Combined legend for twin axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)
    
    ax1.grid(True, linestyle='--', alpha=0.4)
    plt.tight_layout()
    fig_path3 = os.path.join(FIGURES_DIR, 'fig_multiyear_shoreline_length_and_islands.png')
    plt.savefig(fig_path3, dpi=300)
    plt.close()
    print(f"  Saved: {fig_path3}")


def main():
    df = parse_all_seasonal_data(2017, 2026)
    generate_charts(df)

if __name__ == '__main__':
    main()
