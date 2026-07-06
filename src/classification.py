"""
Classification module for SongHong SAR Monitoring project.
Handles loading training polygons, programmatically sampling 'Others' from GEE Dynamic World,
training and evaluating a 200-tree Random Forest classifier, and generating visual Folium maps.
"""

import json
import os
import ee
import folium
import matplotlib.pyplot as plt
import pandas as pd
from src.config import (
    TRAINING_POLYGONS_PATH, CLASSIFIER_FEATURES, CLASS_LABELS,
    EXPORT_SCALE, OUTPUT_DIR, RF_NUM_TREES
)

def load_training_polygons():
    """
    Loads manual ground truth polygons from local GeoJSON and returns as ee.FeatureCollection.
    """
    if not os.path.exists(TRAINING_POLYGONS_PATH):
        raise FileNotFoundError(f"Training polygons not found at {TRAINING_POLYGONS_PATH}. Run scripts/generate_training_polygons.py first.")
        
    with open(TRAINING_POLYGONS_PATH, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
        
    # Convert local GeoJSON directly to ee.FeatureCollection
    training_features = ee.FeatureCollection(geojson_data)
    return training_features

def sample_others_from_dynamic_world(aoi, water_sandbar_polygons, year):
    """
    Programmatically extracts 'Others' class samples (class 2) from Google Dynamic World V1
    excluding regions covered by the manual Water and Sandbar polygons.
    """
    print("[GEE] Fetching Dynamic World V1 LULC for programmatically sampling 'Others'...")
    
    # Load Dynamic World
    dw_col = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1') \
               .filterBounds(aoi) \
               .filterDate(f'{year}-01-01', f'{year}-12-31')
    
    # Mode label for the year
    dw_label = dw_col.select('label').mode().clip(aoi)
    
    # Define 'Others' mask: Trees(1), Grass(2), Crops(4), Shrub(5), Built(6), Bare(7)
    others_mask = dw_label.eq(1) \
        .Or(dw_label.eq(2)) \
        .Or(dw_label.eq(4)) \
        .Or(dw_label.eq(5)) \
        .Or(dw_label.eq(6)) \
        .Or(dw_label.eq(7))
        
    # Exclude area of manual Water and Sandbar polygons to prevent label leakage
    polygons_mask = water_sandbar_polygons.reduceToImage(
        properties=['class'],
        reducer=ee.Reducer.first()
    ).mask().Not()
    
    # Final Others mask
    final_others_mask = others_mask.And(polygons_mask)
    
    # Create Others image with constant value 2 (Others class code)
    others_image = ee.Image.constant(2).rename('class').updateMask(final_others_mask).clip(aoi)
    
    # Sample points from the Others image
    others_samples = others_image.sample(
        region=aoi,
        scale=10,
        numPixels=1500,  # robust sample size representing land
        seed=42,
        geometries=True
    )
    
    # Map to set className property
    def set_properties(f):
        return f.set({
            'class': 2,
            'className': 'Others'
        })
    others_fc = others_samples.map(set_properties)
    print(f"[GEE] Programmatically extracted {others_fc.size().getInfo()} 'Others' points from Dynamic World.")
    return others_fc

def prepare_training_samples(composite, water_sandbar_polygons, others_fc):
    """
    Samples pixel values from the Sentinel-1 composite.
    - Water & Sandbar are sampled inside the manually approved polygons.
    - Others are sampled at the points extracted from GEE Dynamic World.
    """
    # Sample Water & Sandbar inside their polygons
    water_sandbar_samples = composite.select(CLASSIFIER_FEATURES).sampleRegions(
        collection=water_sandbar_polygons,
        properties=['class', 'className'],
        scale=10,
        tileScale=4
    )
    
    # Sample Others (we need to extract values at points)
    others_samples = composite.select(CLASSIFIER_FEATURES).sampleRegions(
        collection=others_fc,
        properties=['class', 'className'],
        scale=10,
        tileScale=4
    )
    
    # Merge both feature collections
    merged_samples = water_sandbar_samples.merge(others_samples)
    return merged_samples

def plot_class_feature_histograms(composite, water_sandbar_polygons, others_fc, year, season):
    """
    Plots pre-training histograms of VV and VH bands to inspect class separability (QA).
    """
    print("[QC] Sampling pixels for class feature histogram check...")
    
    # Sample a small, manageable number of pixels for plotting
    water_sandbar_plot = composite.select(['VV', 'VH']).sampleRegions(
        collection=water_sandbar_polygons,
        properties=['className'],
        scale=20, # larger scale to get fewer pixels for plotting
        tileScale=4
    )
    others_plot = composite.select(['VV', 'VH']).sampleRegions(
        collection=others_fc.limit(500), # limit to 500 points
        properties=['className'],
        scale=10,
        tileScale=4
    )
    
    merged = water_sandbar_plot.merge(others_plot).getInfo().get('features', [])
    
    data = []
    for f in merged:
        props = f.get('properties', {})
        if 'VV' in props and 'VH' in props and 'className' in props:
            data.append({
                'Class': props['className'],
                'VV': props['VV'],
                'VH': props['VH']
            })
            
    df = pd.DataFrame(data)
    if df.empty:
        print("[WARNING] No samples found for histogram plotting.")
        return None
        
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    colors = {'Water': '#1a73e8', 'Sandbar': '#ffd700', 'Others': '#228b22'}
    
    for class_name, group in df.groupby('Class'):
        color = colors.get(class_name, '#808080')
        axes[0].hist(group['VV'], bins=30, alpha=0.5, label=class_name, color=color)
        axes[1].hist(group['VH'], bins=30, alpha=0.5, label=class_name, color=color)
        
    axes[0].set_title(f'VV Backscatter Distribution ({year} {season.upper()})')
    axes[0].set_xlabel('VV (dB)')
    axes[0].set_ylabel('Pixel Count')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    axes[1].set_title(f'VH Backscatter Distribution ({year} {season.upper()})')
    axes[1].set_xlabel('VH (dB)')
    axes[1].set_ylabel('Pixel Count')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plot_path = os.path.join(OUTPUT_DIR, f'class_feature_histograms_{year}_{season}.png')
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"[QC] Class feature histograms saved to: {plot_path}")
    return plot_path

