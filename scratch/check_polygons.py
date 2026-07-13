import json
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer
import numpy as np

def main():
    with open('aoi/training_polygons.geojson', encoding='utf-8') as f:
        geojson = json.load(f)

    # Group by class
    by_class = {}
    for feature in geojson['features']:
        cls = feature['properties']['class']
        name = feature['properties'].get('className', f'Class {cls}')
        geom = shape(feature['geometry'])
        by_class.setdefault((cls, name), []).append(geom)

    # Project coordinates to EPSG:32648 (UTM Zone 48N) for metric area calculation
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32648", always_xy=True)

    print("| Class ID | Class Name | Total Area (ha) | Avg Area (m²) | Lon Bounds (WGS84) | Lat Bounds (WGS84) |")
    print("| :---: | :--- | :---: | :---: | :--- | :--- |")
    for (cls, name), geoms in sorted(by_class.items()):
        areas = []
        centroids_x = []
        centroids_y = []
        for geom in geoms:
            geom_proj = transform(transformer.transform, geom)
            areas.append(geom_proj.area)
            c = geom.centroid
            centroids_x.append(c.x)
            centroids_y.append(c.y)
        
        total_ha = sum(areas) / 10000.0
        avg_m2 = np.mean(areas)
        lon_str = f"[{min(centroids_x):.4f}, {max(centroids_x):.4f}]"
        lat_str = f"[{min(centroids_y):.4f}, {max(centroids_y):.4f}]"
        print(f"| **{cls}** | {name} | {total_ha:.2f} | {avg_m2:.1f} | {lon_str} | {lat_str} |")

if __name__ == '__main__':
    main()
