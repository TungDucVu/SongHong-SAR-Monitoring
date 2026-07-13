import json
import os

def main():
    base_geojson_path = 'aoi/training_polygons.geojson'
    manual_geojson_path = 'aoi/manual_training_polygons.geojson'
    
    # 1. Load original training polygons
    if os.path.exists(base_geojson_path):
        with open(base_geojson_path, 'r', encoding='utf-8') as f:
            base_data = json.load(f)
    else:
        print(f"Error: {base_geojson_path} not found.")
        return

    # 2. Load manual training polygons
    if os.path.exists(manual_geojson_path):
        with open(manual_geojson_path, 'r', encoding='utf-8') as f:
            manual_data = json.load(f)
    else:
        print(f"Error: {manual_geojson_path} not found.")
        return

    features = base_data['features']
    manual_features = manual_data['features']
    
    print(f"Original polygon count: {len(features)}")
    
    # 3. Filter out water ID "1_0_5" and rename class 4 "className" to "Vegetation"
    filtered_features = []
    removed_count = 0
    for f in features:
        feat_id = f['properties'].get('id')
        if feat_id == '1_0_5':
            removed_count += 1
            print("Successfully found and removed polygon 1_0_5.")
            continue
        
        # Rename class 4 classname
        if f['properties'].get('class') == 4:
            f['properties']['className'] = 'Vegetation'
            
        filtered_features.append(f)
        
    print(f"Removed {removed_count} polygon(s) matching ID '1_0_5'.")
    
    # 4. Add manual polygons (and rename class 4 className to "Vegetation")
    added_count = 0
    for f in manual_features:
        if f['properties'].get('class') == 4:
            f['properties']['className'] = 'Vegetation'
        filtered_features.append(f)
        added_count += 1
        
    print(f"Added {added_count} manual polygon(s).")
    
    # Update feature list
    base_data['features'] = filtered_features
    print(f"Total polygons in final dataset: {len(filtered_features)}")
    
    # 5. Save back to training_polygons.geojson
    with open(base_geojson_path, 'w', encoding='utf-8') as f:
        json.dump(base_data, f, indent=2)
    print("Merged and saved training polygons successfully.")

if __name__ == '__main__':
    main()
