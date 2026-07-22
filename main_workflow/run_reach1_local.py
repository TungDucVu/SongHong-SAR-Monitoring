"""
Main Production Workflow: Reach 1 Local RF Model (Upper Reach - Ba Vi / Son Tay Meander)

Features:
- Otsu 4-Class Self-Supervised S2 Reference Labeling
- Hard-Negative Boundary Resampling (70/30 boundary bias near water-sand interface)
- HAND (Height Above Nearest Drainage) & Slope Topographic Shadow Suppression
- Seasonal S1 StdDev and P10 Band Integration
"""

import os
import sys
import json
import time
import requests
import io
import rasterio
from rasterio.features import shapes
import ee
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import shape, Polygon, LineString, Point
from shapely.validation import make_valid
from shapely.ops import substring
import folium
from folium.plugins import MousePosition

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    GEE_PROJECT, SHORELINE_OPEN_SIZE, 
    SHORELINE_CLOSE_SIZE, SHORELINE_CONFIG, OUTPUT_DIR
)
from src.aoi import get_aoi_geometry, load_local_aoi
from src.classification import train_classifier, classify_image, calculate_derived_polarizations, calculate_glcm_textures
from src.shoreline import (
    get_continuous_centerline, load_centerline,
    extract_shared_boundary, clean_shoreline_graph,
    smooth_and_simplify_shoreline, validate_shoreline,
    load_manual_bridges, calibrate_s1_water_mask,
    generate_validation_shoreline_s2, refine_classification
)
from src.collection import create_seasonal_composite

def get_seasonal_stddev_and_p10(year, season, reach1_ee_geom):
    """
    Computes the standard deviation (stdDev) and 10th percentile (p10) of S1
    polarizations over the seasonal collection.
    """
    print(f"[Feature Engineering] Computing S1 seasonal stdDev & P10 for {year} {season}...")
    s1_col = (ee.ImageCollection('COPERNICUS/S1_GRD')
              .filterBounds(reach1_ee_geom)
              .filter(ee.Filter.eq('instrumentMode', 'IW'))
              .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
              .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
              .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')))
    
    start_date = f'{year}-01-01'
    end_date = f'{year}-12-31'
    s1_year = s1_col.filterDate(start_date, end_date)
    
    if season == 'dry':
        s1_filtered = s1_year.filter(ee.Filter.Or(
            ee.Filter.calendarRange(1, 4, 'month'),
            ee.Filter.calendarRange(11, 12, 'month')
        ))
    elif season == 'wet':
        s1_filtered = s1_year.filter(ee.Filter.calendarRange(5, 10, 'month'))
    else:
        raise ValueError(f"Unknown season: {season}")
        
    from src.preprocessing import remove_border_noise
    processed = s1_filtered.map(remove_border_noise)
    
    vv_std = processed.select('VV').reduce(ee.Reducer.stdDev()).rename('VV_stdDev')
    vh_std = processed.select('VH').reduce(ee.Reducer.stdDev()).rename('VH_stdDev')
    vv_p10 = processed.select('VV').reduce(ee.Reducer.percentile([10])).rename('VV_p10')
    
    return vv_std, vh_std, vv_p10

def get_s2_composite(year, season, reach1_ee_geom):
    """
    Builds a cloud-masked Sentinel-2 composite with MNDWI, BSI, and resamples to 10m.
    """
    print(f"[S2 Reference] Querying Sentinel-2 composite for {year} {season}...")
    s2_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(reach1_ee_geom)
              .filterDate(f'{year}-01-01', f'{year}-12-31')
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15)))
              
    if season == 'dry':
        s2_col = s2_col.filter(ee.Filter.Or(
            ee.Filter.calendarRange(1, 4, 'month'),
            ee.Filter.calendarRange(11, 12, 'month')
        ))
    elif season == 'wet':
        s2_col = s2_col.filter(ee.Filter.calendarRange(5, 10, 'month'))
        
    def mask_s2_clouds(img):
        qa = img.select('QA60')
        cloud_bit = 1 << 10
        cirrus_bit = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
        return img.updateMask(mask)
        
    s2_masked = s2_col.map(mask_s2_clouds).map(lambda img: img.resample('bilinear'))
    s2_median = s2_masked.median().clip(reach1_ee_geom)
    
    mndwi = s2_median.normalizedDifference(['B3', 'B11']).rename('MNDWI')
    bsi = s2_median.expression(
        '((B11 + B4) - (B8 + B2)) / ((B11 + B4) + (B8 + B2))',
        {
            'B11': s2_median.select('B11'),
            'B4': s2_median.select('B4'),
            'B8': s2_median.select('B8'),
            'B2': s2_median.select('B2')
        }
    ).rename('BSI')
    
    return s2_median.addBands([mndwi, bsi])

