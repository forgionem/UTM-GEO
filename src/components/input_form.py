"""Components for rendering coordinate input forms in various formats."""

import streamlit as st
import pandas as pd
from utils.dms import dms_to_decimal_degrees, parse_dms, format_dms


def _detect_lat_lon_columns(df: pd.DataFrame):
    """Return best-guess column names for latitude and longitude in the dataframe."""
    lat_candidates = [c for c in df.columns if c.lower() in ("lat", "latitude", "y")]
    lon_candidates = [c for c in df.columns if c.lower() in ("lon", "longitude", "x")]

    lat_col = lat_candidates[0] if lat_candidates else df.columns[0]
    lon_col = lon_candidates[0] if lon_candidates else (df.columns[1] if len(df.columns) > 1 else df.columns[0])
    return lat_col, lon_col


def render_dms_input(label, is_latitude=True):
    """Render degree, minute, second inputs with validation.
    
    Args:
        label (str): Label to show (e.g., "Latitude" or "Longitude")
        is_latitude (bool): True if this is latitude input (±90°), False for longitude (±180°)
    
    Returns:
        tuple: (decimal_degrees, dms_str) or (None, None) if invalid
    """
    max_deg = 90 if is_latitude else 180
    coord_type = "lat" if is_latitude else "lon"
    
    col1, col2, col3 = st.columns([2,2,3])
    with col1:
        degrees = st.number_input(
            f"{label} degrees",
            min_value=-max_deg,
            max_value=max_deg,
            value=0,
            step=1,
            key=f"dms_{coord_type}_deg"
        )
    with col2:
        minutes = st.number_input(
            "minutes",
            min_value=0,
            max_value=59,
            value=0,
            step=1,
            key=f"dms_{coord_type}_min"
        )
    with col3:
        seconds = st.number_input(
            "seconds",
            min_value=0.0,
            max_value=59.99999,
            value=0.0,
            format="%.5f",
            step=0.00001,
            key=f"dms_{coord_type}_sec"
        )
    
    try:
        decimal = dms_to_decimal_degrees(degrees, minutes, seconds)
        dms_str = format_dms(decimal, is_latitude)
        return decimal, dms_str
    except Exception:
        return None, None


def render_input_form():
    """Render input fields and a CSV uploader.

    Returns:
        tuple: (lat, lon, dataframe)
            - If user used DD form and pressed Convert: (lat, lon, None)
            - If user used DMS form and pressed Convert: (lat, lon, None)
            - If user uploaded a CSV and selected columns: (None, None, dataframe_with_lat_lon)
            - Otherwise: (None, None, None)
    """
    st.subheader("Input coordinates")
    
    format_type = st.radio(
        "Coordinate format",
        ["Decimal Degrees", "Degrees Minutes Seconds (DMS)"]
    )

    if format_type == "Decimal Degrees":
        # Single-point DD inputs
        col1, col2 = st.columns(2)
        with col1:
            lat = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=0.0,
                format="%.6f",
                step=0.000001,
            )
        with col2:
            lon = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=0.0,
                format="%.6f",
                step=0.000001,
            )

        # Show DMS equivalent
        st.caption("Equivalent DMS format:")
        st.code(f"Lat: {format_dms(lat, True)}\nLon: {format_dms(lon, False)}")

    else:  # DMS input
        lat, lat_dms = render_dms_input("Latitude", is_latitude=True)
        lon, lon_dms = render_dms_input("Longitude", is_latitude=False)
        
        if lat is not None and lon is not None:
            st.caption("Equivalent decimal degrees:")
            st.code(f"Lat: {lat:.6f}°\nLon: {lon:.6f}°")

    convert = st.button("Convert")
    if convert:
        if format_type == "Decimal Degrees":
            return lat, lon, None
        else:
            if lat is not None and lon is not None:
                return lat, lon, None
            else:
                st.error("Invalid DMS values")
                return None, None, None

    st.markdown("---")
    st.info("Or upload a CSV file with coordinates")

    csv_format = st.radio(
        "CSV coordinate format",
        ["Decimal Degrees", "DMS"],
        key="csv_format"
    )

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            return None, None, None

        st.write("Preview (first 5 rows):")
        st.dataframe(df.head())

        lat_col, lon_col = _detect_lat_lon_columns(df)
        st.write("Select coordinate columns:")
        col_lat = st.selectbox("Latitude column", options=list(df.columns), index=list(df.columns).index(lat_col))
        col_lon = st.selectbox("Longitude column", options=list(df.columns), index=list(df.columns).index(lon_col))

        if st.button("Convert uploaded CSV"):
            df2 = df.copy()
            
            if csv_format == "DMS":
                # Convert DMS strings to decimal degrees
                try:
                    df2["latitude"] = df2[col_lat].apply(parse_dms)
                    df2["longitude"] = df2[col_lon].apply(parse_dms)
                except Exception as e:
                    st.error(f"Error parsing DMS values: {e}")
                    return None, None, None
            else:
                # Just rename columns for decimal degrees
                df2 = df2.rename(columns={col_lat: "latitude", col_lon: "longitude"})
            
            return None, None, df2

    return None, None, None