def train_and_evaluate(samples, split_ratio=0.7):
    """
    Splits samples 70/30, trains Random Forest model, and returns classifier and performance metrics.
    """
    # Add a random column for splitting
    samples_with_random = samples.randomColumn('random')
    
    # Split
    training_samples = samples_with_random.filter(ee.Filter.lt('random', split_ratio))
    validation_samples = samples_with_random.filter(ee.Filter.gte('random', split_ratio))
    
    training_size = training_samples.size().getInfo()
    validation_size = validation_samples.size().getInfo()
    
    # Train RF
    classifier = ee.Classifier.smileRandomForest(RF_NUM_TREES).train(
        features=training_samples,
        classProperty='class',
        inputProperties=CLASSIFIER_FEATURES
    )
    
    # Validate
    validated = validation_samples.classify(classifier)
    
    # Metrics
    error_matrix = validated.errorMatrix('class', 'classification')
    
    overall_accuracy = error_matrix.accuracy().getInfo()
    kappa = error_matrix.kappa().getInfo()
    confusion_matrix = error_matrix.getInfo()
    producer_accuracy = error_matrix.producersAccuracy().getInfo()
    user_accuracy = error_matrix.consumersAccuracy().getInfo()
    
    # Feature Importance
    explain = classifier.explain().getInfo()
    feature_importance = explain.get('importance', {})
    
    # Normalize importance to sum to 1
    total_imp = sum(feature_importance.values())
    if total_imp > 0:
        feature_importance = {k: v / total_imp for k, v in feature_importance.items()}
        
    metrics = {
        'training_size': training_size,
        'validation_size': validation_size,
        'overall_accuracy': overall_accuracy,
        'kappa': kappa,
        'confusion_matrix': confusion_matrix,
        'producer_accuracy': producer_accuracy,
        'user_accuracy': user_accuracy,
        'feature_importance': feature_importance
    }
    
    return classifier, metrics

