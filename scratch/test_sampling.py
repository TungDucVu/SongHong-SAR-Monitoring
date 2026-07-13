import ee
from src.config import GEE_PROJECT, CLASSIFIER_FEATURES
from src.aoi import get_aoi_geometry
from src.collection import create_seasonal_composite
from src.classification import load_training_polygons, train_classifier, classify_image

def main():
    try:
        ee.Initialize(project=GEE_PROJECT)
        print("GEE Initialized")
    except Exception as e:
        print(f"Init failed: {e}")
        return

    aoi = get_aoi_geometry()
    training_fc = load_training_polygons()
    composite = create_seasonal_composite(2024, 'dry', aoi)
    
    best_params = {'numberOfTrees': 200, 'variablesPerSplit': None, 'bagFraction': 0.7}
    final_cf, metrics = train_classifier(training_fc, composite, CLASSIFIER_FEATURES, best_params=best_params)
    classified, max_prob = classify_image(composite, final_cf, CLASSIFIER_FEATURES)

    for scale in [30, 60, 100, 150]:
        print(f"Testing scale={scale}...")
        try:
            samples = classified.sample(
                region=aoi,
                scale=scale,
                numPixels=1000,
                geometries=False
            )
            vals = samples.aggregate_array('classification').getInfo()
            print(f"  SUCCESS! Sample size: {len(vals)}")
            # print class counts
            counts = {}
            for v in vals:
                counts[v] = counts.get(v, 0) + 1
            print(f"  Counts: {counts}")
            break
        except Exception as e:
            print(f"  FAILED: {e}")

if __name__ == '__main__':
    main()
