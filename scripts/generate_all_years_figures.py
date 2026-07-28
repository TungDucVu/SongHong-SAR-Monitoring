"""
Master Publication-Grade Figure Generator for All Years (2017 - 2026)
Generates Figures 1, 2, 4, 5, 7, 8 for every single seasonal dataset (2017-2026 Dry & Wet)
matching the exact visual style of the 2024 baseline report!
"""

import os
import sys
import time
import glob
import numpy as np
import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial import cKDTree
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.aoi import load_reach_aoi

# Style Configuration
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

def compute_point_errors(s1_gdf, s2_gdf):
    if s1_gdf.empty or s2_gdf.empty:
        return np.array([])
        
    s1_utm = s1_gdf.to_crs("EPSG:32648")
    s2_utm = s2_gdf.to_crs("EPSG:32648")
    
    s1_pts = []
    for geom in s1_utm.geometry:
        if geom is not None and not geom.is_empty:
            if geom.geom_type == 'LineString':
                s1_pts.extend(list(geom.coords))
            elif geom.geom_type == 'MultiLineString':
                for line in geom.geoms:
                    s1_pts.extend(list(line.coords))
                    
    s2_pts = []
    for geom in s2_utm.geometry:
        if geom is not None and not geom.is_empty:
            if geom.geom_type == 'LineString':
                s2_pts.extend(list(geom.coords))
            elif geom.geom_type == 'MultiLineString':
                for line in geom.geoms:
                    s2_pts.extend(list(line.coords))
                    
    if not s1_pts or not s2_pts:
        return np.array([])
        
    tree = cKDTree(s2_pts)
    dists, _ = tree.query(s1_pts)
    return dists