def generate_classification_html(composite, classified, year, season, aoi_geometry, valid_polygons, metrics):
    """
    Generates the final interactive Folium classification map.
    Layers stack: Classification (top) -> Sentinel-1 VV (middle, 50% transparent) -> Sentinel-2 True Color -> Google Satellite (bottom).
    """
    m = folium.Map(location=[21.04, 105.86], zoom_start=11)
    
    # 1. Base Layer: Google Satellite
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite (Latest)',
        overlay=False,
        control=True
    ).add_to(m)
    
    def add_ee_layer(folium_map, ee_image_object, vis_params, name, opacity=1.0, show=True):
        map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
        folium.raster_layers.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Google Earth Engine',
            name=name,
            overlay=True,
            control=True,
            opacity=opacity,
            show=show
        ).add_to(folium_map)
        
    # Fetch Sentinel-2 true-color composite for the specified year and season
    print(f"[GEE] Fetching Sentinel-2 True Color composite for {year} {season.upper()}...")
    s2_col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(aoi_geometry) \
        .filter(ee.Filter.calendarRange(year, year, 'year'))
    
    if season.lower() == 'dry':
        filter_months = ee.Filter.Or(
            ee.Filter.calendarRange(1, 4, 'month'),
            ee.Filter.calendarRange(11, 12, 'month')
        )
    else:
        filter_months = ee.Filter.calendarRange(5, 10, 'month')
        
    s2_col = s2_col.filter(filter_months) \
                   .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                   
    def mask_s2_clouds(image):
        qa = image.select('QA60')
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit_mask).eq(0) \
            .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
        return image.updateMask(mask)
        
    masked_col = s2_col.map(mask_s2_clouds)
    s2_composite = ee.Image(ee.Algorithms.If(
        masked_col.size().gt(0),
        masked_col.median(),
        s2_col.median()
    )).clip(aoi_geometry)
    
    s2_vis = {
        'bands': ['B4', 'B3', 'B2'],
        'min': 0,
        'max': 3000,
        'gamma': 1.4
    }
    
    # 2. Historical Background Layer: Sentinel-2 True Color (2024 Seasonal)
    add_ee_layer(m, s2_composite, s2_vis, f'Sentinel-2 True Color ({year} {season.upper()})', opacity=1.0, show=True)
    
    # 3. Middle Layer: Raw Sentinel-1 VV
    s1_vis = {'bands': ['VV'], 'min': -22, 'max': -5, 'palette': ['black', 'white']}
    add_ee_layer(m, composite, s1_vis, f'Sentinel-1 VV ({year} {season.upper()})', opacity=0.5, show=False)
    
    # 4. Post-Processing Pipeline
    # 4.1. Majority Filter (Smoothing classification)
    majority_classified = classified.focalMode(20, 'circle', 'meters')
    
    # 4.2. Water Mask & Morphological Opening (Erosion -> Dilation)
    water_mask = majority_classified.eq(0)
    eroded_water = water_mask.focalMin(20, 'circle', 'meters')
    opened_water = eroded_water.focalMax(20, 'circle', 'meters')
    
    # 4.3. Connected Components & Remove Small Patches (gte 50 pixels = 0.5 ha)
    pixel_count = opened_water.connectedPixelCount(1024, True)
    clean_water_mask = opened_water.updateMask(pixel_count.gte(50))
    
    # 4.4. Polygon Vectorization
    display_water_mask = clean_water_mask.selfMask()
    water_polygons = display_water_mask.reduceToVectors(
        geometry=aoi_geometry,
        scale=10,
        geometryType='polygon',
        eightConnected=True,
        labelProperty='water',
        maxPixels=1e8
    )

    # Visual palettes
    class_vis = {
        'min': 0,
        'max': 2,
        'palette': ['0000ff', 'ffd700', '228b22']
    }
    
    # Add Raw Classification Layer (hidden by default)
    add_ee_layer(m, classified.clip(aoi_geometry), class_vis, f'Raw RF Classification ({year} {season.upper()})', opacity=0.5, show=False)
    
    # Add Majority Filtered Classification Layer (visible by default)
    add_ee_layer(m, majority_classified.clip(aoi_geometry), class_vis, f'RF Classification (Majority Filtered) ({year} {season.upper()})', opacity=0.6, show=True)
    
    # Add Cleaned Water Mask Layer
    water_vis = {'palette': ['00a2ff']}
    add_ee_layer(m, display_water_mask.clip(aoi_geometry), water_vis, f'Cleaned Water Mask ({year} {season.upper()})', opacity=0.7, show=False)
    
    # Add Vector/Raster Shoreline Layer
    try:
        print("[GEE] Fetching vector Shoreline GeoJSON from GEE...")
        shoreline_geojson = water_polygons.getInfo()
        folium.GeoJson(
            shoreline_geojson,
            name=f'Shoreline / Đường bờ (Vector) ({year} {season.upper()})',
            style_function=lambda x: {
                'fillColor': 'none',
                'fillOpacity': 0.0,
                'color': '#ff0055',
                'weight': 3.0,
                'opacity': 1.0
            }
        ).add_to(m)
        print("[GEE] Vector Shoreline added to Folium map.")
    except Exception as e:
        print(f"[GEE WARNING] Failed to vectorize shoreline: {e}. Falling back to raster shoreline.")
        shoreline_raster = ee.Algorithms.CannyEdgeDetector(clean_water_mask, 0.5, 1).selfMask()
        shoreline_vis = {'palette': ['ff0055']}
        add_ee_layer(m, shoreline_raster.clip(aoi_geometry), shoreline_vis, f'Shoreline / Đường bờ (Raster) ({year} {season.upper()})', opacity=1.0, show=True)
    
    # 5. Overlaid Layer: Training Polygons (Reference)
    def style_poly(feature):
        c_code = feature['properties']['class']
        fill_color = '#0000ff' if c_code == 0 else ('#ffd700' if c_code == 1 else '#228b22')
        return {
            'fillColor': fill_color,
            'color': '#000000',
            'weight': 2.0,
            'fillOpacity': 0.4
        }
        
    folium.GeoJson(
        valid_polygons.getInfo(),
        name="Training Polygons (Water/Sandbar)",
        style_function=style_poly,
        tooltip=folium.GeoJsonTooltip(
            fields=['id', 'className', 'area_ha'],
            aliases=['Polygon ID:', 'Class:', 'Area (ha):'],
            localize=True
        )
    ).add_to(m)
    
    # AOI boundary outline
    folium.GeoJson(
        aoi_geometry.getInfo(),
        name="Study Area AOI (Hanoi)",
        style_function=lambda x: {'fillColor': 'none', 'color': '#1a73e8', 'weight': 2.5, 'opacity': 0.8}
    ).add_to(m)
    
    # Legend
    legend_html = f"""
     <div style="position: fixed; 
     bottom: 50px; left: 50px; width: 260px; height: 230px; 
     border:2px solid grey; z-index:9999; font-size:13px;
     background-color:white;
     opacity: 0.95;
     padding: 10px;
     border-radius: 5px;">
     <b>Phân Loại LULC Sông Hồng 2024</b><br>
     <i class="fa fa-square" style="color:#0000ff; margin-right:5px;"></i> Lớp Nước (Water)<br>
     <i class="fa fa-square" style="color:#ffd700; margin-right:5px;"></i> Lớp Bãi Cát (Sandbar)<br>
     <i class="fa fa-square" style="color:#228b22; margin-right:5px;"></i> Lớp Khác (Others)<br>
     <i class="fa fa-minus" style="color:#ff0055; margin-right:5px; font-weight:bold;"></i> Đường bờ (Shoreline)<br>
     <hr style="margin:5px 0;">
     <span>Mùa: <b>{season.upper()} {year}</b></span><br>
     <span>Overall Accuracy: <b>{metrics['overall_accuracy']*100:.2f}%</b></span><br>
     <span>Kappa: <b>{metrics['kappa']:.4f}</b></span>
     </div>
     """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add Layer Control
    folium.LayerControl().add_to(m)
    
    # Save the output HTML
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    html_path = os.path.join(OUTPUT_DIR, f'classification_{year}_{season}.html')
    m.save(html_path)
    print(f"[ML] Classification map saved to: {html_path}")
    return html_path