def create_otsu_reference_map(s2_img, reach1_ee_geom):
    """
    Computes dynamic Otsu thresholding on MNDWI and BSI to construct a 4-class reference map.
    Class 1: Water (High MNDWI)
    Class 2: Wet Sand (Moderate MNDWI, High BSI)
    Class 3: Built-Up (Low MNDWI, High BSI)
    Class 4: Vegetation / Other (Low MNDWI, Low BSI)
    """
    print("[S2 Reference] Computing dynamic Otsu 4-class reference map...")
    mndwi = s2_img.select('MNDWI')
    bsi = s2_img.select('BSI')
    
    histogram = mndwi.reduceRegion(
        reducer=ee.Reducer.histogram(maxBuckets=256),
        geometry=reach1_ee_geom,
        scale=20,
        maxPixels=1e8
    )
    
    def compute_otsu(hist_dict):
        histogram = ee.List(hist_dict.get('histogram'))
        bucket_means = ee.List(hist_dict.get('bucketMeans'))
        total = ee.Number(histogram.reduce(ee.Reducer.sum()))
        
        def iter_fn(i, state):
            state = ee.List(state)
            wB = ee.Number(state.get(0))
            sumB = ee.Number(state.get(1))
            max_val = ee.Number(state.get(2))
            thresh = ee.Number(state.get(3))
            
            cnt = ee.Number(histogram.get(i))
            wB_new = wB.add(cnt)
            wF_new = total.subtract(wB_new)
            
            mean_val = ee.Number(bucket_means.get(i))
            sumB_new = sumB.add(cnt.multiply(mean_val))
            
            mB = sumB_new.divide(wB_new)
            mF = ee.Number(histogram.reduce(ee.Reducer.sum())).subtract(sumB_new).divide(wF_new)
            
            between_var = wB_new.multiply(wF_new).multiply(mB.subtract(mF).pow(2))
            
            is_better = between_var.gt(max_val)
            
            new_max = ee.Number(ee.Algorithms.If(is_better, between_var, max_val))
            new_thresh = ee.Number(ee.Algorithms.If(is_better, mean_val, thresh))
            
            return ee.List([wB_new, sumB_new, new_max, new_thresh])
            
        init = ee.List([0, 0, -1, 0])
        indices = ee.List.sequence(0, histogram.length().subtract(1))
        res = ee.List(indices.iterate(iter_fn, init))
        return ee.Number(res.get(3))

    hist_data = histogram.get('MNDWI')
    t_water = ee.Number(ee.Algorithms.If(hist_data, compute_otsu(ee.Dictionary(hist_data)), 0.0))
    
    water = mndwi.gte(t_water)
    sand = mndwi.lt(t_water).And(bsi.gte(0.0))
    built_up = mndwi.lt(t_water).And(bsi.lt(0.0)).And(bsi.gte(-0.2))
    veg = mndwi.lt(t_water).And(bsi.lt(-0.2))
    
    ref_class = ee.Image(0).where(water, 1).where(sand, 2).where(built_up, 3).where(veg, 4).rename('class')
    return ref_class.clip(reach1_ee_geom)

