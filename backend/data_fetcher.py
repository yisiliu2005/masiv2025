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


def _safe_int(value):
    """Safely convert a value to int, handling strings and None."""
    if value is None:
        return 0
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0


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
        print(f"  Query: {where_clause}", flush=True)
        
        response = requests.get(
            url,
            params={
                "$limit": 50000,
                "$where": where_clause
            },
            timeout=120  # Increase timeout for slow networks
        )
        
        print(f"  Response status: {response.status_code}", flush=True)
        print(f"  Response size: {len(response.text)} bytes", flush=True)
        
        response.raise_for_status()
        results = response.json()
        print(f"✓ Assessments API returned {len(results) if results else 0} records", flush=True)
        
        if results and len(results) > 0:
            print(f"  Sample record keys: {list(results[0].keys())}", flush=True)
        
        return results if results else []
    except requests.exceptions.Timeout:
        print(f"ERROR: Assessments API request TIMED OUT after 120 seconds", flush=True)
        return []
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP {response.status_code} from assessments API", flush=True)
        print(f"  Response: {response.text[:500]}", flush=True)
        return []
    except ValueError as e:
        print(f"ERROR: Failed to parse JSON from assessments API: {e}", flush=True)
        print(f"  Response text: {response.text[:500]}", flush=True)
        return []
    except Exception as e:
        print(f"ERROR fetching property assessments: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return []


def _get_polygon_centroid_simple(polygon_geojson):
    """
    Calculate centroid of a polygon by averaging all coordinates.
    This avoids Shapely parsing issues.
    
    Args:
        polygon_geojson (dict): GeoJSON Polygon object
    
    Returns:
        tuple: (latitude, longitude) of the centroid, or None if invalid
    """
    try:
        if not isinstance(polygon_geojson, dict):
            return None
        
        coords = polygon_geojson.get("coordinates", [])
        if not coords or len(coords) == 0:
            return None
        
        # For Polygon type, coordinates is [[[lon, lat], [lon, lat], ...], ...]
        # Use the outer ring (coords[0])
        ring = coords[0] if coords else []
        if not ring or len(ring) < 3:
            return None
        
        # Calculate average
        lons = [c[0] for c in ring if len(c) >= 2]
        lats = [c[1] for c in ring if len(c) >= 2]
        
        if not lons or not lats:
            return None
        
        centroid_lon = sum(lons) / len(lons)
        centroid_lat = sum(lats) / len(lats)
        
        return (centroid_lat, centroid_lon)
    except Exception as e:
        print(f"DEBUG: Error calculating simple centroid: {e}", flush=True)
        return None


def _get_multipolygon_centroid_simple(multipolygon_geojson):
    """
    Calculate centroid of a multipolygon by averaging all coordinates.
    This avoids Shapely parsing issues.
    
    Args:
        multipolygon_geojson (dict): GeoJSON MultiPolygon object
    
    Returns:
        tuple: (latitude, longitude) of the centroid, or None if invalid
    """
    try:
        if not isinstance(multipolygon_geojson, dict):
            return None
        
        coords = multipolygon_geojson.get("coordinates", [])
        if not coords or len(coords) == 0:
            return None
        
        # For MultiPolygon, coordinates is [[[[lon, lat], ...], ...], ...]
        # Flatten and average all points
        all_lons = []
        all_lats = []
        
        for polygon in coords:
            if polygon:  # polygon is [[[lon, lat], ...], ...]
                for ring in polygon:
                    if ring:  # ring is [[lon, lat], ...]
                        for point in ring:
                            if len(point) >= 2:
                                all_lons.append(point[0])
                                all_lats.append(point[1])
        
        if not all_lons or not all_lats:
            return None
        
        centroid_lon = sum(all_lons) / len(all_lons)
        centroid_lat = sum(all_lats) / len(all_lats)
        
        return (centroid_lat, centroid_lon)
    except Exception as e:
        print(f"DEBUG: Error calculating multipolygon centroid: {e}", flush=True)
        return None


def buildings_match_by_proximity(footprint_polygon, assessment_multipolygon, threshold_meters=50):
    """
    Match buildings by proximity of their centroids instead of Shapely intersection.
    This avoids Shapely geometry parsing issues seen on Render.
    
    Args:
        footprint_polygon (dict): GeoJSON Polygon from footprint dataset
        assessment_multipolygon (dict): GeoJSON MultiPolygon from assessment dataset
        threshold_meters (float): Maximum distance in meters for a match (default 50m)
    
    Returns:
        bool: True if centroids are within threshold distance
    """
    try:
        fp_centroid = _get_polygon_centroid_simple(footprint_polygon)
        ap_centroid = _get_multipolygon_centroid_simple(assessment_multipolygon)
        
        if not fp_centroid or not ap_centroid:
            return False
        
        # Calculate distance using Haversine formula
        from math import radians, sin, cos, sqrt, atan2
        
        lat1, lon1 = fp_centroid
        lat2, lon2 = ap_centroid
        
        R = 6371000  # Earth radius in meters
        
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance <= threshold_meters
    except Exception as e:
        print(f"ERROR in buildings_match_by_proximity: {type(e).__name__}: {e}", flush=True)
        return False


def buildings_intersect(footprint_polygon, assessment_multipolygon):
    """
    Check if a building footprint polygon intersects with an assessment multipolygon.
    This is used to match buildings across the two datasets.
    
    FALLBACK: Uses proximity-based matching due to Shapely issues on Render.
    
    Args:
        footprint_polygon (dict): GeoJSON Polygon object from footprint dataset
        assessment_multipolygon (dict): GeoJSON MultiPolygon object from property dataset
    
    Returns:
        bool: True if geometries intersect (or are within proximity), False otherwise
    """
    try:
        # Try Shapely first (works on local)
        try:
            fp_shape = shape(footprint_polygon)
            ap_shape = shape(assessment_multipolygon)
            result = fp_shape.intersects(ap_shape)
            return result
        except (TypeError, AttributeError, ValueError) as shapely_error:
            # If Shapely fails, fall back to proximity matching
            print(f"DEBUG: Shapely failed ({type(shapely_error).__name__}), falling back to proximity matching", flush=True)
            return buildings_match_by_proximity(footprint_polygon, assessment_multipolygon)
    except Exception as e:
        print(f"ERROR in buildings_intersect: {type(e).__name__}: {e}", flush=True)
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
    Uses geometry intersection for robust matching.
    
    Args:
        footprints (list): Building footprint data
        assessments (list): Property assessment data
    
    Returns:
        list: Combined building data with all attributes
    """
    combined = []
    matched_count = 0
    failed_count = 0
    first_error_logged = False
    
    for footprint in footprints:
        polygon = footprint.get("polygon")
        struct_id = footprint.get("struct_id")
        if not polygon:
            continue
        
        # Find matching assessment data
        matching_assessment = None
        match_found = False
        
        for assessment in assessments:
            multipolygon = assessment.get("multipolygon")
            if multipolygon:
                try:
                    if buildings_intersect(polygon, multipolygon):
                        matching_assessment = assessment
                        match_found = True
                        matched_count += 1
                        break
                except Exception as e:
                    if not first_error_logged:
                        print(f"DEBUG: First intersection error for {struct_id}: {e}", flush=True)
                        first_error_logged = True
                    continue
        
        if not match_found:
            failed_count += 1
        
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
            "assessed_value": _safe_int(matching_assessment.get("assessed_value", 0) if matching_assessment else 0),
            "year_of_construction": matching_assessment.get("year_of_construction") if matching_assessment else None,
            "footprint": polygon.get("coordinates", []) if polygon else []
        }
        
        combined.append(building)
    
    print(f"DEBUG: Matching results - matched: {matched_count}, failed: {failed_count}", flush=True)
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
