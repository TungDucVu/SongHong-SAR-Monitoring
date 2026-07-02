"""
Collection module for SongHong SAR Monitoring project.
Handles querying Sentinel-1 collections and generating seasonal median composites.
"""

import ee
from src.config import (
    S1_COLLECTION, S1_INSTRUMENT_MODE, S1_ORBIT_PASS
)
from src.preprocessing import (
    remove_border_noise, refined_lee_filter, add_derived_features
)

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

def create_seasonal_composite(year, season, aoi_geometry):
    """
    Creates a speckle-filtered, derived-feature-rich seasonal median composite clipped to the AOI.
    """
    raw_col = get_seasonal_s1_collection(year, season, aoi_geometry)
    
    # Check size of collection
    size = raw_col.size().getInfo()
    if size == 0:
        print(f"[Warning] No images found for {year} {season} season!")
        return None
        
    # Apply border noise removal and Refined Lee filter to each image
    processed_col = raw_col.map(remove_border_noise).map(lambda img: refined_lee_filter(img))
    
    # Calculate median composite
    composite = processed_col.median()
    
    # Clip composite to AOI
    composite_clipped = composite.clip(aoi_geometry)
    
    # Add derived features (ratio and difference)
    final_composite = add_derived_features(composite_clipped)
    
    # Set properties
    final_composite = final_composite.set({
        'year': year,
        'season': season,
        'image_count': size,
        'system:time_start': ee.Date(f'{year}-01-01').millis()
    })
    
    return final_composite
