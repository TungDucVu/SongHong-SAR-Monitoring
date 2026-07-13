import ee
import json
from src.config import GEE_PROJECT, CLASSIFIER_FEATURES
from src.aoi import get_aoi_geometry
from src.collection import create_seasonal_composite
from src.classification import load_training_polygons

def main():
    ee.Initialize(project=GEE_PROJECT)
    
    aoi_geometry = get_aoi_geometry()
    training_fc = load_training_polygons()
    
    # Add random column for 70/30 split (using seed 42 to match the training script)
    training_fc = training_fc.randomColumn('split_rand', seed=42)
    train_polys = training_fc.filter(ee.Filter.lt('split_rand', 0.7))
    val_polys = training_fc.filter(ee.Filter.gte('split_rand', 0.7))
    
    # We can use a dummy image (like a constant image) at 30m scale to count the pixels
    # inside the polygons because sampleRegions count only depends on the polygon geometry and scale.
    dummy_img = ee.Image.constant(1).rename('constant')
    
    train_samples = dummy_img.sampleRegions(
        collection=train_polys,
        properties=['class'],
        scale=30,
        projection='EPSG:32648',
        tileScale=16
    )
    
    val_samples = dummy_img.sampleRegions(
        collection=val_polys,
        properties=['class'],
        scale=30,
        projection='EPSG:32648',
        tileScale=16
    )
    
    # Count per class in training set
    print("Counting training pixels per class...")
    train_counts = {}
    for c in [1, 2, 3, 4]:
        count = train_samples.filter(ee.Filter.eq('class', c)).size().getInfo()
        train_counts[c] = count
        
    # Count per class in validation set
    print("Counting validation pixels per class...")
    val_counts = {}
    for c in [1, 2, 3, 4]:
        count = val_samples.filter(ee.Filter.eq('class', c)).size().getInfo()
        val_counts[c] = count
        
    print("\n--- PIXEL COUNTS PER CLASS (Scale = 30m) ---")
    print(f"Class 1 (Water):      Train = {train_counts[1]:<5} | Val = {val_counts[1]:<5} | Total = {train_counts[1]+val_counts[1]}")
    print(f"Class 2 (Sand):       Train = {train_counts[2]:<5} | Val = {val_counts[2]:<5} | Total = {train_counts[2]+val_counts[2]}")
    print(f"Class 3 (Built-up):   Train = {train_counts[3]:<5} | Val = {val_counts[3]:<5} | Total = {train_counts[3]+val_counts[3]}")
    print(f"Class 4 (Vegetation): Train = {train_counts[4]:<5} | Val = {val_counts[4]:<5} | Total = {train_counts[4]+val_counts[4]}")
    print(f"Total Pixels:         Train = {sum(train_counts.values()):<5} | Val = {sum(val_counts.values()):<5} | Total = {sum(train_counts.values())+sum(val_counts.values())}")

if __name__ == '__main__':
    main()
