import os
import sys
import time
import ee
import requests
import io

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    GEE_PROJECT, CLASSIFIER_FEATURES, OUTPUT_DIR
)
from src.aoi import get_aoi_geometry
from src.collection import create_seasonal_composite
from src.classification import load_training_polygons, train_classifier, classify_image
from src.shoreline import load_centerline, refine_classification

def download_image_as_geotiff(ee_image, filename, scale, region_geom):
    print(f"Requesting download URL for {filename} at {scale}m scale...")
    try:
        url = ee_image.getDownloadURL({
            'scale': scale,
            'crs': 'EPSG:32648',
            'region': region_geom.getInfo(),
            'format': 'GEO_TIFF'
        })
        print(f"Downloading {filename}...")
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        
        output_path = os.path.join(OUTPUT_DIR, filename)
        with open(output_path, 'wb') as f:
            f.write(r.content)
        print(f"[Success] Saved to: {output_path} ({len(r.content)} bytes)")
    except Exception as e:
        print(f"[Error] Failed to download {filename}: {e}")

def main():
    print("=============================================================")
    print("   DOWNLOADING WATER AND SAND MASKS (GEOTIFF)   ")
    print("=============================================================")
    
    # 1. Initialize GEE
    if not ee.data.is_initialized():
        ee.Initialize(project=GEE_PROJECT)
    print(f"[GEE] Initialized successfully with project: {GEE_PROJECT}")
    
    aoi_geometry = get_aoi_geometry()
    centerline_fc = load_centerline()
    training_fc = load_training_polygons()
    
    scale = 30
    buffer_geom = centerline_fc.geometry().buffer(2000)
    region_bbox = buffer_geom.bounds()
    
    seasons = {
        'dry': {
            'features': CLASSIFIER_FEATURES,
            'params': {'numberOfTrees': 300, 'variablesPerSplit': 3, 'bagFraction': 0.5}
        },
        'wet': {
            'features': [f for f in CLASSIFIER_FEATURES if not f.startswith('VH_')],
            'params': {'numberOfTrees': 100, 'variablesPerSplit': None, 'bagFraction': 1.0}
        }
    }
    
    for season, config in seasons.items():
        print(f"\n--- Processing 2024 {season.upper()} Season ---")
        composite = create_seasonal_composite(2024, season, aoi_geometry)
        
        final_cf, _ = train_classifier(
            training_fc,
            composite,
            config['features'],
            best_params=config['params']
        )
        
        # Clip and classify
        composite_clipped = composite.clip(buffer_geom)
        classified, _ = classify_image(composite_clipped, final_cf, config['features'])
        
        # Refinement (Phase 4)
        print("Running morphological refinement...")
        water_mask_refined, sand_mask_refined, _ = refine_classification(
            classified=classified,
            aoi_geometry=aoi_geometry,
            centerline_fc=centerline_fc,
            open_radius=2,
            close_radius=3
        )
        
        # Download Water Mask
        water_filename = f"water_mask_2024_{season}.tif"
        download_image_as_geotiff(water_mask_refined.byte(), water_filename, scale, region_bbox)
        
        # Download Sand Mask
        sand_filename = f"sand_mask_2024_{season}.tif"
        download_image_as_geotiff(sand_mask_refined.byte(), sand_filename, scale, region_bbox)

    print("\n[Success] Completed all mask downloads!")

if __name__ == '__main__':
    main()
