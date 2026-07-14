import sys
import os
import time
import ee
import requests
import zipfile
import io
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd

sys.path.insert(0, os.getcwd())

from src.config import GEE_PROJECT, CLASSIFIER_FEATURES
from src.aoi import get_aoi_geometry
from src.collection import create_seasonal_composite
from src.classification import load_training_polygons, train_classifier, classify_image
from src.shoreline import load_centerline

def main():
    ee.Initialize(project=GEE_PROJECT)
    aoi_geometry = get_aoi_geometry()
    centerline_fc = load_centerline()
    training_fc = load_training_polygons()
    
    composite = create_seasonal_composite(2024, 'dry', aoi_geometry)
    final_cf, _ = train_classifier(
        training_fc,
        composite,
        CLASSIFIER_FEATURES,
        best_params={'numberOfTrees': 300, 'variablesPerSplit': 3, 'bagFraction': 0.5}
    )
    
    buffer_geom = centerline_fc.geometry().buffer(2000)
    composite_clipped = composite.clip(buffer_geom)
    classified, _ = classify_image(composite_clipped, final_cf, CLASSIFIER_FEATURES)
    
    # Clip to buffer
    classified_clipped = classified.clip(buffer_geom)
    
    bbox = buffer_geom.bounds()
    print("Requesting download URL from GEE...")
    url = classified_clipped.getDownloadURL({
        'scale': 30,
        'crs': 'EPSG:32648',
        'region': bbox.getInfo(),
        'format': 'GEO_TIFF'
    })
    print("Downloading zip...")
    r = requests.get(url, timeout=300)
    if r.status_code != 200:
        print(f"Error status code: {r.status_code}")
        print(f"Error text: {r.text}")
    r.raise_for_status()
    print("Downloaded successfully. Unzipping...")
    
    print(f"Response size: {len(r.content)} bytes")
    print(f"Content-Type: {r.headers.get('Content-Type')}")
    if not r.content.startswith(b'PK'):
        print(f"First 200 bytes: {r.content[:200]}")
    tiff_bytes = r.content
    
    print("Reading geotiff...")
    with rasterio.open(io.BytesIO(tiff_bytes)) as src:
        raster_data = src.read(1)
        transform = src.transform
        nodata = src.nodata
        print(f"Raster shape: {raster_data.shape}, NoData value: {nodata}")
        
    print("Polygonizing...")
    water_geoms = []
    sand_geoms = []
    
    for geom, val in shapes(raster_data, transform=transform):
        if val == 1:
            water_geoms.append(shape(geom))
        elif val == 2:
            sand_geoms.append(shape(geom))
            
    print(f"Extracted {len(water_geoms)} water and {len(sand_geoms)} sand polygons locally!")

if __name__ == '__main__':
    main()
