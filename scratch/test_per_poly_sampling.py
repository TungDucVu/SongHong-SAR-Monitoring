import ee
from src.config import GEE_PROJECT, CLASSIFIER_FEATURES
from src.aoi import get_aoi_geometry
from src.classification import load_training_polygons
from src.collection import create_seasonal_composite

def main():
    ee.Initialize(project=GEE_PROJECT)
    
    aoi_geometry = get_aoi_geometry()
    training_fc = load_training_polygons()
    
    # Split
    training_fc = training_fc.randomColumn('split_rand', seed=42)
    train_polys = training_fc.filter(ee.Filter.lt('split_rand', 0.7))
    val_polys = training_fc.filter(ee.Filter.gte('split_rand', 0.7))
    
    composite = create_seasonal_composite(2024, 'dry', aoi_geometry)
    
    def sample_collection(polys):
        def sample_single_poly(poly):
            cls = ee.Number(poly.get('class'))
            limit = ee.Number(
                ee.Algorithms.If(cls.eq(1), 13,
                ee.Algorithms.If(cls.eq(2), 15,
                ee.Algorithms.If(cls.eq(3), 30,
                23)))
            )
            
            samples = composite.select(CLASSIFIER_FEATURES).sampleRegions(
                collection=ee.FeatureCollection([poly]),
                properties=['class'],
                scale=30,
                projection='EPSG:32648',
                tileScale=16
            )
            
            return samples.limit(limit)
            
        return polys.map(sample_single_poly).flatten()

    train_samples = sample_collection(train_polys)
    val_samples = sample_collection(val_polys)
    
    print("\nCounting sampled pixels per class...")
    for c in [1, 2, 3, 4]:
        train_c = train_samples.filter(ee.Filter.eq('class', c)).size().getInfo()
        val_c = val_samples.filter(ee.Filter.eq('class', c)).size().getInfo()
        print(f"Class {c}: Train={train_c:<4} | Val={val_c:<4} | Total={train_c+val_c:<4}")

if __name__ == '__main__':
    main()
