import streamlit as st
import pandas as pd
import folium
from folium import plugins
from streamlit_folium import folium_static
import glob
import logging
from datetime import datetime
import numpy as np
import os
import re
from folium.plugins import HeatMap

# Set up logging
logging.basicConfig(level=logging.INFO)  # Changed to INFO level

# Set page config with optimized settings
st.set_page_config(
    page_title="Mainz Data Visualization",
    layout="wide",
    initial_sidebar_state="collapsed"  # Start with collapsed sidebar
)

# Cache the station coordinates
@st.cache_data
def get_station_coords():
    return {
        'Ebersheim': (49.9275, 8.3458),
        'Finthen': (49.9733, 8.1750),
        'Gonsenheim': (49.9833, 8.2167),
        'Hartenberg': (49.9833, 8.2667),
        'Hechtsheim': (49.9667, 8.2500),
        'Laubenheim': (49.9333, 8.3000),
        'Lerchenberg': (49.9833, 8.2333),
        'Marienborn': (49.9667, 8.2167),
        'Mombach': (49.9833, 8.2167),
        'Neustadt': (49.9833, 8.2667),
        'Oberstadt': (49.9833, 8.2667),
        'Weisenau': (49.9667, 8.2833),
        'Bretzenheim': (49.9833, 8.2333)
    }

station_coords = get_station_coords()

# Optimize data loading with better caching
@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(current_dir), 'data')
        
        # Load and process data in parallel using st.cache_data
        @st.cache_data(ttl=3600)
        def load_weather():
            df = pd.read_csv(os.path.join(data_dir, 'monthly_means_weather.csv'))
            df['date'] = pd.to_datetime(df['month_year'], format='%B %Y')
            return df

        @st.cache_data(ttl=3600)
        def load_patients():
            df = pd.read_csv(os.path.join(data_dir, 'monthly_patients_by_station.csv'))
            df['date'] = pd.to_datetime(df['month_year'], format='%B %Y')
            df['station_name'] = df['closest_station'].str.replace('Mainz/', '')
            df['latitude'] = df['station_name'].map(lambda x: station_coords.get(x, [None, None])[0])
            df['longitude'] = df['station_name'].map(lambda x: station_coords.get(x, [None, None])[1])
            return df

        @st.cache_data(ttl=3600)
        def load_noise():
            noise_files = glob.glob(os.path.join(data_dir, 'monthly_means_*.csv'))
            noise_files = [f for f in noise_files if 'weather' not in f]
            
            noise_dfs = []
            for f in noise_files:
                try:
                    base_name = re.sub(r'monthly_means_|\.csv', '', os.path.basename(f))
                    base_name = re.sub(r'_\d+|_ooo', '', base_name)
                    if base_name in station_coords:
                        df = pd.read_csv(f)
                        df['station_name'] = base_name
                        df['date'] = pd.to_datetime(df['month_year'], format='%B %Y')
                        df['latitude'], df['longitude'] = station_coords[base_name]
                        noise_dfs.append(df)
                except Exception as e:
                    logging.warning(f"Error loading file {f}: {str(e)}")
                    continue
            
            return pd.concat(noise_dfs) if noise_dfs else pd.DataFrame()

        # Load all data
        weather = load_weather()
        patients = load_patients()
        noise_data = load_noise()
        
        return weather, patients, noise_data
    except Exception as e:
        logging.error(f"Error loading data: {str(e)}")
        return None, None, None

