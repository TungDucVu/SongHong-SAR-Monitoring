"""
AOI module for SongHong SAR Monitoring.
Handles loading local GeoJSON and manages uploading AOI to Google Earth Engine Assets.
"""

import json
import os
import ee
from src.config import AOI_GEOJSON_PATH, ASSET_AOI_PATH

def load_local_aoi():
    """
    Loads local GeoJSON file and returns it as a Python dict.
    """
    if not os.path.exists(AOI_GEOJSON_PATH):
        raise FileNotFoundError(f"AOI GeoJSON file not found at: {AOI_GEOJSON_PATH}")
    
    with open(AOI_GEOJSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_aoi_collection(project_id=None):
    """
    Returns ee.FeatureCollection of the AOI.
    Loads directly from the local GeoJSON file to guarantee consistency.
    """
    # Initialize ee if not already initialized
    if not ee.data.is_initialized():
        ee.Initialize(project=project_id)
        
    geojson_data = load_local_aoi()
    aoi_fc = ee.FeatureCollection(geojson_data)
    return aoi_fc

def get_aoi_geometry(project_id=None):
    """
    Returns ee.Geometry of the AOI.
    """
    return get_aoi_collection(project_id).geometry()

def sync_aoi_to_assets(project_id=None):
    """
    Checks if AOI exists in GEE Assets. If not, submits an Export task to upload it.
    """
    if not ee.data.is_initialized():
        ee.Initialize(project=project_id)
        
    try:
        # Check if asset exists
        ee.data.getAsset(ASSET_AOI_PATH)
        print(f"[AOI] Asset already exists at: {ASSET_AOI_PATH}")
        return True
    except Exception:
        print(f"[AOI] Asset not found. Submitting export task to upload it...")
        geojson_data = load_local_aoi()
        fc = ee.FeatureCollection(geojson_data)
        
        # Start export task
        task = ee.batch.Export.table.toAsset(
            collection=fc,
            description='Export_AOI_to_Asset',
            assetId=ASSET_AOI_PATH
        )
        task.start()
        print(f"[AOI] Started GEE task to upload AOI. Task ID: {task.id}")
        print(f"      Monitor task progress at: https://code.earthengine.google.com/tasks")
        return False
