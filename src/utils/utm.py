def lat_lon_to_utm(lat, lon):
    import math

    # Constants for UTM conversion
    a = 6378137  # WGS84 major axis
    k0 = 0.9996  # scale factor
    e = 0.081819190842622  # eccentricity
    e_prime_sq = e**2 / (1 - e**2)

    # Calculate the zone
    zone_number = int((lon + 180) / 6) + 1

    # Calculate the central meridian of the zone
    cm = (zone_number - 1) * 6 - 180 + 3

    # Convert latitude and longitude to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    # Calculate the UTM coordinates
    n = a / math.sqrt(1 - e**2 * math.sin(lat_rad)**2)
    t = math.tan(lat_rad)**2
    c = e_prime_sq * math.cos(lat_rad)**2
    a_ = math.cos(lat_rad) * (lon_rad - math.radians(cm))

    m = a * (
        (1 - e**2 / 4 - 3 * e**4 / 64 - 5 * e**6 / 256) * lat_rad
        - (3 * e**2 / 8 + 3 * e**4 / 32 + 45 * e**6 / 1024) * math.sin(2 * lat_rad)
        + (15 * e**4 / 256 + 45 * e**6 / 1024) * math.sin(4 * lat_rad)
        - (35 * e**6 / 3072) * math.sin(6 * lat_rad)
    )

    utm_easting = (k0 * n * (a_ + (1 - t + c) * a_**3 / 6 + (5 - 18 * t + t**2 + 72 * c - 58 * e_prime_sq) * a_**5 / 120) + 500000)
    utm_northing = (k0 * (m + n * math.tan(lat_rad) * (a_**2 / 2 + (5 - t + 9 * c + 4 * c**2) * a_**4 / 24 + (61 - 58 * t + t**2 + 600 * c - 330 * e_prime_sq) * a_**6 / 720)))

    if lat < 0:
        utm_northing += 10000000  # 10000000 meter offset for southern hemisphere

    # Determine hemisphere
    hemisphere = "N" if lat >= 0 else "S"

    # Return easting, northing, zone number and hemisphere
    return utm_easting, utm_northing, int(zone_number), hemisphere


def dataframe_latlon_to_utm(df, lat_col="latitude", lon_col="longitude"):
    """Convert a pandas DataFrame with latitude/longitude columns to UTM.

    Args:
        df (pandas.DataFrame): Input dataframe containing latitude and longitude columns.
        lat_col (str): Name of the latitude column in df. Defaults to 'latitude'.
        lon_col (str): Name of the longitude column in df. Defaults to 'longitude'.

    Returns:
        pandas.DataFrame: A copy of df with added columns: 'easting', 'northing', 'zone', 'hemisphere'.
    """
    try:
        import pandas as pd
    except Exception:
        raise

    if lat_col not in df.columns or lon_col not in df.columns:
        raise ValueError(f"DataFrame must contain columns '{lat_col}' and '{lon_col}'")

    def _row_to_utm(row):
        return lat_lon_to_utm(row[lat_col], row[lon_col])

    # Apply conversion per row and expand results
    results = df.apply(_row_to_utm, axis=1)
    results_df = pd.DataFrame(results.tolist(), index=df.index, columns=["easting", "northing", "zone", "hemisphere"])

    out = df.copy()
    out = pd.concat([out, results_df], axis=1)
    return out


def read_shapefile_zip_to_gdf(zip_bytes):
    """Read a zipped shapefile (bytes) into a GeoDataFrame.

    Args:
        zip_bytes (bytes or file-like): Bytes of a ZIP file containing .shp/.shx/.dbf/.prj

    Returns:
        geopandas.GeoDataFrame
    """
    try:
        import geopandas as gpd
        import zipfile
        import tempfile
        import os
    except Exception:
        raise RuntimeError("geopandas and zipfile are required to read shapefile uploads. Please install geopandas and its dependencies.")

    with tempfile.TemporaryDirectory() as tmpdir:
        zpath = os.path.join(tmpdir, "upload.zip")
        with open(zpath, "wb") as f:
            # zip_bytes may be a BytesIO or raw bytes
            if hasattr(zip_bytes, "read"):
                f.write(zip_bytes.read())
            else:
                f.write(zip_bytes)

        with zipfile.ZipFile(zpath, "r") as z:
            z.extractall(tmpdir)

        # Find the .shp file in the extracted contents
        shp_files = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.lower().endswith('.shp')]
        if not shp_files:
            raise RuntimeError("No .shp file found in uploaded ZIP")

        shp_path = shp_files[0]
        gdf = gpd.read_file(shp_path)
        return gdf


