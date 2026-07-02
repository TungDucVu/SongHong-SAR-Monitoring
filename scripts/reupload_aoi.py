import sys
import os
import json
import time

sys.path.insert(0, os.getcwd())

import ee
from src.config import GEE_PROJECT, ASSET_AOI_PATH, AOI_GEOJSON_PATH
from src.aoi import load_local_aoi

print("Initializing GEE...")
ee.Initialize(project=GEE_PROJECT)

# 1. Delete old asset if it exists
try:
    print(f"Checking if GEE asset already exists at {ASSET_AOI_PATH}...")
    ee.data.getAsset(ASSET_AOI_PATH)
    print("Found! Deleting old asset...")
    ee.data.deleteAsset(ASSET_AOI_PATH)
    print("Old asset deleted successfully.")
except Exception as e:
    print(f"Asset does not exist or failed to delete: {e}")

# 2. Upload new asset
print(f"Loading local GeoJSON: {AOI_GEOJSON_PATH}...")
geojson_data = load_local_aoi()
fc = ee.FeatureCollection(geojson_data)

print(f"Submitting GEE table export task to: {ASSET_AOI_PATH}...")
task = ee.batch.Export.table.toAsset(
    collection=fc,
    description='Re_Export_AOI_to_Asset_Week2',
    assetId=ASSET_AOI_PATH
)
task.start()

print(f"GEE Task started! ID: {task.id}")
print("Waiting for task completion...")

# Poll task status until complete
while True:
    status = task.status()
    state = status.get('state')
    print(f"Current task state: {state}")
    if state in ['COMPLETED', 'SUCCEEDED']:
        print("AOI Asset uploaded successfully!")
        break
    elif state in ['FAILED', 'CANCELLED']:
        print("Error: AOI upload task failed!")
        print(status)
        sys.exit(1)
    time.sleep(10)
