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
from folium import CircleMarker, FeatureGroup

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Set page config
st.set_page_config(page_title="Mainz Data Visualization", layout="wide")

# Define station coordinates
station_coords = {
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

@st.cache_data
def load_data():
    # Get the current directory (src)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the parent directory (project root)
    parent_dir = os.path.dirname(current_dir)
    # Construct the data directory path
    data_dir = os.path.join(parent_dir, 'data')
    
    weather = pd.read_csv(os.path.join(data_dir, 'monthly_means_weather.csv'))
    weather['date'] = pd.to_datetime(weather['month_year'], format='%B %Y')

    patients = pd.read_csv(os.path.join(data_dir, 'monthly_patients_by_station.csv'))
    patients['date'] = pd.to_datetime(patients['month_year'], format='%B %Y')
    patients['station_name'] = patients['closest_station'].str.replace('Mainz/', '')
    patients['latitude'] = patients['station_name'].map(lambda x: station_coords.get(x, [None, None])[0])
    patients['longitude'] = patients['station_name'].map(lambda x: station_coords.get(x, [None, None])[1])

    noise_files = glob.glob(os.path.join(data_dir, 'monthly_means_*.csv'))
    noise_files = [f for f in noise_files if 'weather' not in f]
    noise_dfs = []
    for f in noise_files:
        base_name = re.sub(r'monthly_means_|\.csv', '', os.path.basename(f))
        base_name = re.sub(r'_\d+|_ooo', '', base_name)
        if base_name in station_coords:
            df = pd.read_csv(f)
            df['station_name'] = base_name
            df['date'] = pd.to_datetime(df['month_year'], format='%B %Y')
            df['latitude'], df['longitude'] = station_coords[base_name]
            noise_dfs.append(df)
    noise_data = pd.concat(noise_dfs)

    return weather, patients, noise_data

weather, patients, noise_data = load_data()

st.title('Spatio-Temporal Visualization of Aircraft Noise and Patients')

# Convert dates to datetime objects for the slider
all_dates = sorted(patients['date'].unique())
date_options = [d.strftime('%Y-%m-%d') for d in all_dates]
selected_date_str = st.select_slider(
    "Select Date",
    options=date_options,
    value=date_options[0]
)
selected_date = pd.to_datetime(selected_date_str)

# Filtered data
filtered_patients = patients[patients['date'] == selected_date].dropna(subset=['latitude', 'longitude'])
filtered_noise = noise_data[noise_data['date'] == selected_date].dropna(subset=['latitude', 'longitude'])

# Normalize values for color intensities
def normalize(series):
    return (series - series.min()) / (series.max() - series.min() + 1e-5)

filtered_noise['intensity'] = normalize(filtered_noise['db_a'])

# Create map
m = folium.Map(location=[49.9929, 8.2473], zoom_start=11)

# Create feature groups for each layer
noise_group = FeatureGroup(name='Aircraft Noise', show=True)
patient_group = FeatureGroup(name='Patients', show=True)

# Add noise layer (red heatmap)
heat_noise = [[row['latitude'], row['longitude'], row['intensity']] for _, row in filtered_noise.iterrows()]
HeatMap(heat_noise, 
        name='Aircraft Noise',
        gradient={0.4: 'yellow', 0.65: 'orange', 0.85: 'red', 1: 'darkred'},
        radius=15,
        blur=10,
        max_zoom=1).add_to(noise_group)

# Calculate the maximum number of patients for scaling
max_patients = filtered_patients['patient_count'].max()

# Add patient markers (concentric circles)
for _, row in filtered_patients.iterrows():
    num_patients = row['patient_count']
    
    # Calculate radius based on number of patients
    radius = 8 + (num_patients / max_patients) * 20
    
    # Create a cluster of circles
    for i in range(3):  # Three concentric circles
        current_radius = radius * (1 - i * 0.2)  # Decrease radius for inner circles
        CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=current_radius,
            popup=f"{row['station_name']}: {num_patients} patients",
            color='#1f77b4',  # A distinct blue color
            fill=True,
            fill_color='#1f77b4',
            fill_opacity=0.2,  # Very transparent
            weight=2,  # Thicker border
            opacity=0.8  # More visible border
        ).add_to(patient_group)

# Add feature groups to map
noise_group.add_to(m)
patient_group.add_to(m)

# Add layer control
folium.LayerControl().add_to(m)

# Display the map
folium_static(m)

# Optional: Add summary info
col1, col2 = st.columns(2)
with col1:
    st.metric("Mean Noise (dB)", f"{filtered_noise['db_a'].mean():.1f}")
with col2:
    st.metric("Total Patients", f"{filtered_patients['patient_count'].sum()}")

# Add legend with more details
st.markdown("""
### Legend
- 🟡🔴 Aircraft Noise Heatmap:
  - Yellow: Low noise levels
  - Orange: Medium noise levels
  - Red: High noise levels
  - Dark Red: Very high noise levels

- 🔵 Patient Locations:
  - Blue circles: Size indicates number of patients
  - Multiple concentric circles: Higher patient density
  - Click on circles to see exact patient count
""")

# Add instructions
st.markdown("""
### How to Use
1. Use the date slider to select a time period
2. Toggle layers on/off using the layer control in the top right of the map
3. Click on patient circles to see detailed information
4. The heatmap shows aircraft noise intensity across the area
""") 