# Cache the visualization creation
@st.cache_data(ttl=300)  # Cache for 5 minutes
def create_visualization(selected_date, patients, noise_data):
    try:
        # Filter data for selected date
        filtered_patients = patients[patients['date'].dt.strftime('%Y-%m') == selected_date.strftime('%Y-%m')].dropna(subset=['latitude', 'longitude'])
        filtered_noise = noise_data[noise_data['date'].dt.strftime('%Y-%m') == selected_date.strftime('%Y-%m')].dropna(subset=['latitude', 'longitude'])

        # Create map with optimized settings
        m = folium.Map(
            location=[49.9929, 8.2473],
            zoom_start=11,
            tiles='CartoDB positron',  # Lighter tile set
            prefer_canvas=True  # Better performance
        )

        if not filtered_patients.empty:
            # Calculate min and max patient counts for scaling
            min_patients = filtered_patients['patient_count'].min()
            max_patients = filtered_patients['patient_count'].max()

            # Add patient circles with optimized settings
            for _, row in filtered_patients.iterrows():
                normalized_count = (row['patient_count'] - min_patients) / (max_patients - min_patients + 1e-5)
                radius = 5 + (15 * normalized_count)  # Simplified radius calculation
                
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=radius,
                    popup=f"{row['station_name']}: {row['patient_count']} patients",
                    color='blue',
                    fill=True,
                    fill_color='blue',
                    fill_opacity=0.4,
                    weight=1,
                    name='Patients'
                ).add_to(m)

        if not filtered_noise.empty:
            # Optimize heatmap data
            heat_data = filtered_noise[['latitude', 'longitude', 'db_a']].values.tolist()
            HeatMap(
                heat_data,
                name='Noise',
                gradient={0.4: 'orange', 0.7: 'red', 1: 'darkred'},
                radius=15,
                opacity=0.6,
                blur=10,
                max_zoom=1
            ).add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)

        return m, filtered_patients, filtered_noise
    except Exception as e:
        logging.error(f"Error creating visualization: {str(e)}")
        return None, None, None

# Main app code
def main():
    try:
        st.title('Spatio-Temporal Visualization of Aircraft Noise and Patients')
        
        # Load data with progress indicator
        with st.spinner('Loading data...'):
            weather, patients, noise_data = load_data()
        
        if weather is None or patients is None or noise_data is None:
            st.error("Failed to load data. Please try refreshing the page.")
            return

        # Get unique dates
        all_dates = np.unique(patients['date'].dt.to_pydatetime())
        min_date = all_dates[0]
        max_date = all_dates[-1]

        # Time slider with more descriptive format
        selected_date = st.slider(
            "Select Month and Year",
            min_value=min_date,
            max_value=max_date,
            value=min_date,
            format="MMMM YYYY"
        )

        # Convert selected_date back to pandas Timestamp
        selected_date = pd.Timestamp(selected_date)

        # Create visualization with progress indicator
        with st.spinner('Creating visualization...'):
            m, filtered_patients, filtered_noise = create_visualization(selected_date, patients, noise_data)

        if m is None:
            st.error("Failed to create visualization. Please try refreshing the page.")
            return

        # Display the map
        folium_static(m, width=800, height=600)

        # Add comprehensive guide
        st.markdown("""
        ### Visualization Guide

        #### Patient Data (Blue Circles)
        - Each blue circle represents a measurement station
        - The size of the circle indicates the number of patients
        - Larger circles = more patients
        - Click on any circle to see the exact patient count

        #### Noise Data (Red Heatmap)
        - The red heatmap shows aircraft noise levels
        - Color intensity indicates noise level:
          - Light orange = lower noise
          - Dark red = higher noise
        - The noise values are in decibels (dB)

        #### How to Use
        1. Use the slider above to select different months
        2. Toggle layers using the control in the top-right of the map
        3. Click on circles to see detailed information
        4. Use the layer control to show/hide patient or noise data
        """)

        # Add summary info
        st.subheader(f"Summary for {selected_date.strftime('%B %Y')}")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Mean Noise (dB)", f"{filtered_noise['db_a'].mean():.1f}")
        with col2:
            st.metric("Total Patients", f"{filtered_patients['patient_count'].sum()}")

    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        st.error("An error occurred. Please try refreshing the page.")

if __name__ == '__main__':
    main() 