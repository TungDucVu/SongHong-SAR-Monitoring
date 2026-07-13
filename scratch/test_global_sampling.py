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
    
    # 2. Sample ALL regions for pixels inside train and validation polygons
    train_samples_all = composite.select(CLASSIFIER_FEATURES).sampleRegions(
        collection=train_polys,
        properties=['class'],
        scale=30,
        projection='EPSG:32648',
        tileScale=16
    )
    
    val_samples_all = composite.select(CLASSIFIER_FEATURES).sampleRegions(
        collection=val_polys,
        properties=['class'],
        scale=30,
        projection='EPSG:32648',
        tileScale=16
    )
    
    train_limits = {1: 700, 2: 1260, 3: 1260, 4: 1260}
    val_limits = {1: 300, 2: 540, 3: 540, 4: 540}
    
    train_samples = ee.FeatureCollection([])
    val_samples = ee.FeatureCollection([])
    
    for c in [1, 2, 3, 4]:
        # Filter, shuffle, and limit for training
        c_train = train_samples_all.filter(ee.Filter.eq('class', c))\
                                   .randomColumn('rand', seed=42)\
                                   .sort('rand')\
                                   .limit(train_limits[c])
        train_samples = train_samples.merge(c_train)
        
        # Filter, shuffle, and limit for validation
        c_val = val_samples_all.filter(ee.Filter.eq('class', c))\
                               .randomColumn('rand', seed=42)\
                               .sort('rand')\
                               .limit(val_limits[c])
        val_samples = val_samples.merge(c_val)
        
    print("\nCounting globally limited sampled pixels per class...")
    for c in [1, 2, 3, 4]:
        train_c = train_samples.filter(ee.Filter.eq('class', c)).size().getInfo()
        val_c = val_samples.filter(ee.Filter.eq('class', c)).size().getInfo()
        print(f"Class {c}: Train={train_c:<4} | Val={val_c:<4} | Total={train_c+val_c:<4}")

if __name__ == '__main__':
    main()
