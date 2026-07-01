"""
Data collection and aggregation module for SongHong SAR Monitoring.
Queries Sentinel-1 GRD, maps preprocessing, calculates yearly/monthly coverage, and generates composites.
"""

import ee
from src.config import (
    S1_COLLECTION, S1_INSTRUMENT_MODE, S1_ORBIT_PASS, 
    S1_POLARISATIONS, S1_BANDS
)
from src.preprocessing import preprocess_image

def get_s1_collection(aoi_geometry, start_date, end_date):
    """
    Queries and filters raw Sentinel-1 GRD collection.
    
    Args:
        aoi_geometry: ee.Geometry to filter bounds.
        start_date: str (YYYY-MM-DD).
        end_date: str (YYYY-MM-DD).
        
    Returns:
        ee.ImageCollection containing filtered raw Sentinel-1 images.
    """
    collection = (ee.ImageCollection(S1_COLLECTION)
                  .filterBounds(aoi_geometry)
                  .filterDate(start_date, end_date)
                  .filter(ee.Filter.eq('instrumentMode', S1_INSTRUMENT_MODE))
                  .filter(ee.Filter.eq('orbitProperties_pass', S1_ORBIT_PASS))
                  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', S1_POLARISATIONS[0]))
                  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', S1_POLARISATIONS[1]))
                  .select(S1_BANDS))
    return collection

def get_processed_collection(aoi_geometry, start_date, end_date):
    """
    Queries, filters, and pre-processes Sentinel-1 GRD collection.
    
    Args:
        aoi_geometry: ee.Geometry to filter bounds.
        start_date: str (YYYY-MM-DD).
        end_date: str (YYYY-MM-DD).
        
    Returns:
        ee.ImageCollection of pre-processed images with VV, VH, and VV_VH_ratio bands.
    """
    raw_col = get_s1_collection(aoi_geometry, start_date, end_date)
    # Map preprocess_image with explicit casting
    processed_col = raw_col.map(lambda img: preprocess_image(img, aoi_geometry))
    return processed_col

def get_monthly_composite(processed_collection, year, month, aoi_geometry):
    """
    Generates monthly median composite for a specific year and month.
    
    Args:
        processed_collection: ee.ImageCollection preprocessed.
        year: int.
        month: int.
        aoi_geometry: ee.Geometry.
        
    Returns:
        ee.Image median composite.
    """
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')
    
    composite = (processed_collection
                 .filterDate(start_date, end_date)
                 .median()
                 .clip(aoi_geometry))
    
    # Format system:index as YYYY_MM
    year_str = ee.Number(year).format('%04d')
    month_str = ee.Number(month).format('%02d')
    img_id = year_str.cat('_').cat(month_str)
    
    return ee.Image(composite.set({
        'year': year,
        'month': month,
        'system:time_start': start_date.millis(),
        'system:index': img_id
    }))

def get_annual_composite(processed_collection, year, aoi_geometry):
    """
    Generates annual median composite for a specific year.
    
    Args:
        processed_collection: ee.ImageCollection preprocessed.
        year: int.
        aoi_geometry: ee.Geometry.
        
    Returns:
        ee.Image annual median composite.
    """
    start_date = ee.Date.fromYMD(year, 1, 1)
    end_date = start_date.advance(1, 'year')
    
    composite = (processed_collection
                 .filterDate(start_date, end_date)
                 .median()
                 .clip(aoi_geometry))
    
    year_str = ee.Number(year).format('%04d')
    
    return ee.Image(composite.set({
        'year': year,
        'system:time_start': start_date.millis(),
        'system:index': year_str
    }))

def get_coverage_statistics(s1_collection, start_year=2015, end_year=2024):
    """
    Computes count of S1 images per year and month.
    
    Args:
        s1_collection: ee.ImageCollection raw or processed.
        start_year: int.
        end_year: int.
        
    Returns:
        tuple (year_stats, month_stats_recent):
          - year_stats: list of dicts {'year': y, 'count': c, 'status': s}
          - month_stats: list of dicts {'month': m, 'month_name': n, 'count': c} for years 2020-2024
    """
    # 1. Stats by year
    year_stats = []
    for y in range(start_year, end_year + 1):
        count = s1_collection.filter(ee.Filter.calendarRange(y, y, 'year')).size().getInfo()
        status = "✅ OK" if count >= 20 else "⚠️ Warning (low count)" if count > 0 else "❌ No data"
        year_stats.append({
            'year': y,
            'count': count,
            'status': status
        })
        
    # 2. Stats by month (2020-2024 recent period)
    month_stats = []
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    recent_col = s1_collection.filterDate(f'{start_year+5}-01-01', f'{end_year}-12-31')
    
    for m in range(1, 13):
        count = recent_col.filter(ee.Filter.calendarRange(m, m, 'month')).size().getInfo()
        month_stats.append({
            'month': m,
            'month_name': month_names[m - 1],
            'count': count
        })
        
    return year_stats, month_stats
