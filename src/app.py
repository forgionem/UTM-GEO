import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from utils.utm import (
    lat_lon_to_utm,
    dataframe_latlon_to_utm,
    utm_to_lat_lon,
    dataframe_utm_to_latlon,
    read_shapefile_zip_to_gdf,
    transform_gdf_to_utm,
    gdf_to_shapefile_zip_bytes,
    gdf_to_geojson_bytes,
)
from utils.dms import format_dms
from components.input_form import render_input_form


def main():
    st.title("Convertidor de Coordenadas UTM <---> Geográficas (Datum WGS84):")
    st.write("El programa fue desarrollado por Mario Forgione López, para facilitar la conversión entre coordenadas geográficas (latitud/longitud) y coordenadas UTM en el sistema WGS-84. Utiliza Streamlit para la interfaz web y bibliotecas geoespaciales como geopandas y pyproj para las transformaciones de coordenadas.")
    st.write("Perfil de LinkedIn: https://linkedin.com/in/mario-forgione")
    st.write("**** Nota: Está en fase de prueba, por favor use con precaución bajo su responsabilidad ****")
    st.write("Seleccionar el sentido de la transformación (punto simple o carga de archivo de puntos CSV o Shapefile).")

    direction = st.radio("Conversion direction", ["Geographic -> UTM", "UTM -> Geographic"]) 

    # For geographic->UTM we reuse the input form which provides lat/lon or a dataframe
    lat, lon, df = (None, None, None)
    if direction == "Geographic -> UTM":
        st.write("Introducir la latitud y longitud en grados decimales o DMS y presionar Convertir.")
        lat, lon, df = render_input_form()
    else:
        st.write("Introducir UTM easting/northing y zona (punto simple) o cargar un CSV con columnas UTM para conversión por lotes.")

    # Geographic -> UTM: Batch conversion from uploaded dataframe
    if direction == "Geographic -> UTM" and df is not None:
        try:
            out_df = dataframe_latlon_to_utm(df, lat_col="latitude", lon_col="longitude")
            st.success("Conversión por lotes exitosa")
            st.dataframe(out_df.head(100))

            csv = out_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Descargar CSV convertido",
                data=csv,
                file_name="utm_converted.csv",
                mime="text/csv",
            )
            # Plot the input geographic points on a map (latitude/longitude)
            try:
                # (debug prints removed) show only table above and the map below
                pass
                
                plot_df = out_df[["latitude", "longitude"]].dropna()
                if not plot_df.empty:
                    
                    # Crear mapa base
                    m = folium.Map()
                    
                    # Marcadores para cada punto
                    points = []
                    for _, row in plot_df.iterrows():
                        lat, lon = row["latitude"], row["longitude"]
                        points.append([lat, lon])
                        folium.Circle(
                            location=[lat, lon],
                            radius=50,  # Radio en metros
                            color='blue',
                            fill=True,
                            popup=f"Lat: {lat:.6f}<br>Lon: {lon:.6f}"
                        ).add_to(m)
                    
                    if points:
                        # Calcular el centro y ajustar el zoom
                        bounds = [[min(p[0] for p in points), min(p[1] for p in points)],
                                [max(p[0] for p in points), max(p[1] for p in points)]]
                        m.fit_bounds(bounds)
                    
                    # Agregar control de escala
                    folium.map.LayerControl().add_to(m)
                    
                    # Mostrar el mapa
                    folium_static(m)
                else:
                    st.warning("No se encontraron coordenadas válidas para mostrar en el mapa")
                    
            except Exception as e:
                st.error("Error al mostrar el mapa:")
                st.error(str(e))
                st.write("Detalles del error:", {
                    "tipo": type(e).__name__,
                    "módulo": e.__class__.__module__
                })
        except Exception as e:
            st.error(f"Error converting uploaded CSV: {e}")

    # Geographic -> UTM: Single-point conversion (only when no dataframe was uploaded)
    if direction == "Geographic -> UTM" and lat is not None and lon is not None and df is None:
        try:
            easting, northing, zone, hemisphere = lat_lon_to_utm(lat, lon)
            st.success("Conversión exitosa")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("UTM Zone", f"{zone}{hemisphere}")
                st.metric("Easting (m)", f"{easting:.3f}")
            with col2:
                st.metric("Northing (m)", f"{northing:.3f}")
                st.info(f"Input: {lat:.6f}, {lon:.6f}")

            # show the original point on a small map (latitude, longitude)
            try:
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    st.warning("⚠️ Las coordenadas están fuera de rango: lat debe estar entre -90 y 90, lon entre -180 y 180")
                else:
                    # Crear mapa centrado en el punto
                    m = folium.Map(location=[lat, lon], zoom_start=10)
                    # Agregar marcador
                    folium.Marker(
                        [lat, lon],
                        popup=f"Lat: {lat:.6f}, Lon: {lon:.6f}",
                        tooltip="Punto"
                    ).add_to(m)
                    # Mostrar el mapa
                    folium_static(m)
            except Exception as e:
                st.error(f"Error al mostrar el mapa: {str(e)}")
                st.write("Tipo de error:", type(e).__name__)

        except Exception as e:
            st.error(f"Error converting coordinates: {e}")

    # UTM -> Geographic
    if direction == "UTM -> Geographic":
        st.markdown("---")
        st.subheader("Punto simple UTM -> Geographic")
        col1, col2, col3 = st.columns([2,2,1])
        with col1:
            easting = st.number_input("Easting (m)", value=500000.0, format="%.3f")
        with col2:
            northing = st.number_input("Northing (m)", value=0.0, format="%.3f")
        with col3:
            zone = st.number_input("Zone", min_value=1, max_value=60, value=31, step=1)
        hemi = st.selectbox("Hemisphere", options=["N", "S"], index=0)
        if st.button("Convert UTM -> Lat/Lon"):
            try:
                lat_out, lon_out = utm_to_lat_lon(easting, northing, int(zone), hemi)
                st.success("Conversión exitosa")
                st.metric("Latitude", f"{lat_out:.6f}°")
                st.metric("Longitude", f"{lon_out:.6f}°")
                
                st.caption("DMS format:")
                st.code(f"Lat: {format_dms(lat_out, True)}\nLon: {format_dms(lon_out, False)}")
                
                try:
                    if not (-90 <= lat_out <= 90) or not (-180 <= lon_out <= 180):
                        st.warning("⚠️ Las coordenadas están fuera de rango: lat debe estar entre -90 y 90, lon entre -180 y 180")
                    else:
                        # Crear mapa centrado en el punto
                        m = folium.Map(location=[lat_out, lon_out], zoom_start=10)
                        # Agregar marcador
                        folium.Marker(
                            [lat_out, lon_out],
                            popup=f"Lat: {lat_out:.6f}, Lon: {lon_out:.6f}",
                            tooltip="Punto"
                        ).add_to(m)
                        # Mostrar el mapa
                        folium_static(m)
                except Exception as e:
                    st.error(f"Error al mostrar el mapa: {str(e)}")
                    st.write("Tipo de error:", type(e).__name__)
            except Exception as e:
                st.error(f"Error converting UTM to geographic: {e}")

        st.markdown("---")
        st.subheader("Archivo UTM -> Geographic (Subir archivo CSV)")
        uploaded_utm = st.file_uploader("Subir archivo CSV con columnas UTM (easting,northing,zone,hemisphere opcional)", type=["csv"], key="utm_batch")
        if uploaded_utm is not None:
            try:
                df_utm = pd.read_csv(uploaded_utm)
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
                df_utm = None

            if df_utm is not None:
                st.write("Preview:")
                st.dataframe(df_utm.head())

                # detect columns
                cols = list(df_utm.columns)
                def detect(cands):
                    for c in cols:
                        if c.lower() in cands:
                            return c
                    return None

                e_col = detect(["easting", "x", "utm_easting"] ) or cols[0]
                n_col = detect(["northing", "y", "utm_northing"]) or (cols[1] if len(cols) > 1 else cols[0])
                z_col = detect(["zone"]) or (cols[2] if len(cols) > 2 else cols[0])
                h_col = detect(["hemisphere", "hem"] )

                sel_e = st.selectbox("Easting column", options=cols, index=cols.index(e_col))
                sel_n = st.selectbox("Northing column", options=cols, index=cols.index(n_col))
                sel_z = st.selectbox("Zone column", options=cols, index=cols.index(z_col) if z_col in cols else 0)
                if h_col:
                    sel_h = st.selectbox("Hemisphere column", options=[None] + cols, index=cols.index(h_col)+1)
                else:
                    sel_h = None

                default_hemi = st.selectbox("Hemisferio por defecto (si falta)", options=["N","S"], index=0)

                if st.button("Convertir archivo UTM -> Lat/Lon"):
                    try:
                        # If hemisphere column not provided, add default
                        df2 = df_utm.copy()
                        if sel_h is None:
                            df2["hemisphere"] = default_hemi
                            hemi_col = "hemisphere"
                        else:
                            hemi_col = sel_h

                        out = dataframe_utm_to_latlon(df2, easting_col=sel_e, northing_col=sel_n, zone_col=sel_z, hemisphere_col=hemi_col)
                        st.success("Conversión por lotes UTM->LatLon exitosa")
                        st.dataframe(out.head())
                        # Plot converted geographic points
                        try:
                            plot_df = out[["latitude", "longitude"]].dropna()
                            if not plot_df.empty:
                                # Mostrar puntos convertidos en un mapa (folium)
                                center_lat = plot_df["latitude"].mean()
                                center_lon = plot_df["longitude"].mean()
                                m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
                                for idx, row in plot_df.iterrows():
                                    folium.Circle(
                                        location=[row["latitude"], row["longitude"]],
                                        radius=50,
                                        color='green',
                                        fill=True,
                                        popup=f"Lat: {row['latitude']:.6f}<br>Lon: {row['longitude']:.6f}"
                                    ).add_to(m)
                                if not plot_df.empty:
                                    bounds = [[plot_df["latitude"].min(), plot_df["longitude"].min()], [plot_df["latitude"].max(), plot_df["longitude"].max()]]
                                    m.fit_bounds(bounds)
                                folium_static(m)
                        except Exception:
                            pass

                        csv = out.to_csv(index=False).encode("utf-8")
                        st.download_button("Descargar CSV convertido", data=csv, file_name="latlon_converted.csv", mime="text/csv")
                    except Exception as e:
                        st.error(f"Error converting uploaded UTM CSV: {e}")

    # Vector/shapefile support (zipped shapefile)
    st.markdown("---")
    st.subheader("Conversión de Shapefile (.zip)")
    st.write("Subir un archivo shapefile comprimido (.zip que contenga .shp/.shx/.dbf/.prj). La aplicación intentará leer y convertir las geometrías.")
    uploaded_shp = st.file_uploader("Subir archivo shapefile zip", type=["zip"], key="shp_upload")
    if uploaded_shp is not None:
        try:
            gdf = read_shapefile_zip_to_gdf(uploaded_shp)
        except Exception as e:
            st.error(f"Error reading shapefile: {e}")
            gdf = None

        if gdf is not None:
            st.write("Previsualización de las primeras filas del Shapefile:")
            st.dataframe(gdf.head())

            if direction == "Geographic -> UTM":
                st.info("Transformar las geometrías del shapefile de geográficas a UTM.")
                zone_input = st.number_input("Forzar zona UTM (dejar 0 para detección automática)", min_value=0, max_value=60, value=0, step=1)
                if st.button("Convertir shapefile a UTM"):
                    try:
                        z = None if zone_input == 0 else int(zone_input)
                        gdf_utm, zone_used, hemi = transform_gdf_to_utm(gdf, zone=z)
                        st.success(f"Shapefile transformado a UTM zona {zone_used}{hemi}")
                        st.dataframe(gdf_utm.head())
                        # Nota: la visualización en mapa para shapefiles ha sido deshabilitada temporalmente.
                        # Se mantiene la previsualización de la tabla y las opciones de descarga.
                        st.info("Visualización en mapa deshabilitada para shapefiles. Use la descarga GeoJSON/Shapefile para visualizar en su SIG de escritorio.")
                        # Offer downloads: GeoJSON and zipped shapefile
                        geojson_bytes = gdf_to_geojson_bytes(gdf_utm)
                        shp_zip = gdf_to_shapefile_zip_bytes(gdf_utm)
                        st.download_button("Download GeoJSON", data=geojson_bytes, file_name=f"shapefile_utm_zone{zone_used}.geojson", mime="application/geo+json")
                        st.download_button("Download zipped Shapefile", data=shp_zip, file_name=f"shapefile_utm_zone{zone_used}.zip", mime="application/zip")
                    except Exception as e:
                        st.error(f"Error transforming shapefile to UTM: {e}")

            else:  # UTM -> Geographic
                st.info("Transformar las geometrías del shapefile de UTM a geográficas. Si el shapefile no tiene CRS, proporcionar zona y hemisferio UTM.")
                # If the gdf has a CRS, show it and offer to use it
                crs_info = str(gdf.crs) if gdf.crs is not None else "None"
                st.write(f"CRS detectado: {crs_info}")
                use_detected = True if gdf.crs is not None else False
                if not use_detected:
                    st.write("Proveer zona y hemisferio UTM para el shapefile (si falta CRS)")
                zone_input = st.number_input("Zona UTM para el shapefile (si es desconocida)", min_value=1, max_value=60, value=31, step=1)
                hemi_input = st.selectbox("Hemisferio para el shapefile (si es desconocido)", options=["N","S"], index=0)

                if st.button("Convertir shapefile a Geográficas"):
                    try:
                        # If CRS exists and is not geographic, attempt to transform directly
                        if gdf.crs is not None:
                            # Try to convert to EPSG:4326
                            gdf_geo = gdf.to_crs(epsg=4326)
                        else:
                            # Assign UTM CRS from zone/hemi
                            from pyproj import CRS
                            proj_string = f"+proj=utm +zone={int(zone_input)} +datum=WGS84 +units=m +no_defs"
                            if hemi_input.upper() == "S":
                                proj_string += " +south"
                            crs_utm = CRS.from_proj4(proj_string)
                            gdf = gdf.set_crs(crs_utm)
                            gdf_geo = gdf.to_crs(epsg=4326)

                        st.success("Shapefile transformado a geográficas (WGS84)")
                        st.dataframe(gdf_geo.head())
                        # Nota: la visualización en mapa para shapefiles ha sido deshabilitada temporalmente.
                        # Se mantiene la previsualización de la tabla y las opciones de descarga.
                        st.info("Visualización en mapa deshabilitada para shapefiles. Use la descarga GeoJSON/Shapefile para visualizar en su SIG de escritorio.")
                        geojson_bytes = gdf_to_geojson_bytes(gdf_geo)
                        shp_zip = gdf_to_shapefile_zip_bytes(gdf_geo)
                        st.download_button("Download GeoJSON", data=geojson_bytes, file_name="shapefile_geographic.geojson", mime="application/geo+json")
                        st.download_button("Download zipped Shapefile", data=shp_zip, file_name="shapefile_geographic.zip", mime="application/zip")
                    except Exception as e:
                        st.error(f"Error transforming shapefile to geographic: {e}")


if __name__ == "__main__":
    main()