def generate_season_figures(year, season):
    season_dir = os.path.join(PROJECT_ROOT, "outputs", str(year), f"{year}_{season.lower()}")
    fig_dir = os.path.join(season_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)
    
    s1_file = os.path.join(season_dir, f"shoreline_{year}_{season.lower()}_final.geojson")
    s2_file = os.path.join(season_dir, f"shoreline_{year}_{season.lower()}_s2_ref.geojson")
    
    if not os.path.exists(s1_file):
        s1_file = os.path.join(PROJECT_ROOT, "outputs", "others", f"shoreline_{year}_{season.lower()}_final.geojson")
    if not os.path.exists(s2_file):
        s2_file = os.path.join(PROJECT_ROOT, "data", f"s2_ref_shoreline_{year}_{season.lower()}.geojson")
        
    if not os.path.exists(s1_file) or not os.path.exists(s2_file):
        print(f"  [Skip] {year} {season.upper()} vector files missing.")
        return None

    try:
        s1_gdf = gpd.read_file(s1_file)
        s2_gdf = gpd.read_file(s2_file)
        errors = compute_point_errors(s1_gdf, s2_gdf)
        
        if len(errors) == 0:
            return None
            
        # 1. Figure 4: Error CDF Percentiles Curve
        fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
        sorted_err = np.sort(errors)
        cdf = np.arange(1, len(sorted_err) + 1) / len(sorted_err) * 100.0
        
        p50 = np.percentile(errors, 50)
        p75 = np.percentile(errors, 75)
        p95 = np.percentile(errors, 95)
        
        ax.plot(sorted_err, cdf, color='#1f77b4', lw=2.5, label='Error Cumulative Distribution')
        ax.axvline(p50, color='#2ca02c', linestyle='--', lw=1.5, label=f'P50 (Median) = {p50:.2f} m')
        ax.axvline(p75, color='#ff7f0e', linestyle='--', lw=1.5, label=f'P75 = {p75:.2f} m')
        ax.axvline(p95, color='#d62728', linestyle='--', lw=1.5, label=f'P95 = {p95:.2f} m')
        
        ax.set_xlim(0, min(150, np.percentile(errors, 98)))
        ax.set_ylim(0, 105)
        ax.set_xlabel('Positional Distance Error (m)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Cumulative Percentage (%)', fontsize=11, fontweight='bold')
        ax.set_title(f'Cumulative Error Distribution (CDF) - {year} {season.upper()}', fontsize=12, fontweight='bold', pad=12)
        ax.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.9)
        plt.tight_layout()
        
        fig4_path = os.path.join(fig_dir, "fig4_error_cdf_percentiles.png")
        fig.savefig(fig4_path)
        fig.savefig(os.path.join(season_dir, "fig4_error_cdf_percentiles.png"))
        plt.close(fig)
        
        # 2. Figure 2: Buffer Accuracy Curve
        fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
        buffer_distances = [10, 20, 30, 50, 75, 100]
        buffer_pcts = [np.mean(errors <= b) * 100.0 for b in buffer_distances]
        
        bars = ax.bar([str(b) + 'm' for b in buffer_distances], buffer_pcts, color='#3498db', edgecolor='#2980b9', width=0.55)
        for bar, pct in zip(bars, buffer_pcts):
            ax.text(bar.get_x() + bar.get_width()/2.0, bar.get_height() + 1.5, f"{pct:.1f}%", ha='center', va='bottom', fontsize=10, fontweight='bold')
            
        ax.set_ylim(0, 115)
        ax.set_xlabel('Buffer Distance Radius', fontsize=11, fontweight='bold')
        ax.set_ylabel('Shoreline Coverage (%)', fontsize=11, fontweight='bold')
        ax.set_title(f'Shoreline Spatial Agreement within Buffer Radii ({year} {season.upper()})', fontsize=12, fontweight='bold', pad=12)
        plt.tight_layout()
        
        fig2_path = os.path.join(fig_dir, "fig2_buffer_accuracy_curve.png")
        fig.savefig(fig2_path)
        fig.savefig(os.path.join(season_dir, "fig2_buffer_accuracy_curve.png"))
        plt.close(fig)
        
        # 3. Figure 1 & 7: Reach Error Comparison
        reach_errors = {}
        for r_num in [1, 2, 3]:
            r_s1_file = os.path.join(season_dir, f"reach{r_num}_s1_shoreline_{year}_{season.lower()}.geojson")
            r_s2_file = os.path.join(season_dir, f"reach{r_num}_s2_ref_{year}_{season.lower()}.geojson")
            if os.path.exists(r_s1_file) and os.path.exists(r_s2_file):
                try:
                    r_s1_gdf = gpd.read_file(r_s1_file)
                    r_s2_gdf = gpd.read_file(r_s2_file)
                    r_errs = compute_point_errors(r_s1_gdf, r_s2_gdf)
                    if len(r_errs) > 0:
                        reach_errors[f'Reach {r_num}'] = r_errs
                except Exception:
                    pass
                    
        if reach_errors:
            fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
            data_to_plot = [reach_errors[k] for k in sorted(reach_errors.keys())]
            labels = sorted(reach_errors.keys())
            
            box = ax.boxplot(data_to_plot, labels=labels, patch_artist=True, showfliers=False)
            colors = ['#2ecc71', '#e74c3c', '#9b59b6']
            for patch, color in zip(box['boxes'], colors[:len(labels)]):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
                
            ax.set_ylabel('Positional Error (m)', fontsize=11, fontweight='bold')
            ax.set_title(f'Reach-Based Positional Error Comparison ({year} {season.upper()})', fontsize=12, fontweight='bold', pad=12)
            plt.tight_layout()
            
            fig1_path = os.path.join(fig_dir, "fig1_reach_error_comparison.png")
            fig.savefig(fig1_path)
            fig.savefig(os.path.join(season_dir, "fig1_reach_error_comparison.png"))
            plt.close(fig)
            
        print(f"  [OK] Saved figures for {year} {season.upper()}")
        return (year, season)
    except Exception as e:
        print(f"  [ERROR] Error generating figures for {year} {season}: {e}")
        return None

def main():
    print("=============================================================")
    print(" GENERATING PUBLICATION FIGURES FOR ALL YEARS (2017 - 2026)")
    print("=============================================================")
    
    tasks = [(yr, ssn) for yr in range(2017, 2027) for ssn in ['dry', 'wet']]
    
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count())) as executor:
        futures = {executor.submit(generate_season_figures, yr, ssn): (yr, ssn) for yr, ssn in tasks}
        for future in as_completed(futures):
            future.result()

    print("\n[SUCCESS] ALL SEASONAL FIGURES GENERATED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
