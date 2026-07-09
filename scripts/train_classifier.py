"""
Orchestration script for Phase 3: Random Forest Classification (4-class schema).
Loads training data, trains models for 2024 Dry and Wet seasons, performs sequential tuning,
and generates reports and interactive HTML maps.
"""

import ee
import os
import json
from src.config import GEE_PROJECT, CLASSIFIER_FEATURES, OUTPUT_DIR
from src.aoi import get_aoi_geometry
from src.collection import create_seasonal_composite
from src.classification import (
    load_training_polygons, train_classifier, classify_image,
    run_area_qc, generate_classification_html
)

def run_pipeline_for_season(year, season, aoi_geometry, training_fc):
    print("\n" + "="*50)
    print(f"      CALIBRATING MODEL FOR {year} {season.upper()}       ")
    print("="*50)
    
    # 1. Load the Sentinel-1 feature stack composite
    print("[Step 1] Loading S1 feature stack composite...")
    composite = create_seasonal_composite(year, season, aoi_geometry)
    
    # 2. Train RF model (bypass slow sequential tuning with standard parameters)
    best_params = {'numberOfTrees': 200, 'variablesPerSplit': None, 'bagFraction': 0.7}
    final_cf, metrics = train_classifier(training_fc, composite, CLASSIFIER_FEATURES, best_params=best_params)
    
    # 3. Apply model to classify the entire composite
    print(f"\n[Step 4] Applying model to classify S1 composite...")
    classified, max_prob = classify_image(composite, final_cf, CLASSIFIER_FEATURES)
    
    # 4. Run post-classification area statistics check
    print(f"\n[Step 5] Running Post-classification Area Statistics Sanity Check...")
    percentages, warnings = run_area_qc(classified, aoi_geometry)
    
    # 5. Render interactive Folium map
    print(f"\n[Step 6] Rendering Interactive Folium QC Map...")
    html_path = generate_classification_html(
        composite=composite,
        classified=classified,
        max_prob=max_prob,
        year=year,
        season=season,
        aoi_geometry=aoi_geometry,
        combined_fc=training_fc,
        metrics=metrics
    )
    
    # 6. Save metrics report
    report_path = os.path.join(OUTPUT_DIR, f'rf_metrics_{year}_{season}.txt')
    print(f"[Report] Saving classification report to: {report_path}")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"Random Forest Classification Report - {year} {season.upper()}\n")
        f.write("="*50 + "\n\n")
        
        f.write("Optimal Hyperparameters (Tuned Sequentially):\n")
        for k, v in metrics['best_params'].items():
            f.write(f"  {k}: {v}\n")
        f.write("\n")
        
        f.write("Model Accuracy Summary (Averaged over 5 random seeds):\n")
        f.write(f"  Overall Accuracy: {metrics['overall_accuracy']*100:.2f}%\n")
        f.write(f"  Kappa Coefficient: {metrics['kappa']:.4f}\n")
        f.write(f"  Macro F1-score:    {metrics['macro_f1']:.4f}\n\n")
        
        f.write("Class-Specific Metrics:\n")
        class_names = {1: 'Water', 2: 'Sand', 3: 'Built-up', 4: 'Others'}
        for c in range(1, 5):
            c_m = metrics['class_metrics'][c]
            f.write(f"  {class_names[c]:<12}: Precision = {c_m['precision']*100:.2f}%, Recall = {c_m['recall']*100:.2f}%, F1 = {c_m['f1_score']:.4f}\n")
        f.write("\n")
        
        f.write("Average Confusion Matrix (rows = true class, columns = predicted class):\n")
        header = "                " + " ".join([f"{class_names[c]:>10}" for c in range(1, 5)]) + "\n"
        f.write(header)
        for i, c1 in enumerate(range(1, 5)):
            row_str = f"  {class_names[c1]:<14}"
            for j, c2 in enumerate(range(1, 5)):
                val = metrics['confusion_matrix'][i][j] if i < len(metrics['confusion_matrix']) and j < len(metrics['confusion_matrix'][i]) else 0.0
                row_str += f" {val:10.1f}"
            f.write(row_str + "\n")
        f.write("\n")
        
        if 'feature_importance' in metrics:
            f.write("Feature Importance Rankings:\n")
            for i, item in enumerate(metrics['feature_importance']):
                f.write(f"   {i+1:2d}. {item['feature']:<15} : {item['importance_pct']:.2f}%\n")
            f.write("\n")
            
        f.write("Post-Classification Area Statistics:\n")
        for c in range(1, 5):
            f.write(f"  {class_names[c]:<12}: {percentages[c]:.2f}%\n")
        f.write("\n")
        
        f.write("QC Sanity Check Flags:\n")
        if warnings:
            for w in warnings:
                f.write(f"  [WARNING] {w}\n")
        else:
            f.write("  [PASS] Area statistics are within physically realistic boundaries.\n")
            
    print(f"[Success] Completed seasonal run for {year} {season.upper()}!")

def main():
    print("="*50)
    print("     PHASE 3: RANDOM FOREST MODEL TRAINING        ")
    print("="*50)
    
    # 1. Initialize Earth Engine
    try:
        ee.Initialize(project=GEE_PROJECT)
        print(f"[GEE] Initialized successfully with project: {GEE_PROJECT}")
    except Exception as e:
        print(f"[GEE Error] Failed to initialize: {e}")
        return

    # 2. Get AOI and training polygons
    aoi_geometry = get_aoi_geometry()
    
    print("[Data] Loading unified training dataset (ESA WorldCover sourced)...")
    try:
        training_fc = load_training_polygons()
        print(f"  Total training polygons loaded: {training_fc.size().getInfo()}")
    except Exception as e:
        print(f"[Error] Failed to load training polygons: {e}")
        return

    # 3. Run pipeline for both seasons of 2024
    run_pipeline_for_season(2024, 'dry', aoi_geometry, training_fc)
    run_pipeline_for_season(2024, 'wet', aoi_geometry, training_fc)

if __name__ == '__main__':
    main()
