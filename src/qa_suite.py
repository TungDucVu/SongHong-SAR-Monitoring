"""
QA Suite module for SongHong SAR Monitoring project.
Generates comprehensive visual and statistical verification outputs for Feature Engineering.
"""

import os
import json
import io
import urllib.request
import numpy as np
import matplotlib.pyplot as plt
import folium
import ee
from src.config import (
    WATER_REF_POLYGON, SAND_REF_POLYGON, URBAN_REF_POLYGON, LAND_REF_POLYGON,
    WATER_REF_POLYGONS, SAND_REF_POLYGONS, URBAN_REF_POLYGONS, LAND_REF_POLYGONS,
    CLASSIFIER_FEATURES, PROJECT_ROOT
)

PHASE2_OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'outputs', 'others')
os.makedirs(PHASE2_OUTPUT_DIR, exist_ok=True)


def get_thumb_image(ee_image, vis_params):
    """
    Downloads and reads a PNG thumbnail from GEE.
    """
    url = ee_image.getThumbURL(vis_params)
    with urllib.request.urlopen(url) as response:
        img_bytes = response.read()
    return plt.imread(io.BytesIO(img_bytes), format='png')

def generate_11_feature_maps(composite, aoi_geometry, year, season):
    """
    Creates an interactive HTML map containing Google Satellite, Sentinel-2 RGB,
    and all 11 feature stack layers as toggleable grayscale GEE layers.
    """
    from folium.plugins import MousePosition
    from src.qc import get_s2_rgb_composite

    print(f"  Generating 11-feature interactive map layer sheet...")
    
    # 1. Setup Folium Map centered on Hanoi Red River with scale control
    m = folium.Map(location=[21.04, 105.86], zoom_start=11, control_scale=True)
    
    # Add click coordinate popup and mouse position tracker
    folium.LatLngPopup().add_to(m)
    MousePosition().add_to(m)
    
    # Add Google Satellite Base layer
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # GEE tile layers helper
    def add_ee_layer(folium_map, ee_image_object, vis_params, name, opacity=1.0, show=False):
        try:
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
        except Exception as e:
            print(f"    [Warning] Failed to add GEE layer {name}: {e}")

    # Sentinel-2 RGB layer (bottom)
    s2_img = get_s2_rgb_composite(year, season, aoi_geometry)
    s2_vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
    try:
        band_names = s2_img.bandNames().getInfo()
        if 'B4' in band_names:
            add_ee_layer(m, s2_img, s2_vis, f'Sentinel-2 RGB ({year} {season})', show=True)
    except Exception as e:
        print(f"    [Warning] S2 imagery check failed: {e}")

    # Feature visualization specifications
    vis_specs = {
        'VV': {'min': -22, 'max': -5},
        'VH': {'min': -28, 'max': -10},
        'VV_ratio': {'min': 0, 'max': 15},
        'VV_sum': {'min': -22, 'max': -5},
        'VV_mean': {'min': -22, 'max': -5},
        'VV_contrast': {'min': 0, 'max': 800},
        'VV_entropy': {'min': 0, 'max': 5},
        'VV_homogeneity': {'min': 0, 'max': 1},
        'VV_correlation': {'min': -1, 'max': 1},
        'VV_ASM': {'min': 0, 'max': 1},
        'VV_variance': {'min': 0, 'max': 800}
    }

    # Add each feature band as a grayscale layer (except show VV by default)
    for band in CLASSIFIER_FEATURES:
        spec = vis_specs.get(band, {'min': 0, 'max': 1})
        vis_params = {
            'bands': [band],
            'min': spec['min'],
            'max': spec['max'],
            'palette': ['black', 'white']
        }
        show_by_default = (band == 'VV')
        add_ee_layer(m, composite, vis_params, f'Feature: {band}', opacity=0.8, show=show_by_default)

    # Add AOI Outline
    folium.GeoJson(
        aoi_geometry.getInfo(),
        name="Red River AOI (Hanoi)",
        style_function=lambda x: {'fillColor': 'none', 'color': '#1a73e8', 'weight': 2, 'opacity': 0.8}
    ).add_to(m)
    
    # Add Hanoi Boundary
    hanoi_geojson_path = os.path.join(PROJECT_ROOT, 'aoi', 'hanoi_boundary.geojson')
    if os.path.exists(hanoi_geojson_path):
        try:
            with open(hanoi_geojson_path, 'r', encoding='utf-8') as f:
                hanoi_data = json.load(f)
            folium.GeoJson(
                hanoi_data,
                name="Hanoi Boundary",
                style_function=lambda x: {'fillColor': 'none', 'color': '#ff3300', 'weight': 2.5, 'dashArray': '5, 5', 'opacity': 0.8}
            ).add_to(m)
        except Exception as e:
            print(f"    [Warning] Failed to add Hanoi Boundary: {e}")

    # Add Reference Polygons for manual visual QA
    ref_polygons_groups = [
        ('Water', WATER_REF_POLYGONS, '#1a73e8'),
        ('Sand', SAND_REF_POLYGONS, '#e67e22'),
        ('Urban', URBAN_REF_POLYGONS, '#e74c3c'),
        ('Land', LAND_REF_POLYGONS, '#2ecc71')
    ]
    for class_label, coords_list, color in ref_polygons_groups:
        for idx, coords in enumerate(coords_list):
            folium_coords = [[pt[1], pt[0]] for pt in coords]
            name = f"{class_label} Reference Polygon {idx+1}"
            folium.Polygon(
                locations=folium_coords,
                popup=name,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.35,
                weight=2.5,
                name=name
            ).add_to(m)

    # Add Legend and North Arrow
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 100px; left: 10px; width: 220px; height: 165px; 
                z-index:9999; font-size:12px; background-color:rgba(255, 255, 255, 0.9);
                border: 2px solid grey; border-radius: 6px; padding: 10px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2); font-family: sans-serif;">
        <h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: bold; text-align: center;">Feature Map Legend</h4>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <div style="width: 18px; height: 18px; background-color: #1a73e8; border: 1px solid #000; margin-right: 8px;"></div>
            <span>Red River AOI (Hanoi)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <div style="width: 18px; height: 0px; border-top: 2px dashed #ff3300; margin-right: 8px;"></div>
            <span>Hanoi Province Boundary</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <div style="width: 18px; height: 18px; background: linear-gradient(to right, black, white); border: 1px solid #000; margin-right: 8px;"></div>
            <span>Grayscale Feature scale</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 18px; height: 18px; background-color: #2ca02c; border: 1px solid #000; margin-right: 8px;"></div>
            <span>S2 RGB Composite</span>
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    north_arrow_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 10px; width: 40px; height: 40px; 
                z-index:9999; font-size:16px; background-color:rgba(255, 255, 255, 0.8);
                border: 2px solid grey; border-radius: 4px; padding: 2px;
                text-align: center; font-weight: bold; line-height: 38px; font-family: sans-serif;">
        N ↑
    </div>
    '''
    m.get_root().html.add_child(folium.Element(north_arrow_html))

    folium.LayerControl().add_to(m)
    
    html_path = os.path.join(PHASE2_OUTPUT_DIR, f'feature_maps_{year}_{season}.html')
    m.save(html_path)
    print(f"  [QA] Saved 11-feature map sheet to: {html_path}")
    return html_path

def generate_class_distributions(composite, year, season):
    """
    Samples pixels from Water, Sand, Urban, and Land reference polygons,
    and plots class-differentiated histograms and boxplots.
    """
    print("  Sampling reference polygons for class-based distributions...")
    
    # Define polygon lists
    class_polygons = {
        'Water': WATER_REF_POLYGONS,
        'Sand': SAND_REF_POLYGONS,
        'Urban': URBAN_REF_POLYGONS,
        'Land': LAND_REF_POLYGONS
    }
    
    # Gather samples
    classes_data = {}
    for class_name, coords_list in class_polygons.items():
        classes_data[class_name] = {b: [] for b in CLASSIFIER_FEATURES}
        print(f"    Sampling {class_name} ({len(coords_list)} polygons)...")
        for idx, coords in enumerate(coords_list):
            geom = ee.Geometry.Polygon(coords)
            try:
                # Sample up to 400 pixels per individual polygon
                samples = composite.sample(region=geom, scale=10, numPixels=400, geometries=False).getInfo()
                for f in samples.get('features', []):
                    props = f.get('properties', {})
                    for b in CLASSIFIER_FEATURES:
                        val = props.get(b)
                        if val is not None:
                            classes_data[class_name][b].append(val)
            except Exception as e:
                print(f"      [Warning] Failed to sample from {class_name} polygon {idx+1}: {e}")

    # Color mapping
    colors = {'Water': '#1a73e8', 'Sand': '#e67e22', 'Urban': '#e74c3c', 'Land': '#2ecc71'}

    # 1. Plot histograms
    print("  Generating class overlay histograms plot...")
    fig, axes = plt.subplots(4, 3, figsize=(18, 16))
    axes = axes.ravel()
    
    for i, b in enumerate(CLASSIFIER_FEATURES):
        ax = axes[i]
        for class_name in ['Water', 'Sand', 'Urban', 'Land']:
            vals = classes_data[class_name][b]
            if vals:
                ax.hist(vals, bins=35, alpha=0.5, label=class_name, color=colors[class_name])
        ax.set_title(f"Histogram: {b}", fontsize=12, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.legend(fontsize=8)
        
    if len(CLASSIFIER_FEATURES) < len(axes):
        axes[-1].axis('off')
        
    plt.suptitle(f"Feature Value Histograms per Land Cover Class ({year} {season})", fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    hist_plot_path = os.path.join(PHASE2_OUTPUT_DIR, f'class_histograms_{year}_{season}.png')
    plt.savefig(hist_plot_path, dpi=150)
    plt.close()
    print(f"  [QA] Saved class histograms to: {hist_plot_path}")

    # 2. Plot boxplots
    print("  Generating class boxplots plot...")
    fig, axes = plt.subplots(4, 3, figsize=(18, 16))
    axes = axes.ravel()
    
    for i, b in enumerate(CLASSIFIER_FEATURES):
        ax = axes[i]
        box_data = []
        labels = []
        for class_name in ['Water', 'Sand', 'Urban', 'Land']:
            vals = classes_data[class_name][b]
            if vals:
                box_data.append(vals)
                labels.append(class_name)
        if box_data:
            bp = ax.boxplot(box_data, labels=labels, patch_artist=True)
            # Color box plots
            for patch, class_name in zip(bp['boxes'], labels):
                patch.set_facecolor(colors[class_name])
                patch.set_alpha(0.6)
        ax.set_title(f"Boxplot: {b}", fontsize=12, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.3)
        
    if len(CLASSIFIER_FEATURES) < len(axes):
        axes[-1].axis('off')
        
    plt.suptitle(f"Feature Value Boxplots per Land Cover Class ({year} {season})", fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    box_plot_path = os.path.join(PHASE2_OUTPUT_DIR, f'class_boxplots_{year}_{season}.png')
    plt.savefig(box_plot_path, dpi=150)
    plt.close()
    print(f"  [QA] Saved class boxplots to: {box_plot_path}")
    
    return classes_data

def generate_class_scatter(classes_data, year, season):
    """
    Creates scatter plot of VV vs VV_contrast color-coded by class.
    """
    print("  Generating VV vs VV_contrast scatter plot...")
    colors = {'Water': '#1a73e8', 'Sand': '#e67e22', 'Urban': '#e74c3c', 'Land': '#2ecc71'}
    
    plt.figure(figsize=(10, 8))
    for class_name in ['Water', 'Sand', 'Urban', 'Land']:
        vvs = classes_data[class_name]['VV']
        contrasts = classes_data[class_name]['VV_contrast']
        if len(vvs) == len(contrasts) and len(vvs) > 0:
            plt.scatter(vvs, contrasts, alpha=0.5, label=class_name, color=colors[class_name], s=20)
            
    plt.xlabel('VV Backscatter (dB)', fontsize=12)
    plt.ylabel('VV Contrast Texture', fontsize=12)
    plt.title(f'Feature Scatter: VV vs VV_contrast ({year} {season})', fontsize=14, fontweight='bold')
    plt.legend(fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.3)
    
    scatter_path = os.path.join(PHASE2_OUTPUT_DIR, f'class_scatter_{year}_{season}.png')
    plt.savefig(scatter_path, dpi=150)
    plt.close()
    print(f"  [QA] Saved class scatter plot to: {scatter_path}")
    return scatter_path

def generate_sandbar_zoom(composite, year, season):
    """
    Crops a 1.5km x 1.5km bounding box around the Long Bien sandbar
    and outputs a 2x2 grid display of VV, VV_contrast, VV_entropy, and VV_homogeneity.
    """
    print("  Fetching high-resolution sandbar zoom thumbnail images...")
    
    # Sandbar box: [minLon, minLat, maxLon, maxLat]
    # Centered on Long Bien sandbar
    sandbar_geom = ee.Geometry.Rectangle([105.860, 21.035, 105.875, 21.050])
    
    vis_specs = {
        'VV': {'min': -22, 'max': -5},
        'VV_contrast': {'min': 0, 'max': 800},
        'VV_entropy': {'min': 0, 'max': 5},
        'VV_homogeneity': {'min': 0, 'max': 1}
    }
    
    imgs = {}
    for band, limits in vis_specs.items():
        vis_params = {
            'region': sandbar_geom,
            'scale': 5, # 5m resolution for detailed zoom
            'min': limits['min'],
            'max': limits['max'],
            'format': 'png'
        }
        try:
            imgs[band] = get_thumb_image(composite.select(band), vis_params)
        except Exception as e:
            print(f"    [Warning] Failed to fetch thumbnail for {band}: {e}")
            imgs[band] = None

    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    bands = ['VV', 'VV_contrast', 'VV_entropy', 'VV_homogeneity']
    titles = [
        'VV Backscatter (dB)',
        'VV Contrast Texture',
        'VV Entropy Texture',
        'VV Homogeneity Texture'
    ]
    
    for idx, (band, title) in enumerate(zip(bands, titles)):
        ax = axes[idx // 2, idx % 2]
        img = imgs.get(band)
        if img is not None:
            ax.imshow(img)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.axis('off')
        
    plt.suptitle(f"Sandbar Texture Zoom - Long Bien Reach ({year} {season})", fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    zoom_path = os.path.join(PHASE2_OUTPUT_DIR, f'sandbar_zoom_{year}_{season}.png')
    plt.savefig(zoom_path, dpi=150)
    plt.close()
    print(f"  [QA] Saved sandbar zoom composite to: {zoom_path}")
    return zoom_path

def generate_correlation_heatmap(composite, aoi_geometry, year, season):
    """
    Samples 1,000 pixels inside the AOI and creates a correlation heatmap.
    """
    print("  Sampling AOI for correlation matrix heatmap...")
    samples = composite.sample(region=aoi_geometry, scale=100, numPixels=1000, geometries=False).getInfo()
    
    data = {b: [] for b in CLASSIFIER_FEATURES}
    for f in samples.get('features', []):
        props = f.get('properties', {})
        for b in CLASSIFIER_FEATURES:
            val = props.get(b)
            if val is not None:
                data[b].append(val)
                
    n_samples = len(data['VV'])
    if n_samples < 10:
        print("    [Warning] Too few samples to draw heatmap.")
        return None
        
    matrix = np.corrcoef([data[b] for b in CLASSIFIER_FEATURES])
    
    plt.figure(figsize=(12, 10))
    im = plt.imshow(matrix, cmap='coolwarm', vmin=-1, vmax=1)
    plt.colorbar(im)
    
    tick_marks = np.arange(len(CLASSIFIER_FEATURES))
    plt.xticks(tick_marks, CLASSIFIER_FEATURES, rotation=45, ha='right', fontsize=10)
    plt.yticks(tick_marks, CLASSIFIER_FEATURES, fontsize=10)
    
    for i in range(len(CLASSIFIER_FEATURES)):
        for j in range(len(CLASSIFIER_FEATURES)):
            plt.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", 
                     color="white" if abs(matrix[i, j]) > 0.6 else "black", fontsize=9)
            
    plt.title(f'Feature Correlation Heatmap ({year} {season})', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    heatmap_path = os.path.join(PHASE2_OUTPUT_DIR, f'correlation_heatmap_{year}_{season}.png')
    plt.savefig(heatmap_path, dpi=150)
    plt.close()
    print(f"  [QA] Saved correlation heatmap to: {heatmap_path}")
    return heatmap_path

def generate_random_pixel_inspection(classes_data, year, season):
    """
    Selects 5 random pixels per class and logs them to a markdown file.
    """
    print("  Creating random pixel inspection table...")
    md_content = f"# Feature Value Random Inspection Table ({year} {season})\n\n"
    md_content += "This table lists the values of the 11 feature stack bands for 20 randomly selected pixels (5 per land cover class).\n\n"
    
    # Headers
    headers = ["Class", "Pixel ID"] + CLASSIFIER_FEATURES
    md_content += "| " + " | ".join(headers) + " |\n"
    md_content += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    
    for class_name in ['Water', 'Sand', 'Urban', 'Land']:
        n_available = len(classes_data[class_name]['VV'])
        if n_available == 0:
            continue
        # Randomly pick 5 indices
        indices = np.random.choice(n_available, size=min(5, n_available), replace=False)
        for idx_num, idx in enumerate(indices):
            row = [class_name, f"{class_name.lower()}_{idx_num+1}"]
            for b in CLASSIFIER_FEATURES:
                val = classes_data[class_name][b][idx]
                row.append(f"{val:.2f}")
            md_content += "| " + " | ".join(row) + " |\n"
            
    inspection_path = os.path.join(PHASE2_OUTPUT_DIR, f'feature_inspection_{year}_{season}.md')
    with open(inspection_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    print(f"  [QA] Saved random pixel inspection report to: {inspection_path}")
    return inspection_path

def generate_qa_suite(composite, aoi_geometry, year, season):
    """
    Orchestrates the creation of the entire Phase 2 QA Suite.
    """
    print(f"\n==========================================")
    print(f"       GENERATING PHASE 2 QA SUITE: {year} {season.upper()}")
    print(f"==========================================")
    
    # 1. 11 grayscale maps in one folium HTML map sheet
    generate_11_feature_maps(composite, aoi_geometry, year, season)
    
    # 2. Histograms and Boxplots per class
    classes_data = generate_class_distributions(composite, year, season)
    
    # 3. Scatter plot (VV vs VV_contrast)
    generate_class_scatter(classes_data, year, season)
    
    # 4. Zoom sandbar image (2x2 grid)
    generate_sandbar_zoom(composite, year, season)
    
    # 5. Correlation Heatmap
    generate_correlation_heatmap(composite, aoi_geometry, year, season)
    
    # 6. Random pixel inspection table
    generate_random_pixel_inspection(classes_data, year, season)
    
    print(f"Phase 2 QA Suite generation finished successfully for {year} {season}!")
