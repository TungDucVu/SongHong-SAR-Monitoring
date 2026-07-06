import sys
import os
import ee

sys.path.insert(0, os.getcwd())

from src.config import GEE_PROJECT, ASSET_COMPOSITE_TEMPLATE
from src.aoi import get_aoi_geometry
from src.classification import (
    load_training_polygons, sample_others_from_dynamic_world,
    prepare_training_samples, plot_class_feature_histograms,
    train_and_evaluate, generate_classification_html
)

def run_ml_pipeline_for_season(year, season):
    print(f"\n==========================================")
    print(f"Running Machine Learning Pipeline: {year} {season.upper()}")
    print(f"==========================================")
    
    # 1. Load the seasonal composite from GEE Assets
    composite_asset_path = ASSET_COMPOSITE_TEMPLATE.format(year=year, season=season)
    print(f"[Step 1] Loading GEE composite asset: {composite_asset_path}")
    try:
        composite = ee.Image(composite_asset_path)
        bands = composite.bandNames().getInfo()
        print(f"Composite loaded successfully. Bands: {bands}")
    except Exception as e:
        print(f"[ERROR] Failed to load composite asset {composite_asset_path}: {e}")
        print("Please ensure the production asset task has succeeded and the asset is available in your account.")
        return False
        
    # 2. Get AOI Geometry
    aoi_geometry = get_aoi_geometry()
    
    # 3. Load manual training polygons (Water & Sandbar)
    print(f"[Step 2] Loading manual Water and Sandbar training polygons...")
    water_sandbar_polygons = load_training_polygons()
    poly_count = water_sandbar_polygons.size().getInfo()
    print(f"Loaded {poly_count} training polygons.")
    
    # 4. Programmatically sample 'Others' from GEE Dynamic World
    print(f"[Step 3] Sampling 'Others' class from GEE Dynamic World...")
    others_fc = sample_others_from_dynamic_world(aoi_geometry, water_sandbar_polygons, year)
    
    # 5. Pre-training feature QA histograms
    print(f"[Step 4] Running class feature QA checks (generating histograms)...")
    plot_class_feature_histograms(composite, water_sandbar_polygons, others_fc, year, season)
    
    # 6. Prepare training samples
    print(f"[Step 5] Sampling pixel values from composite...")
    samples = prepare_training_samples(composite, water_sandbar_polygons, others_fc)
    sample_count = samples.size().getInfo()
    print(f"Extracted {sample_count} training pixels from the composite.")
    
    if sample_count == 0:
        print("[ERROR] Extracted 0 training samples. Check training polygons and Dynamic World samples.")
        return False
        
    # 7. Train Random Forest (200 trees) and Evaluate (70/30 split)
    print(f"[Step 6] Training Random Forest model & Evaluating (70/30 split)...")
    classifier, metrics = train_and_evaluate(samples, split_ratio=0.7)
    
    # Print results
    print(f"\n================ METRICS REPORT ================")
    print(f"Training Set Size  : {metrics['training_size']} pixels")
    print(f"Validation Set Size: {metrics['validation_size']} pixels")
    print(f"Overall Accuracy   : {metrics['overall_accuracy'] * 100:.2f}%")
    print(f"Kappa Coefficient  : {metrics['kappa']:.4f}")
    
    print("\nConfusion Matrix:")
    print("      Classified")
    print("      0    1    2  (0: Water, 1: Sandbar, 2: Others)")
    matrix = metrics['confusion_matrix']
    for idx, row in enumerate(matrix):
        print(f"True {idx}: {row}")
        
    # Flatten producer accuracy (usually column vector Nx1)
    prod_acc_raw = metrics['producer_accuracy']
    prod_acc = []
    if isinstance(prod_acc_raw, list):
        if len(prod_acc_raw) == 1 and isinstance(prod_acc_raw[0], list) and len(prod_acc_raw[0]) > 1:
            prod_acc = prod_acc_raw[0]
        else:
            for item in prod_acc_raw:
                if isinstance(item, list):
                    prod_acc.append(item[0])
                else:
                    prod_acc.append(item)
                    
    # Flatten user accuracy (usually row vector 1xN)
    user_acc_raw = metrics['user_accuracy']
    user_acc = []
    if isinstance(user_acc_raw, list):
        if len(user_acc_raw) == 1 and isinstance(user_acc_raw[0], list):
            user_acc = user_acc_raw[0]
        else:
            for item in user_acc_raw:
                if isinstance(item, list):
                    user_acc.append(item[0])
                else:
                    user_acc.append(item)

    print("\nProducer's Accuracy (Recall):")
    for i, val in enumerate(prod_acc):
        print(f"Class {i} ({['Water', 'Sandbar', 'Others'][i]}): {val*100:.2f}%")
        
    print("\nUser's Accuracy (Precision):")
    for i, val in enumerate(user_acc):
        print(f"Class {i} ({['Water', 'Sandbar', 'Others'][i]}): {val*100:.2f}%")
        
    print("\nFeature Importance:")
    print("Feature        | Importance")
    print("---------------------------")
    if 'feature_importance' in metrics:
        # Sort feature importance
        sorted_imp = sorted(metrics['feature_importance'].items(), key=lambda x: x[1], reverse=True)
        for feat, imp in sorted_imp:
            print(f"{feat:<14} | {imp*100:.2f}%")
    else:
        print("Feature importance data is missing.")
    print(f"================================================\n")
    
    # 8. Apply classifier to the composite
    print(f"[Step 7] Classifying the full Red River AOI...")
    classified = composite.classify(classifier)
    
    # 9. Generate Folium Interactive Map
    print(f"[Step 8] Generating Folium interactive HTML map...")
    html_path = generate_classification_html(composite, classified, year, season, aoi_geometry, water_sandbar_polygons, metrics)
    print(f"HTML map generated at: {os.path.abspath(html_path)}")
    return True

if __name__ == "__main__":
    # Initialize ee
    try:
        ee.Initialize(project=GEE_PROJECT)
        print(f"Earth Engine initialized successfully for project: {GEE_PROJECT}")
    except Exception as e:
        print(f"GEE initialization failed: {e}. Running ee.Authenticate()...")
        ee.Authenticate()
        ee.Initialize(project=GEE_PROJECT)
        
    # Run pipeline for 2024 Dry
    run_ml_pipeline_for_season(2024, 'dry')
    
    # Run pipeline for 2024 Wet
    run_ml_pipeline_for_season(2024, 'wet')
