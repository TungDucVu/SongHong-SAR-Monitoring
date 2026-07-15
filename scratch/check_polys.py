import os
import sys
import ee
import geopandas as gpd
import shapely
from shapely.geometry import shape

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.aoi import get_aoi_geometry
from src.shoreline import load_centerline, refine_classification
from src.collection import create_seasonal_composite
from src.classification import load_training_polygons, train_classifier, classify_image
from src.config import CLASSIFIER_FEATURES, SHORELINE_OPEN_SIZE, SHORELINE_CLOSE_SIZE
from rasterio.features import shapes
import requests
import io
import rasterio

ee.Initialize(project='songhong-sar-monitoring')

aoi = get_aoi_geometry()
centerline_fc = load_centerline()
training_fc = load_training_polygons()

composite = create_seasonal_composite(2024, 'dry', aoi)
best_params = {'numberOfTrees': 300, 'variablesPerSplit': 3, 'bagFraction': 0.5}
classifier, _ = train_classifier(training_fc, composite, CLASSIFIER_FEATURES, best_params)

corridor_geom = centerline_fc.geometry().buffer(2000)
classified, _ = classify_image(composite.clip(corridor_geom), classifier, CLASSIFIER_FEATURES)

water_mask_refined, _, _ = refine_classification(
    classified, aoi, centerline_fc, SHORELINE_OPEN_SIZE, SHORELINE_CLOSE_SIZE
)
water_mask_unmasked = water_mask_refined.unmask(0).eq(1)

url = water_mask_unmasked.clip(corridor_geom).getDownloadURL({
    'scale': 30,
    'crs': 'EPSG:32648',
    'region': corridor_geom.bounds().getInfo(),
    'format': 'GEO_TIFF'
})
r = requests.get(url)
src = rasterio.open(io.BytesIO(r.content))
raster_data = src.read(1)
transform = src.transform

water_geoms = [shape(g) for g, v in shapes(raster_data, transform=transform) if v == 1]
centerline_gdf = gpd.GeoDataFrame.from_features(centerline_fc.getInfo(), crs='EPSG:4326').to_crs('EPSG:32648')
cl_union = centerline_gdf.geometry.unary_union

print(f"Total polygons: {len(water_geoms)}")
print("Polygon ID | Area (ha) | Intersection Length (m)")
for idx, p in enumerate(water_geoms):
    intersect_len = p.intersection(cl_union).length
    if intersect_len > 0 or p.area > 100000:
        print(f"{idx:10d} | {p.area/10000:9.2f} | {intersect_len:23.2f}")
