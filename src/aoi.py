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

def load_reach_aoi(reach_num):
    """
    Loads reach-specific GeoJSON file (aoi_reach1.geojson, aoi_reach2.geojson, aoi_reach3.geojson)
    and returns it as a Python dict.
    """
    reach_path = os.path.join(os.path.dirname(AOI_GEOJSON_PATH), f"aoi_reach{reach_num}.geojson")
    if not os.path.exists(reach_path):
        raise FileNotFoundError(f"Reach AOI file not found at: {reach_path}")
    with open(reach_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_reach_ee_geometry(reach_num, project_id=None):
    """
    Returns ee.Geometry for a specific Reach (1, 2, or 3).
    """
    if not ee.data.is_initialized():
        ee.Initialize(project=project_id)
    reach_data = load_reach_aoi(reach_num)
    return ee.Geometry(reach_data['features'][0]['geometry'])

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
