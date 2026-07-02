import sys
import os

sys.path.insert(0, os.getcwd())

import ee
from src.config import GEE_PROJECT, ASSET_COMPOSITE_TEMPLATE

print("Initializing GEE...")
ee.Initialize(project=GEE_PROJECT)

years = range(2017, 2027)
seasons = ['dry', 'wet']

deleted_count = 0
for year in years:
    for season in seasons:
        asset_path = ASSET_COMPOSITE_TEMPLATE.format(year=year, season=season)
        try:
            # Check if asset exists
            ee.data.getAsset(asset_path)
            print(f"Found old/incorrect asset: {asset_path}. Deleting...")
            ee.data.deleteAsset(asset_path)
            print(f"Deleted: {asset_path}")
            deleted_count += 1
        except Exception:
            # Asset does not exist, which is fine
            pass

print(f"Cleanup finished. Deleted {deleted_count} assets.")
