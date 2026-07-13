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
CENTERLINE_GEOJSON_PATH = os.path.join(PROJECT_ROOT, 'aoi', 'song_hong_centerline.geojson')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'outputs')
METADATA_JSON_PATH = os.path.join(OUTPUT_DIR, 's1_dataset_metadata.json')

# Machine Learning Settings
RF_NUM_TREES = 200
CLASSIFIER_FEATURES = [
    'VV', 'VH', 'VV_ratio', 'VV_sum', 'VV_mean',
    'VV_contrast', 'VV_entropy', 'VV_homogeneity',
    'VV_correlation', 'VV_ASM', 'VV_variance',
    'VH_contrast', 'VH_entropy', 'VH_homogeneity',
    'VH_correlation', 'VH_ASM', 'VH_variance'
]
CLASS_LABELS = {
    1: 'Water',
    2: 'Sand',
    3: 'Built-up',
    4: 'Vegetation'
}


# Output asset path template for GEE
# Example: projects/crested-library-500309-i2/assets/s1_composite_2024_dry
ASSET_COMPOSITE_TEMPLATE = f'projects/{GEE_PROJECT}/assets/s1_composite_{{year}}_{{season}}'

# Coordinate reference system and resolution for exporting
EXPORT_CRS = 'EPSG:32648'  # UTM Zone 48N (suitable for Hanoi)
EXPORT_SCALE = 10          # 10m native spatial resolution of Sentinel-1

# Sentinel-1 IW mode angle limits
S1_IW_ANGLE_MIN = 30.6
S1_IW_ANGLE_MAX = 45.9

# Reference validation coordinates (Long Bien river and land check points/polygons)
WATER_REF_POINT = [105.8600, 21.0400]
LAND_REF_POINT = [105.8600, 21.0200]

# Robust reference polygons (coordinates in WGS 84 [Lon, Lat])
# Small box (~200m) in the active river channel
# Multiple distributed reference polygons (~100m x 100m) per class
# Multiple distributed reference polygons (~100m x 100m) per class
# Multiple distributed reference polygons (~100m x 100m) per class
WATER_REF_POLYGONS = [
    [[105.8540, 21.0560], [105.8560, 21.0560], [105.8560, 21.0580], [105.8540, 21.0580], [105.8540, 21.0560]], # Hanoi reach (Current baseline)
    [[105.4600, 21.1850], [105.4610, 21.1850], [105.4610, 21.1860], [105.4600, 21.1860], [105.4600, 21.1850]], # Upstream Son Tay
    [[105.8950, 20.9550], [105.8960, 20.9550], [105.8960, 20.9560], [105.8950, 20.9560], [105.8950, 20.9550]], # Downstream Thanh Tri
    [[105.7150, 21.1400], [105.7160, 21.1400], [105.7160, 21.1410], [105.7150, 21.1410], [105.7150, 21.1400]], # Mid-channel curve
    [[105.8400, 21.0850], [105.8410, 21.0850], [105.8410, 21.0860], [105.8400, 21.0860], [105.8400, 21.0850]], # Midstream Hanoi
    [[105.5788, 21.1565], [105.5798, 21.1565], [105.5798, 21.1575], [105.5788, 21.1575], [105.5788, 21.1565]], # Upstream curve (vetted)
    [[105.9664, 20.7337], [105.9674, 20.7337], [105.9674, 20.7347], [105.9664, 20.7347], [105.9664, 20.7337]]  # Newest Water polygon (vetted)
]

LAND_REF_POLYGONS = [
    [[105.8596, 21.0354], [105.8606, 21.0354], [105.8606, 21.0364], [105.8596, 21.0364], [105.8596, 21.0354]], # Hanoi agricultural/park
    [[105.4500, 21.2200], [105.4510, 21.2200], [105.4510, 21.2210], [105.4500, 21.2210], [105.4500, 21.2200]], # Upstream crops
    [[105.8950, 20.9500], [105.8960, 20.9500], [105.8960, 20.9510], [105.8950, 20.9510], [105.8950, 20.9500]], # Downstream crops
    [[105.7100, 21.1500], [105.7110, 21.1500], [105.7110, 21.1510], [105.7100, 21.1510], [105.7100, 21.1500]], # Midstream crops
    [[105.8400, 21.0900], [105.8410, 21.0900], [105.8410, 21.0910], [105.8400, 21.0910], [105.8400, 21.0900]], # Midstream Hanoi fields
    [[105.7550, 21.0750], [105.7560, 21.0750], [105.7560, 21.0760], [105.7550, 21.0760], [105.7550, 21.0750]], # Stable vegetation west
    [[105.9307, 20.8578], [105.9317, 20.8578], [105.9317, 20.8588], [105.9307, 20.8588], [105.9307, 20.8578]], # New Land polygon (vetted)
    [[105.9669, 20.7050], [105.9679, 20.7050], [105.9679, 20.7060], [105.9669, 20.7060], [105.9669, 20.7050]]  # Newest Land polygon (vetted)
]

