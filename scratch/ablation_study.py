import ee
import os
from src.config import GEE_PROJECT, CLASSIFIER_FEATURES, OUTPUT_DIR
from src.aoi import get_aoi_geometry
from src.collection import create_seasonal_composite
from src.classification import load_training_polygons, train_classifier

def get_params_for_model(features, base_params):
    params = base_params.copy()
    if params.get('variablesPerSplit') is not None:
        if params['variablesPerSplit'] > len(features):
            params['variablesPerSplit'] = None  # fall back to default
    return params

def main():
    # 1. Initialize Earth Engine
    try:
        ee.Initialize(project=GEE_PROJECT)
        print(f"[GEE] Initialized successfully with project: {GEE_PROJECT}")
    except Exception as e:
        print(f"[GEE Error] Failed to initialize: {e}")
        return

    # 2. Get AOI and training polygons
    aoi_geometry = get_aoi_geometry()
    training_fc = load_training_polygons()
    
    # Define models to test
    models = {
        "Model 1: VV + VH": ['VV', 'VH'],
        "Model 2: VV + VH + Ratio": ['VV', 'VH', 'VV_ratio'],
        "Model 3: VV + VH + Ratio + Textures": [
            'VV', 'VH', 'VV_ratio', 
            'VV_contrast', 'VV_entropy', 'VV_homogeneity', 
            'VV_correlation', 'VV_ASM', 'VV_variance'
        ],
        "Model 4: Full Feature Set": CLASSIFIER_FEATURES
    }
    
    # Base params from previous optimization
    dry_base_params = {
        'numberOfTrees': 300,
        'variablesPerSplit': 8,
        'bagFraction': 0.7
    }
    
    wet_base_params = {
        'numberOfTrees': 100,
        'variablesPerSplit': None,
        'bagFraction': 1.0
    }
    
    results = {}
    
    for season, base_params in [('dry', dry_base_params), ('wet', wet_base_params)]:
        print(f"\n==========================================")
        print(f"   RUNNING ABLATION STUDY FOR {season.upper()} SEASON")
        print(f"==========================================")
        
        composite = create_seasonal_composite(2024, season, aoi_geometry)
        results[season] = []
        
        for model_name, features in models.items():
            print(f"\nEvaluating {model_name}...")
            print(f"Features: {features}")
            
            # Adjust params if variablesPerSplit is greater than number of features
            params = get_params_for_model(features, base_params)
            
            # Train and evaluate using the 5-seed average
            _, metrics = train_classifier(training_fc, composite, features, best_params=params)
            
            results[season].append({
                'model': model_name,
                'num_features': len(features),
                'oa': metrics['overall_accuracy'],
                'kappa': metrics['kappa'],
                'macro_f1': metrics['macro_f1'],
                'water_f1': metrics['class_metrics'][1]['f1_score'],
                'sand_f1': metrics['class_metrics'][2]['f1_score'],
                'built_f1': metrics['class_metrics'][3]['f1_score'],
                'veg_f1': metrics['class_metrics'][4]['f1_score'],
            })
            
    # 3. Format results into markdown
    md_content = "# Random Forest Ablation Study Results (2024 Seasons)\n\n"
    md_content += "This report compares the performance of 4 model configurations (varying feature sets) "
    md_content += "trained on the same training set using class-level global sampling limits (Water=1000, others=1800).\n\n"
    
    for season in ['dry', 'wet']:
        md_content += f"## {season.upper()} Season\n\n"
        md_content += "| Model Config | Num Features | OA (%) | Kappa | Macro F1 | Water F1 | Sand F1 | Built-up F1 | Vegetation F1 |\n"
        md_content += "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
        
        for res in results[season]:
            md_content += f"| {res['model']} " \
                          f"| {res['num_features']} " \
                          f"| {res['oa']*100:.2f}% " \
                          f"| {res['kappa']:.4f} " \
                          f"| {res['macro_f1']:.4f} " \
                          f"| {res['water_f1']:.4f} " \
                          f"| {res['sand_f1']:.4f} " \
                          f"| {res['built_f1']:.4f} " \
                          f"| {res['veg_f1']:.4f} |\n"
        md_content += "\n"
        
    # Save the report to outputs/ablation_study_results.md
    out_path = os.path.join(OUTPUT_DIR, 'ablation_study_results.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    print("\n==========================================")
    print("        ABLATION STUDY COMPLETED!         ")
    print("==========================================")
    print(f"Results report saved to: {out_path}\n")
    print(md_content)

if __name__ == '__main__':
    main()
