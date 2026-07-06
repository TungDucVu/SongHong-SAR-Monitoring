"""
Configuration module for SongHong SAR Monitoring project.
Defines GEE project IDs, dataset settings, temporal ranges, coordinates, and local file paths.
"""

import os

# GEE settings
GEE_PROJECT = 'songhong-sar-monitoring'
ASSET_AOI_PATH = f'projects/{GEE_PROJECT}/assets/song_hong_aoi'

# Sentinel-1 filter settings
S1_COLLECTION = 'COPERNICUS/S1_GRD'
S1_INSTRUMENT_MODE = 'IW'
S1_ORBIT_PASS = 'DESCENDING'
S1_POLARISATIONS = ['VV', 'VH']
S1_BANDS = ['VV', 'VH']

# Temporal settings
START_YEAR = 2017
END_YEAR = 2026

# Seasonal definitions (months)
# Dry season is split into Jan-Apr and Nov-Dec of the same calendar year Y
DRY_SEASON_MONTHS = [1, 2, 3, 4, 11, 12]
WET_SEASON_MONTHS = [5, 6, 7, 8, 9, 10]

# Local directory and file paths
PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
AOI_GEOJSON_PATH = os.path.join(PROJECT_ROOT, 'aoi', 'song_hong_aoi.geojson')
TRAINING_POLYGONS_PATH = os.path.join(PROJECT_ROOT, 'aoi', 'training_polygons.geojson')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'outputs')
METADATA_JSON_PATH = os.path.join(OUTPUT_DIR, 's1_dataset_metadata.json')

# Machine Learning Settings
RF_NUM_TREES = 200
CLASSIFIER_FEATURES = ['VV', 'VH', 'angle', 'VV_VH_ratio', 'VV_VH_diff']
CLASS_LABELS = {
    0: 'Water',
    1: 'Sandbar',
    2: 'Others'
}


# Output asset path template for GEE
# Example: projects/crested-library-500309-i2/assets/s1_composite_2024_dry
ASSET_COMPOSITE_TEMPLATE = f'projects/{GEE_PROJECT}/assets/s1_composite_{{year}}_{{season}}'

# Coordinate reference system and resolution for exporting
EXPORT_CRS = 'EPSG:32648'  # UTM Zone 48N (suitable for Hanoi)
EXPORT_SCALE = 10          # 10m native spatial resolution of Sentinel-1

# Reference validation coordinates (Long Bien river and land check points)
WATER_REF_POINT = [105.8600, 21.0400]
LAND_REF_POINT = [105.8600, 21.0200]

# Reference backscatter dB thresholds for verification
EXPECTED_WATER_VV_MAX = -15.0
EXPECTED_LAND_VV_MIN = -10.0

