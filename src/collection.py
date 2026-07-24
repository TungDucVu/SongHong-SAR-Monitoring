"""
Collection module for SongHong SAR Monitoring project.
Handles querying Sentinel-1 collections and generating seasonal median composites.
"""

import ee
from src.config import (
    S1_COLLECTION, S1_INSTRUMENT_MODE, S1_ORBIT_PASS
)
from src.preprocessing import (
    remove_border_noise, refined_lee_filter
)
from src.classification import create_feature_stack

def get_seasonal_s1_collection(year, season, aoi_geometry):
    """
    Queries, filters, and returns the raw Sentinel-1 collection for the specified year, season, and AOI.
    Only includes descending pass and IW mode.
    """
    # Initialize base collection
    s1_col = (ee.ImageCollection(S1_COLLECTION)
              .filterBounds(aoi_geometry)
              .filter(ee.Filter.eq('instrumentMode', S1_INSTRUMENT_MODE))
              .filter(ee.Filter.eq('orbitProperties_pass', S1_ORBIT_PASS))
              .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
              .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')))
    
    # Set temporal range for calendar year
    start_date = f'{year}-01-01'
    end_date = f'{year}-12-31'
    s1_year = s1_col.filterDate(start_date, end_date)
    
    # Filter by seasonal calendar months
    if season == 'dry':
        s1_filtered = s1_year.filter(ee.Filter.Or(
            ee.Filter.calendarRange(1, 4, 'month'),
            ee.Filter.calendarRange(11, 12, 'month')
        ))
    elif season == 'wet':
        s1_filtered = s1_year.filter(ee.Filter.calendarRange(5, 10, 'month'))
    else:
        raise ValueError(f"Unknown season: {season}. Expected 'dry' or 'wet'")
        
    return s1_filtered

def create_seasonal_composite(year, season, aoi_geometry, reducer_type='percentile_10', force_on_the_fly=True):
    """
    Creates a speckle-filtered, derived-feature-rich seasonal composite clipped to the AOI.
    Supports multi-temporal 10th percentile reduction (Option A/B) for superior wave and silt suppression.
    """
    asset_path = f"projects/songhong-sar-monitoring/assets/s1_composite_{year}_{season}"
    if not force_on_the_fly and reducer_type == 'median':
        try:
            composite = ee.Image(asset_path)
            bands = composite.bandNames().getInfo()
            print(f"[Collection] Loaded pre-calculated composite asset: {asset_path}")
            size = 15
            try:
                size = composite.get('image_count').getInfo()
            except:
                pass
            s1_dates_sorted = []
            try:
                s1_dates_json = composite.get('s1_dates_json').getInfo()
                import json
                s1_dates_sorted = json.loads(s1_dates_json)
            except:
                pass
                
            print(f"\nSentinel-1 {season.capitalize()}")
            print(f"Images: {len(s1_dates_sorted)}")
            for d in s1_dates_sorted:
                print(f"  {d}")
                
        except Exception as e:
            print(f"[Collection] Asset load bypassed or unavailable ({e}). Generating on-the-fly...")
            force_on_the_fly = True
    else:
        force_on_the_fly = True

    if force_on_the_fly:
        print(f"[Collection] Generating on-the-fly S1 composite with reducer_type='{reducer_type}'...")
        raw_col = get_seasonal_s1_collection(year, season, aoi_geometry)
        size = raw_col.size().getInfo()
        if size == 0:
            print(f"[Warning] No images found for {year} {season} season!")
            return None
            
        import json
        try:
            s1_dates = raw_col.aggregate_array('system:time_start').map(
                lambda t: ee.Date(t).format('YYYY-MM-dd')
            ).getInfo()
            s1_dates_sorted = sorted(list(set(s1_dates)))
        except Exception as err:
            print(f"[Warning] Failed to fetch Sentinel-1 image list: {err}")
            s1_dates_sorted = []
            
        print(f"\nSentinel-1 {season.capitalize()} (Count: {len(s1_dates_sorted)})")
        
        processed_col = raw_col.map(remove_border_noise)
        
        if reducer_type == 'percentile_10':
            print(f"[Collection] Applying 10th Percentile Reducer (P10) for wave/silt suppression...")
            composite_raw = processed_col.select(['VV', 'VH', 'angle']).reduce(ee.Reducer.percentile([10])).rename(['VV', 'VH', 'angle'])
        else:
            composite_raw = processed_col.median()
            
        # Reproject composite_raw to 20m WGS84 grid to flatten GEE reduction tree and guarantee server-side stability
        composite_raw = composite_raw.reproject(crs='EPSG:4326', scale=20)
        composite = refined_lee_filter(composite_raw)

    # Add derived features (Phase 2 Feature stack) on the unclipped composite
    feature_stack = create_feature_stack(composite)
    
    # Clip final feature stack to AOI
    final_composite = feature_stack.clip(aoi_geometry)
    
    # Set properties
    final_composite = final_composite.set({
        'year': year,
        'season': season,
        'image_count': size,
        'system:time_start': ee.Date(f'{year}-01-01').millis()
    })
    
    return final_composite
