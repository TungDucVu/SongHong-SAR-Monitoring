"""
Configuration module for SongHong SAR Monitoring project.
Defines GEE project IDs, dataset settings, temporal ranges, coordinates, and local file paths.
"""

import os

# GEE settings
GEE_PROJECT = 'crested-library-500309-i2'
ASSET_AOI_PATH = f'projects/{GEE_PROJECT}/assets/song_hong_aoi'

# Sentinel-1 filter settings
S1_COLLECTION = 'COPERNICUS/S1_GRD'
S1_INSTRUMENT_MODE = 'IW'
S1_ORBIT_PASS = 'DESCENDING'
S1_POLARISATIONS = ['VV', 'VH']
S1_BANDS = ['VV', 'VH']

# Temporal settings
START_DATE = '2015-01-01'
END_DATE = '2024-12-31'

# Local directory and file paths
PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
AOI_GEOJSON_PATH = os.path.join(PROJECT_ROOT, 'aoi', 'song_hong_aoi.geojson')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'outputs')

# Coordinate reference system and resolution for exporting
EXPORT_CRS = 'EPSG:32648'  # UTM Zone 48N (suitable for Hanoi)
EXPORT_SCALE = 10          # 10m native spatial resolution of Sentinel-1

# Reference validation coordinates (Long Bien river and land check points)
WATER_REF_POINT = [105.8600, 21.0400]
LAND_REF_POINT = [105.8600, 21.0200]

# Reference backscatter dB thresholds for verification
EXPECTED_WATER_VV_MAX = -15.0
EXPECTED_LAND_VV_MIN = -10.0
