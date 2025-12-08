"""
Data fetcher module for Calgary building data.
Fetches and combines data from two SODA endpoints:
1. Building footprints and heights (cchr-krqg.json)
2. Property assessment data (4bsw-nn7w.json)
"""

import requests
from sodapy import Socrata
from shapely.geometry import shape, MultiPolygon, Polygon
import os

# Bounding box for the 4-block area (axis-aligned rectangle)
# Adjusted from hand-picked coordinates to clean rectangle
MIN_LAT = 51.03893877415592   # southernmost point
MAX_LAT = 51.03999458794443   # northernmost point
MIN_LON = -114.07927447774654 # westernmost point
MAX_LON = -114.07429304853973 # easternmost point


def fetch_building_footprints():
    """
    Fetch building footprints and heights from Calgary Open Data.
    Endpoint: https://data.calgary.ca/resource/cchr-krqg.json
    
    Returns:
        list: Building data with footprints and heights
    """
    url = "https://data.calgary.ca/resource/cchr-krqg.json"
    
    # Use SODA API with within_box filter for the bounding box
    # Note: within_box uses (lat, lon) ordering
    try:
        print(f"Fetching from {url}...", flush=True)
        response = requests.get(
            url,
            params={
                "$limit": 50000,  # Fetch up to 50k records
                "$where": f"""
                    within_box(polygon, {MIN_LAT}, {MIN_LON}, {MAX_LAT}, {MAX_LON})
                """
            },
            timeout=120  # Increase timeout for slow networks
        )
        response.raise_for_status()
        data = response.json()
        print(f"✓ Footprints API returned {len(data) if data else 0} records", flush=True)
        return data if data else []
    except requests.exceptions.Timeout:
        print(f"ERROR: Footprints API request TIMED OUT after 120 seconds", flush=True)
        return []
    except Exception as e:
        print(f"ERROR fetching building footprints: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return []


def fetch_property_assessments():
    """
    Fetch property assessment data from Calgary Open Data.
    Endpoint: https://data.calgary.ca/resource/4bsw-nn7w.json
    
    Returns:
        list: Property assessment data with zoning and values
    """
    try:
        # Use requests directly for more reliable API access
        # This bypasses the Socrata client which may have network issues on Render
        url = "https://data.calgary.ca/resource/4bsw-nn7w.json"
        
        where_clause = f"within_box(multipolygon, {MIN_LAT}, {MIN_LON}, {MAX_LAT}, {MAX_LON})"
        
        print(f"Fetching from {url}...", flush=True)
        response = requests.get(
            url,
            params={
                "$limit": 50000,
                "$where": where_clause
            },
            timeout=120  # Increase timeout for slow networks
        )
        response.raise_for_status()
        results = response.json()
        print(f"✓ Assessments API returned {len(results) if results else 0} records", flush=True)
        return results if results else []
    except requests.exceptions.Timeout:
        print(f"ERROR: Assessments API request TIMED OUT after 120 seconds", flush=True)
        return []
    except Exception as e:
        print(f"ERROR fetching property assessments: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return []


def buildings_intersect(footprint_polygon, assessment_multipolygon):
    """
    Check if a building footprint polygon intersects with an assessment multipolygon.
    This is used to match buildings across the two datasets.
    
    Args:
        footprint_polygon (dict): GeoJSON Polygon object from footprint dataset
        assessment_multipolygon (dict): GeoJSON MultiPolygon object from property dataset
    
    Returns:
        bool: True if geometries intersect, False otherwise
    """
    try:
        fp_shape = shape(footprint_polygon)
        ap_shape = shape(assessment_multipolygon)
        return fp_shape.intersects(ap_shape)
    except Exception:
        return False


def get_polygon_centroid(polygon_geojson):
    """
    Get the centroid (center) of a polygon in (lat, lon) format.
    
    Args:
        polygon_geojson (dict): GeoJSON Polygon object
    
    Returns:
        tuple: (latitude, longitude) of the centroid
    """
    try:
        poly = shape(polygon_geojson)
        centroid = poly.centroid
        # GeoJSON uses (lon, lat), convert to (lat, lon)
        return (centroid.y, centroid.x)
    except Exception:
        return None


def combine_building_data(footprints, assessments):
    """
    Combine footprint data with property assessment data by matching geometries.
    
    Args:
        footprints (list): Building footprint data
        assessments (list): Property assessment data
    
    Returns:
        list: Combined building data with all attributes
    """
    combined = []
    
    for footprint in footprints:
        polygon = footprint.get("polygon")
        if not polygon:
            continue
        
        # Find matching assessment data
        matching_assessment = None
        for assessment in assessments:
            multipolygon = assessment.get("multipolygon")
            if multipolygon and buildings_intersect(polygon, multipolygon):
                matching_assessment = assessment
                break
        
        # Calculate building height
        height = None
        try:
            rooftop_z = float(footprint.get("rooftop_elev_z", 0))
            ground_z = float(footprint.get("grd_elev_min_z", 0))
            height = rooftop_z - ground_z
        except (ValueError, TypeError):
            height = 0
        
        # Get centroid for lat/lon
        lat_lon = get_polygon_centroid(polygon)
        if not lat_lon:
            continue
        
        # Build combined record
        building = {
            "id": str(footprint.get("struct_id", "")),
            "struct_id": footprint.get("struct_id"),
            "address": matching_assessment.get("address", "") if matching_assessment else "",
            "latitude": lat_lon[0],
            "longitude": lat_lon[1],
            "height": height,
            "land_use_designation": matching_assessment.get("land_use_designation", "") if matching_assessment else "",
            "assessed_value": matching_assessment.get("assessed_value", 0) if matching_assessment else 0,
            "year_of_construction": matching_assessment.get("year_of_construction") if matching_assessment else None,
            "footprint": polygon.get("coordinates", []) if polygon else []
        }
        
        combined.append(building)
    
    return combined


def get_all_buildings():
    """
    Main function to fetch and combine all building data.
    
    Returns:
        list: Combined building data for the target area
    """
    print("=" * 60, flush=True)
    print("STARTING: Fetching all building data", flush=True)
    print("=" * 60, flush=True)
    
    print("Fetching building footprints...", flush=True)
    footprints = fetch_building_footprints()
    print(f"✓ Found {len(footprints)} building footprints", flush=True)
    
    print("Fetching property assessments...", flush=True)
    assessments = fetch_property_assessments()
    print(f"✓ Found {len(assessments)} property assessments", flush=True)
    
    print("Combining data...", flush=True)
    buildings = combine_building_data(footprints, assessments)
    print(f"✓ Combined {len(buildings)} buildings with all attributes", flush=True)
    
    # Count how many have matching assessment data
    with_address = sum(1 for b in buildings if b["address"])
    with_value = sum(1 for b in buildings if b["assessed_value"] > 0)
    print(f"  - Buildings with address: {with_address}", flush=True)
    print(f"  - Buildings with assessed value: {with_value}", flush=True)
    
    print("=" * 60, flush=True)
    return buildings
