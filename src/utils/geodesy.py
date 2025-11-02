def calculate_distance(point1, point2):
    # This function calculates the distance between two geographic points
    # given as (latitude, longitude) tuples using the Haversine formula.
    import math

    R = 6371  # Radius of the Earth in kilometers

    lat1, lon1 = point1
    lat2, lon2 = point2

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c  # Distance in kilometers
    return distance

# Additional geodesy utility functions can be added here as needed.