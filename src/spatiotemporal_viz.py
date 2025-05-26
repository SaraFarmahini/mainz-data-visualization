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
    # Get the current directory (src) and go up one level to find the data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(current_dir), 'data')
    
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

def create_visualization(selected_date, patients, noise_data):
    # Filter data for selected date
    filtered_patients = patients[patients['date'].dt.strftime('%Y-%m') == selected_date.strftime('%Y-%m')].dropna(subset=['latitude', 'longitude'])
    filtered_noise = noise_data[noise_data['date'].dt.strftime('%Y-%m') == selected_date.strftime('%Y-%m')].dropna(subset=['latitude', 'longitude'])

    # Debug information
    st.write(f"Selected date: {selected_date.strftime('%B %Y')}")
    st.write(f"Number of patient records: {len(filtered_patients)}")
    st.write(f"Number of noise records: {len(filtered_noise)}")

    # Create map
    m = folium.Map(location=[49.9929, 8.2473], zoom_start=11)

    if not filtered_patients.empty:
        # Calculate min and max patient counts for scaling
        min_patients = filtered_patients['patient_count'].min()
        max_patients = filtered_patients['patient_count'].max()

        # Add patient circles
        for _, row in filtered_patients.iterrows():
            # Calculate circle radius based on patient count (scaled for visibility)
            base_size = 5  # Minimum circle size
            max_size = 20  # Maximum circle size
            
            # Normalize patient count between 0 and 1
            normalized_count = (row['patient_count'] - min_patients) / (max_patients - min_patients + 1e-5)
            
            # Calculate radius using logarithmic scaling
            radius = base_size + (max_size - base_size) * np.log1p(normalized_count * 9) / np.log1p(9)
            
            # Create circle marker
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
        # Normalize noise values for heatmap
        filtered_noise['intensity'] = (filtered_noise['db_a'] - filtered_noise['db_a'].min()) / (filtered_noise['db_a'].max() - filtered_noise['db_a'].min() + 1e-5)
        
        # Add noise heatmap
        heat_noise = [[row['latitude'], row['longitude'], row['intensity']] for _, row in filtered_noise.iterrows()]
        HeatMap(
            heat_noise,
            name='Noise',
            gradient={0.4: 'orange', 0.7: 'red', 1: 'darkred'},
            radius=15,
            opacity=0.6
        ).add_to(m)

    # Add layer control
    folium.LayerControl().add_to(m)

    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; height: 120px; 
                border:2px solid grey; z-index:9999; font-size:14px;
                background-color:white;
                padding: 10px;
                border-radius: 5px;">
        <p><strong>Map Legend</strong></p>
        <p><span style="color: blue;">●</span> Patient Count (Circle Size)</p>
        <p><span style="color: red;">●</span> Noise Level (Heatmap)</p>
        <p style="font-size: 12px; color: #666;">Click on circles to see exact values</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    return m, filtered_patients, filtered_noise

# Load data
weather, patients, noise_data = load_data()

st.title('Spatio-Temporal Visualization of Aircraft Noise and Patients')

# Get unique dates and convert to datetime objects
all_dates = np.unique(patients['date'].dt.to_pydatetime())
min_date = all_dates[0]
max_date = all_dates[-1]

# Time slider with more descriptive format
selected_date = st.slider(
    "Select Month and Year",
    min_value=min_date,
    max_value=max_date,
    value=min_date,
    format="MMMM YYYY"  # Full month name and year
)

# Convert selected_date back to pandas Timestamp for filtering
selected_date = pd.Timestamp(selected_date)

# Create visualization
m, filtered_patients, filtered_noise = create_visualization(selected_date, patients, noise_data)

# Display the map
folium_static(m)

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

# Add station-wise breakdown
st.subheader("Station-wise Breakdown")
station_data = filtered_patients.merge(
    filtered_noise[['station_name', 'db_a']],
    on='station_name',
    how='left'
)
station_data = station_data[['station_name', 'patient_count', 'db_a']].sort_values('patient_count', ascending=False)
st.dataframe(station_data.style.format({'db_a': '{:.1f}'})) 