def transform_gdf_to_utm(gdf, zone=None):
    """Transform a GeoDataFrame to a UTM CRS.

    If zone is None, the function will compute an appropriate UTM zone from the centroid longitude.

    Returns:
        tuple: (gdf_utm, zone, hemisphere)
    """
    try:
        import geopandas as gpd
        from pyproj import CRS
    except Exception:
        raise RuntimeError("pyproj and geopandas are required for vector CRS transformations.")

    # Ensure gdf is geographic (WGS84). If not, try to convert.
    if gdf.crs is None:
        # Assume input is WGS84
        gdf = gdf.set_crs(epsg=4326)
    else:
        try:
            gdf = gdf.to_crs(epsg=4326)
        except Exception:
            # If conversion fails, assume it is already geographic
            pass

    # Determine zone if not provided
    if zone is None:
        # Use centroid of total bounds for robust approximation
        minx, miny, maxx, maxy = gdf.total_bounds
        center_lon = (minx + maxx) / 2.0
        zone = int((center_lon + 180) / 6) + 1

    # Hemisphere: determine based on centroid latitude
    minx, miny, maxx, maxy = gdf.total_bounds
    center_lat = (miny + maxy) / 2.0
    hemisphere = "N" if center_lat >= 0 else "S"

    # Build CRS for UTM
    south = hemisphere.upper() == "S"
    proj_string = f"+proj=utm +zone={int(zone)} +datum=WGS84 +units=m +no_defs"
    if south:
        proj_string += " +south"

    crs_utm = CRS.from_proj4(proj_string)
    gdf_utm = gdf.to_crs(crs_utm)
    return gdf_utm, int(zone), hemisphere


def gdf_to_shapefile_zip_bytes(gdf):
    """Write a GeoDataFrame to a zipped shapefile and return bytes.

    Returns:
        bytes: ZIP archive bytes containing the shapefile components.
    """
    try:
        import geopandas as gpd
        import tempfile
        import os
        import zipfile
    except Exception:
        raise RuntimeError("geopandas and zipfile are required to write shapefile outputs.")

    with tempfile.TemporaryDirectory() as tmpdir:
        base = os.path.join(tmpdir, "out")
        # geopandas will create out.shp, out.dbf, etc.
        gdf.to_file(base + ".shp", driver="ESRI Shapefile")

        # Collect shapefile components
        files = [f for f in os.listdir(tmpdir) if f.startswith("out.")]
        zip_path = os.path.join(tmpdir, "out_shapefile.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for fname in files:
                z.write(os.path.join(tmpdir, fname), arcname=fname)

        with open(zip_path, "rb") as f:
            data = f.read()

    return data


def gdf_to_geojson_bytes(gdf):
    """Return GeoJSON bytes for a GeoDataFrame."""
    try:
        import tempfile
        import os
    except Exception:
        raise

    with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as tmp:
        tmpname = tmp.name
    try:
        gdf.to_file(tmpname, driver="GeoJSON")
        with open(tmpname, "rb") as f:
            data = f.read()
    finally:
        try:
            os.remove(tmpname)
        except Exception:
            pass

    return data


def utm_to_lat_lon(easting, northing, zone, hemisphere="N"):
    """Convert UTM coordinates to latitude and longitude (WGS84).

    Args:
        easting (float): UTM easting in meters.
        northing (float): UTM northing in meters.
        zone (int): UTM zone number.
        hemisphere (str): 'N' or 'S' for hemisphere.

    Returns:
        tuple: (latitude, longitude) in decimal degrees.
    """
    try:
        from pyproj import CRS, Transformer
    except Exception:
        raise RuntimeError("pyproj is required for UTM->lat/lon conversion. Please install pyproj.")

    # Build CRS for the UTM zone
    south = hemisphere.upper() == "S"
    # Use PROJ string to include south flag when needed
    proj_string = f"+proj=utm +zone={int(zone)} +datum=WGS84 +units=m +no_defs"
    if south:
        proj_string += " +south"

    crs_utm = CRS.from_proj4(proj_string)
    crs_geo = CRS.from_epsg(4326)
    transformer = Transformer.from_crs(crs_utm, crs_geo, always_xy=True)

    lon, lat = transformer.transform(easting, northing)
    return lat, lon


def dataframe_utm_to_latlon(df, easting_col="easting", northing_col="northing", zone_col="zone", hemisphere_col="hemisphere"):
    """Convert a pandas DataFrame with UTM columns to geographic coordinates.

    The dataframe must contain easting and northing columns. Zone is required; hemisphere is optional
    (if missing, the function will assume 'N' unless the user provides a constant hemisphere column).

    Returns a copy of the dataframe with added 'latitude' and 'longitude' columns, and also
    'latitude_dms' and 'longitude_dms' formatted using DMS with 5 decimal places for seconds.
    """
    try:
        import pandas as pd
    except Exception:
        raise

    if easting_col not in df.columns or northing_col not in df.columns or zone_col not in df.columns:
        raise ValueError(f"DataFrame must contain columns '{easting_col}', '{northing_col}' and '{zone_col}'")

    def _row_to_latlon(row):
        hemi = row[hemisphere_col] if hemisphere_col in df.columns else "N"
        lat, lon = utm_to_lat_lon(row[easting_col], row[northing_col], int(row[zone_col]), hemi)
        return lat, lon

    results = df.apply(_row_to_latlon, axis=1)
    results_df = pd.DataFrame(results.tolist(), index=df.index, columns=["latitude", "longitude"])

    out = df.copy()
    out = pd.concat([out, results_df], axis=1)
    # Add DMS formatted columns
    try:
        from .dms import format_dms
    except Exception:
        # fallback: try absolute import
        from utils.dms import format_dms

    out["latitude_dms"] = out["latitude"].apply(lambda x: format_dms(x, True))
    out["longitude_dms"] = out["longitude"].apply(lambda x: format_dms(x, False))
    return out