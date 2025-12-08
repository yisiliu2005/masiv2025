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
        response = requests.get(
            url,
            params={
                "$limit": 50000,  # Fetch up to 50k records
                "$where": f"""
                    within_box(polygon, {MIN_LAT}, {MIN_LON}, {MAX_LAT}, {MAX_LON})
                """
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching building footprints: {e}")
        return []


def fetch_property_assessments():
    """
    Fetch property assessment data from Calgary Open Data.
    Endpoint: https://data.calgary.ca/resource/4bsw-nn7w.json
    
    Returns:
        list: Property assessment data with zoning and values
    """
    try:
        client = Socrata("data.calgary.ca", None)
        
        # Query property data within the bounding box
        results = client.get(
            "4bsw-nn7w",
            where=f"""
                within_box(multipolygon, {MIN_LAT}, {MIN_LON}, {MAX_LAT}, {MAX_LON})
            """,
            limit=50000
        )
        return results
    except Exception as e:
        print(f"Error fetching property assessments: {e}")
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
    print("Fetching building footprints...")
    footprints = fetch_building_footprints()
    print(f"Found {len(footprints)} building footprints")
    
    print("Fetching property assessments...")
    assessments = fetch_property_assessments()
    print(f"Found {len(assessments)} property assessments")
    
    print("Combining data...")
    buildings = combine_building_data(footprints, assessments)
    print(f"Combined {len(buildings)} buildings with all attributes")
    
    return buildings