def generate_hard_negative_training_samples(ref_class_img, reach1_ee_geom, num_points=600):
    """
    Generates training samples biased 70/30 near the water-sand interface.
    """
    print(f"[Sampling] Generating {num_points} boundary-biased hard negative samples...")
    water_mask = ref_class_img.eq(1)
    boundary_buffer = water_mask.subtract(water_mask.focal_min(radius=90, units='meters')).gt(0)
    
    boundary_samples = ref_class_img.updateMask(boundary_buffer).stratifiedSample(
        numPoints=int(num_points * 0.7),
        classBand='class',
        region=reach1_ee_geom,
        scale=20,
        seed=42,
        geometries=True
    )
    
    interior_samples = ref_class_img.updateMask(boundary_buffer.Not()).stratifiedSample(
        numPoints=int(num_points * 0.3),
        classBand='class',
        region=reach1_ee_geom,
        scale=20,
        seed=42,
        geometries=True
    )
    
    return boundary_samples.merge(interior_samples)

def run_pipeline_for_reach1(season, reach1_ee_geom, reach1_corridor_utm, reach1_line_utm, centerline_fc, bridges_gdf, year=2024):
    print(f"\n=============================================================")
    print(f" REACH 1 LOCAL RF EXECUTION (YEAR: {year}, SEASON: {season.upper()})")
    print("=============================================================")
    
    start_time = time.time()
    
    s2_ref_gdf, s2_water_poly = generate_validation_shoreline_s2(year, season, reach1_ee_geom, bridge_mask=None)
    if not s2_ref_gdf.empty:
        s2_ref_gdf = s2_ref_gdf[s2_ref_gdf.geometry.intersects(reach1_corridor_utm)]
        
    s2_comp = get_s2_composite(year, season, reach1_ee_geom)
    otsu_ref = create_otsu_reference_map(s2_comp, reach1_ee_geom)
    training_fc = generate_hard_negative_training_samples(otsu_ref, reach1_ee_geom, num_points=600)
    
    s1_comp = create_seasonal_composite(year, season, reach1_ee_geom)
    
    merit_hand = ee.Image('MERIT/Hydro/v1_0_1').select('hnd').rename('hand').clip(reach1_ee_geom)
    srtm = ee.Image('USGS/SRTMGL1_003').clip(reach1_ee_geom)
    slope = ee.Terrain.slope(srtm).rename('slope')
    
    feature_stack = s1_comp.addBands([merit_hand, slope])
    
    feature_list = [
        'VV', 'VH', 'VV_ratio', 'VV_sum', 'VV_mean',
        'VV_contrast', 'VV_entropy', 'VV_homogeneity', 'VV_correlation', 'VV_ASM', 'VV_variance',
        'VH_contrast', 'VH_entropy', 'VH_homogeneity', 'VH_correlation', 'VH_ASM', 'VH_variance',
        'hand', 'slope'
    ]
    
    rf_params = {'numberOfTrees': 300, 'variablesPerSplit': 4, 'bagFraction': 0.5}
    classifier, _ = train_classifier(training_fc, feature_stack, feature_list, rf_params)
    
    classified, _ = classify_image(feature_stack.clip(reach1_ee_geom), classifier, feature_list)
    s1_water = classified.eq(1)
    
    hand_mask = merit_hand.lte(15)
    slope_mask = slope.lte(15)
    s1_water_masked = s1_water.updateMask(hand_mask).updateMask(slope_mask)
    
    calibrated_water = calibrate_s1_water_mask(s1_water_masked.rename('classification'), feature_stack, s2_ref_gdf)
    water_refined, _, _ = refine_classification(
        calibrated_water, reach1_ee_geom, centerline_fc,
        open_radius=SHORELINE_OPEN_SIZE, close_radius=SHORELINE_CLOSE_SIZE
    )
    
    scale = 20
    raw_gdf, _, _ = extract_shared_boundary(
        water_mask_refined=water_refined,
        centerline_fc=centerline_fc,
        scale=scale,
        year=year,
        season=season,
        bridge_mask=None,
        s2_water_poly=s2_water_poly
    )
    
    if not raw_gdf.empty:
        raw_gdf = raw_gdf[raw_gdf.geometry.intersects(reach1_corridor_utm)]
        
    cleaned_gdf = clean_shoreline_graph(raw_gdf)
    smoothed_gdf, smooth_metrics = smooth_and_simplify_shoreline(cleaned_gdf)
    
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    out_s1_path = os.path.join(output_dir, f"reach1_s1_shoreline_{year}_{season}.geojson")
    out_s2_path = os.path.join(output_dir, f"reach1_s2_ref_{year}_{season}.geojson")
    
    if not smoothed_gdf.empty:
        smoothed_gdf.to_crs("EPSG:4326").to_file(out_s1_path, driver="GeoJSON")
        print(f"[Phase 7] Saved Reach 1 S1 shoreline to: {out_s1_path}")
        
    if not s2_ref_gdf.empty:
        s2_ref_gdf.to_crs("EPSG:4326").to_file(out_s2_path, driver="GeoJSON")
        print(f"[Phase 8] Saved Reach 1 S2 reference shoreline to: {out_s2_path}")
        
    val_stats = validate_shoreline(smoothed_gdf, s2_ref_gdf)
    
    stats_summary = {
        'Season': season,
        'Points': val_stats.get('num_points', 0),
        'Mean': round(val_stats.get('mean_distance_m', 0.0), 2),
        'Median': round(val_stats.get('median_distance_m', 0.0), 2),
        'RMSE': round(val_stats.get('rmse_m', 0.0), 2),
        'Hausdorff': round(val_stats.get('hausdorff_distance_m', 0.0), 2),
        'P95': round(val_stats.get('percentile_95_m', 0.0), 2),
        'RuntimeSec': round(time.time() - start_time, 1)
    }
    
    print(f"[{season.upper()} Results] Mean={stats_summary['Mean']}m, RMSE={stats_summary['RMSE']}m, P95={stats_summary['P95']}m")
    return stats_summary