SAND_REF_POLYGONS = [
    [[105.6018, 21.1663], [105.6028, 21.1663], [105.6028, 21.1673], [105.6018, 21.1673], [105.6018, 21.1663]], # Upstream sandbar (User coordinate)
    [[105.9188, 20.7888], [105.9198, 20.7888], [105.9198, 20.7898], [105.9188, 20.7898], [105.9188, 20.7888]], # Sand polygon 2 (vetted)
    [[105.4403, 21.2564], [105.4413, 21.2564], [105.4413, 21.2574], [105.4403, 21.2574], [105.4403, 21.2564]], # Sand polygon 3 (vetted)
    [[105.4308, 21.2722], [105.4318, 21.2722], [105.4318, 21.2732], [105.4308, 21.2732], [105.4308, 21.2722]], # Sand polygon 4 (vetted)
    [[105.3916, 21.2953], [105.3926, 21.2953], [105.3926, 21.2963], [105.3916, 21.2963], [105.3916, 21.2953]], # Sand polygon 5 (vetted)
    [[105.4158, 21.2851], [105.4168, 21.2851], [105.4168, 21.2861], [105.4158, 21.2861], [105.4158, 21.2851]]  # Sand polygon 6 (vetted)
]

URBAN_REF_POLYGONS = [
    [[105.8495, 21.0245], [105.8505, 21.0245], [105.8505, 21.0255], [105.8495, 21.0255], [105.8495, 21.0245]], # Hoan Kiem (Current baseline)
    [[105.4550, 21.2000], [105.4560, 21.2000], [105.4560, 21.2010], [105.4550, 21.2010], [105.4550, 21.2000]], # Upstream urban
    [[105.8759, 20.9491], [105.8769, 20.9491], [105.8769, 20.9501], [105.8759, 20.9501], [105.8759, 20.9491]], # Urban polygon 3 (vetted)
    [[105.7250, 21.1550], [105.7260, 21.1550], [105.7260, 21.1560], [105.7250, 21.1560], [105.7250, 21.1550]], # Midstream urban west
    [[105.8550, 21.0800], [105.8560, 21.0800], [105.8560, 21.0810], [105.8550, 21.0810], [105.8550, 21.0800]], # Midstream urban east
    [[105.5570, 21.1376], [105.5580, 21.1376], [105.5580, 21.1386], [105.5570, 21.1386], [105.5570, 21.1376]]  # Urban polygon 6 (vetted)
]

# Backwards compatibility mapping (points to the first polygon of each class list)
WATER_REF_POLYGON = WATER_REF_POLYGONS[0]
LAND_REF_POLYGON = LAND_REF_POLYGONS[0]
SAND_REF_POLYGON = SAND_REF_POLYGONS[0]
URBAN_REF_POLYGON = URBAN_REF_POLYGONS[0]


# Reference backscatter dB thresholds for verification
EXPECTED_WATER_VV_MAX = -15.0
EXPECTED_WATER_VH_MAX = -22.0
EXPECTED_LAND_VV_MIN = -10.0

# --- Shoreline Extraction Parameters ---
# Kernel size in pixels for morphological opening (clean noise)
SHORELINE_OPEN_SIZE = 2
# Kernel size in pixels for morphological closing (fill gaps)
SHORELINE_CLOSE_SIZE = 3
# Minimum component area in pixels to keep (1000 pixels = 10 ha)
SHORELINE_MIN_COMPONENT_AREA = 1000
# Minimum hole area in pixels to fill
SHORELINE_MIN_HOLE_AREA = 1000
# Snapping distance in meters for topology snapping
SHORELINE_SNAP_DISTANCE = 15.0
# Number of refinements for Chaikin's smoothing
SHORELINE_SMOOTH_ITERATIONS = 3
# Tolerance in meters for Douglas-Peucker simplification
SHORELINE_SIMPLIFY_TOLERANCE = 1.0
# Minimum branch length in meters for pruning dead ends in graph
SHORELINE_MIN_BRANCH_LENGTH = 100.0

# Class values in the input raster
# For GEE 5-class schema: Water=1, Sand=[2, 3]
SHORELINE_GEE_WATER_CLASSES = [1]
SHORELINE_GEE_SAND_CLASSES = [2, 3]

# For user's 4-class schema: Water=1, Sand=[2]
SHORELINE_USER_WATER_CLASSES = [1]
SHORELINE_USER_SAND_CLASSES = [2]

# New Publication-Quality Shoreline Refinement Parameters
# Orientation cosine threshold (cos theta >= 0.5 -> angle <= 60 deg with flow)
SHORELINE_ORIENTATION_THRESHOLD = 0.5
# Snapping distance in meters for bank continuity optimization
SHORELINE_BANK_SNAP_DISTANCE = 150.0
# Minimum branch length in meters for bank graph pruning
SHORELINE_BANK_PRUNE_LENGTH = 200.0
