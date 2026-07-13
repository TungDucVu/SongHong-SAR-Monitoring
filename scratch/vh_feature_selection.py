import ee
import os
from src.config import GEE_PROJECT, OUTPUT_DIR
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
    
    # 11 base features (Full Feature Set from baseline)
    base_features = [
        'VV', 'VH', 'VV_ratio', 'VV_sum', 'VV_mean',
        'VV_contrast', 'VV_entropy', 'VV_homogeneity',
        'VV_correlation', 'VV_ASM', 'VV_variance'
    ]
    
    # Define combinations to test
    combinations = {
        "Combo 1: Base + VH_contrast": base_features + ['VH_contrast'],
        "Combo 2: Base + VH_contrast + VH_homogeneity": base_features + ['VH_contrast', 'VH_homogeneity'],
        "Combo 3: Base + VH_contrast + VH_variance": base_features + ['VH_contrast', 'VH_variance']
    }
    
    # Current hyperparameter status
    dry_base_params = {
        'numberOfTrees': 300,
        'variablesPerSplit': 3,
        'bagFraction': 0.5
    }
    
    wet_base_params = {
        'numberOfTrees': 100,
        'variablesPerSplit': None,
        'bagFraction': 1.0
    }
    
    results = {}
    
    for season, base_params in [('dry', dry_base_params), ('wet', wet_base_params)]:
        print(f"\n==========================================")
        print(f"   RUNNING FEATURE SELECTION FOR {season.upper()} SEASON")
        print(f"==========================================")
        
        composite = create_seasonal_composite(2024, season, aoi_geometry)
        results[season] = []
        
        for name, features in combinations.items():
            print(f"\nEvaluating {name}...")
            print(f"Features ({len(features)}): {features}")
            
            params = get_params_for_model(features, base_params)
            
            # Train and evaluate using the 5-seed average
            _, metrics = train_classifier(training_fc, composite, features, best_params=params)
            
            # Print confusion matrix immediately to stdout
            print(f"Overall Accuracy: {metrics['overall_accuracy']*100:.2f}%, Kappa: {metrics['kappa']:.4f}, Macro F1: {metrics['macro_f1']:.4f}")
            
            results[season].append({
                'name': name,
                'num_features': len(features),
                'oa': metrics['overall_accuracy'],
                'kappa': metrics['kappa'],
                'macro_f1': metrics['macro_f1'],
                'water_f1': metrics['class_metrics'][1]['f1_score'],
                'sand_f1': metrics['class_metrics'][2]['f1_score'],
                'built_f1': metrics['class_metrics'][3]['f1_score'],
                'veg_f1': metrics['class_metrics'][4]['f1_score'],
                'confusion': metrics['confusion_matrix']
            })
            
    # 3. Format results into markdown
    md_content = "# VH Textures Feature Selection Results (2024 Seasons)\n\n"
    md_content += "This report compares three feature selection combinations on top of the 11 base features (VV textures + ratios).\n\n"
    
    for season in ['dry', 'wet']:
        md_content += f"## {season.upper()} Season\n\n"
        md_content += "| Combination Config | Num Features | OA (%) | Kappa | Macro F1 | Water F1 | Sand F1 | Built-up F1 | Vegetation F1 |\n"
        md_content += "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
        
        for res in results[season]:
            md_content += f"| {res['name']} " \
                          f"| {res['num_features']} " \
                          f"| {res['oa']*100:.2f}% " \
                          f"| {res['kappa']:.4f} " \
                          f"| {res['macro_f1']:.4f} " \
                          f"| {res['water_f1']:.4f} " \
                          f"| {res['sand_f1']:.4f} " \
                          f"| {res['built_f1']:.4f} " \
                          f"| {res['veg_f1']:.4f} |\n"
        md_content += "\n"
        
    out_path = os.path.join(OUTPUT_DIR, 'vh_feature_selection_results.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    print("\n==========================================")
    print("      FEATURE SELECTION COMPLETED!        ")
    print("==========================================")
    print(f"Results report saved to: {out_path}\n")
    print(md_content)

if __name__ == '__main__':
    main()