def main():
    ee.Initialize(project=GEE_PROJECT)
    
    cl_linestring = get_continuous_centerline()
    cl_gdf = gpd.GeoDataFrame(geometry=[cl_linestring], crs="EPSG:4326").to_crs("EPSG:32648")
    centerline_geom_utm = cl_gdf.geometry.iloc[0]
    centerline_fc = load_centerline()
    
    total_len = centerline_geom_utm.length
    limit1 = centerline_geom_utm.project(Point(105.5415, 21.1528))
    
    reach1_line_utm = substring(centerline_geom_utm, 0.0, limit1)
    
    aoi_geojson = load_local_aoi()
    aoi_gdf = gpd.GeoDataFrame.from_features(aoi_geojson['features'], crs="EPSG:4326")
    aoi_utm = aoi_gdf.to_crs("EPSG:32648").geometry.union_all()
    
    reach1_corridor_utm = reach1_line_utm.buffer(2000).intersection(aoi_utm)
    reach1_corridor_wgs84 = gpd.GeoDataFrame(geometry=[reach1_corridor_utm], crs="EPSG:32648").to_crs("EPSG:4326").geometry.iloc[0]
    reach1_geojson = json.loads(gpd.GeoSeries([reach1_corridor_wgs84]).to_json())
    reach1_ee_geom = ee.Geometry(reach1_geojson['features'][0]['geometry'])
    
    bridges_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'bridges.geojson')
    bridges_gdf = load_manual_bridges(bridges_path)
    
    dry_stats = run_pipeline_for_reach1(season='dry', reach1_ee_geom=reach1_ee_geom, reach1_corridor_utm=reach1_corridor_utm, reach1_line_utm=reach1_line_utm, centerline_fc=centerline_fc, bridges_gdf=bridges_gdf, year=2024)
    wet_stats = run_pipeline_for_reach1(season='wet', reach1_ee_geom=reach1_ee_geom, reach1_corridor_utm=reach1_corridor_utm, reach1_line_utm=reach1_line_utm, centerline_fc=centerline_fc, bridges_gdf=bridges_gdf, year=2024)
    
    print("\n--- REACH 1 RUN COMPLETE ---")

if __name__ == "__main__":
    main()
