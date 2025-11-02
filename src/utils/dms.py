"""Utility functions for converting between decimal degrees and DMS (degrees, minutes, seconds)."""

def decimal_degrees_to_dms(decimal_degrees):
    """Convert decimal degrees to degrees, minutes, seconds.
    
    Args:
        decimal_degrees (float): Angle in decimal degrees.
    
    Returns:
        tuple: (degrees, minutes, seconds) where seconds has 5 decimal places.
    """
    degrees = int(decimal_degrees)
    minutes_float = (decimal_degrees - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60
    
    # Round to 5 decimal places as requested
    seconds = round(seconds, 5)
    
    return degrees, minutes, seconds


def dms_to_decimal_degrees(degrees, minutes, seconds):
    """Convert degrees, minutes, seconds to decimal degrees.
    
    Args:
        degrees (int): Degrees component (-180 to +180 for longitude, -90 to +90 for latitude)
        minutes (int): Minutes component (0 to 59)
        seconds (float): Seconds component with up to 5 decimal places (0 to 59.99999)
    
    Returns:
        float: Angle in decimal degrees
    """
    sign = -1 if degrees < 0 else 1
    return sign * (abs(degrees) + minutes/60 + seconds/3600)


def format_dms(decimal_degrees, is_latitude=True):
    """Format decimal degrees as a DMS string with hemisphere.
    
    Args:
        decimal_degrees (float): Angle in decimal degrees
        is_latitude (bool): True if formatting latitude, False for longitude
    
    Returns:
        str: Formatted string like "12°34'56.78901"N" for latitude
             or "123°45'56.78901"E" for longitude
    """
    degrees, minutes, seconds = decimal_degrees_to_dms(abs(decimal_degrees))
    
    if is_latitude:
        hemisphere = "N" if decimal_degrees >= 0 else "S"
    else:
        hemisphere = "E" if decimal_degrees >= 0 else "W"
    
    return f"{degrees:d}°{minutes:02d}'{seconds:09.5f}\"{hemisphere}"


def parse_dms(dms_str):
    """Parse a DMS string into decimal degrees.
    
    Accepts formats:
    - "12°34'56.78901"N"
    - "12 34 56.78901N"
    - "12d34m56.78901sN"
    - "-12.5789" (decimal degrees)
    
    Returns:
        float: Decimal degrees
    """
    dms_str = dms_str.strip().upper()
    
    # Try decimal degrees first
    try:
        return float(dms_str.rstrip('NS'))
    except ValueError:
        pass
    
    # Extract hemisphere if present
    hemisphere = 1
    if dms_str[-1] in 'NSEW':
        if dms_str[-1] in 'SW':
            hemisphere = -1
        dms_str = dms_str[:-1]
    
    # Remove markers and split
    for char in '°\'"dms':
        dms_str = dms_str.replace(char, ' ')
    parts = dms_str.split()
    
    if len(parts) != 3:
        raise ValueError("Invalid DMS format. Expected degrees, minutes, and seconds.")
    
    degrees = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    
    if not (0 <= minutes < 60 and 0 <= seconds < 60):
        raise ValueError("Minutes and seconds must be in range [0,60)")
    
    decimal = hemisphere * (abs(degrees) + minutes/60 + seconds/3600)
    return decimal