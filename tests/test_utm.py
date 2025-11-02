import pytest
from src.utils.utm import lat_lon_to_utm

def test_lat_lon_to_utm():
    # Test case 1: Equator and Prime Meridian
    lat, lon = 0, 0
    expected_utm = (0, 'N', 31)  # Example expected UTM coordinates
    assert lat_lon_to_utm(lat, lon) == expected_utm

    # Test case 2: Latitude 45, Longitude 45
    lat, lon = 45, 45
    expected_utm = (37, 'N', 38)  # Example expected UTM coordinates
    assert lat_lon_to_utm(lat, lon) == expected_utm

    # Test case 3: Latitude -45, Longitude -45
    lat, lon = -45, -45
    expected_utm = (37, 'S', 38)  # Example expected UTM coordinates
    assert lat_lon_to_utm(lat, lon) == expected_utm

    # Test case 4: Edge case at the poles
    lat, lon = 90, 0
    expected_utm = (0, 'N', 0)  # Example expected UTM coordinates
    assert lat_lon_to_utm(lat, lon) == expected_utm

    lat, lon = -90, 0
    expected_utm = (0, 'S', 0)  # Example expected UTM coordinates
    assert lat_lon_to_utm(lat, lon) == expected_utm

    # Add more test cases as needed for coverage