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

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define station coordinates directly (temporary solution)
station_coords = {
    'Bretzenheim': [49.9833, 8.2667],
    'Ebersheim': [49.9333, 8.2333],
    'Hechtsheim': [49.9833, 8.2667],
    'Laubenheim': [49.9667, 8.2833],
    'Lerchenberg': [49.9833, 8.2333],
    'Oberstadt': [49.9833, 8.2667],
    'Weisenau': [49.9667, 8.2833]
}

def get_base_station_name(filename):
    """Extract base station name from filename, handling numbered stations"""
    # Remove 'monthly_means_' prefix and '.csv' suffix
    name = filename.replace('monthly_means_', '').replace('.csv', '')
    
    # Extract base name and number if present
    match = re.match(r'([A-Za-z]+)(?:_(\d+))?(?:_ooo)?', name)
    if match:
        base_name = match.group(1)
        number = match.group(2)
        return base_name, number
    return name, None

# Load the data
@st.cache_data
def load_data():
    try:
        logging.info("Starting to load data...")
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Get the project root directory (one level up from src)
        project_root = os.path.dirname(current_dir)
        # Construct the data directory path
        data_dir = os.path.join(project_root, 'data')
        
        # Load weather data first
        logging.info("Loading weather data...")
        weather_path = os.path.join(data_dir, 'monthly_means_weather.csv')
        weather = pd.read_csv(weather_path)
        weather['date'] = pd.to_datetime(weather['month_year'], format='%B %Y')
        
        # Load patient data
        logging.info("Loading patient data...")
        patients_path = os.path.join(data_dir, 'monthly_patients_by_station.csv')
        patients = pd.read_csv(patients_path)
        patients['date'] = pd.to_datetime(patients['month_year'], format='%B %Y')
        
        # Extract station name from closest_station (remove 'Mainz/' prefix)
        patients['station_name'] = patients['closest_station'].str.replace('Mainz/', '')
        
        # Add coordinates to patient data
        patients['latitude'] = patients['station_name'].map(lambda x: station_coords.get(x, [None, None])[0])
        patients['longitude'] = patients['station_name'].map(lambda x: station_coords.get(x, [None, None])[1])
        
        # Load aircraft noise data
        logging.info("Loading aircraft noise data...")
        noise_files = glob.glob(os.path.join(data_dir, 'monthly_means_*.csv'))
        noise_files = [f for f in noise_files if 'weather' not in f]
        
        # Create a dictionary to store DataFrames by base station name
        station_data_dict = {}
        
        for file in noise_files:
            try:
                df = pd.read_csv(file)
                base_station, number = get_base_station_name(os.path.basename(file))
                
                if base_station in station_coords:
                    df['station_name'] = base_station
                    df['station_number'] = number
                    df['date'] = pd.to_datetime(df['month_year'], format='%B %Y')
                    df['latitude'] = station_coords[base_station][0]
                    df['longitude'] = station_coords[base_station][1]
                    
                    if base_station not in station_data_dict:
                        station_data_dict[base_station] = []
                    station_data_dict[base_station].append(df)
                else:
                    logging.warning(f"Skipping unknown station: {base_station}")
            except Exception as e:
                logging.error(f"Error processing file {file}: {str(e)}")
                continue
        
        # Combine data for stations with multiple measurements
        noise_data = pd.DataFrame()
        for base_station, dfs in station_data_dict.items():
            if len(dfs) > 1:
                # Multiple measurements exist, calculate mean
                combined_df = pd.concat(dfs)
                mean_df = combined_df.groupby(['month_year', 'date', 'station_name', 'latitude', 'longitude'])['db_a'].mean().reset_index()
                noise_data = pd.concat([noise_data, mean_df], ignore_index=True)
            else:
                # Only one measurement exists, use it directly
                noise_data = pd.concat([noise_data, dfs[0]], ignore_index=True)
        
        logging.info("Data loading completed successfully")
        return None, weather, patients, noise_data
    except Exception as e:
        logging.error(f"Error loading data: {str(e)}")
        st.error(f"Error loading data: {str(e)}")
        return None, None, None, None

def filter_data_by_date(data, selected_date, frequency):
    """Filter data based on selected date and frequency"""
    if frequency == 'Monthly':
        return data[
            (data['date'].dt.year == selected_date.year) & 
            (data['date'].dt.month == selected_date.month)
        ]
    else:  # Annual
        return data[data['date'].dt.year == selected_date.year]

# Function to create a heatmap
def create_heatmap(data, data_type, frequency, selected_date, weather_data=None):
    try:
        logging.info(f"Creating heatmap for {data_type} with {frequency} frequency for date {selected_date}")
        
        # Create a map centered at Mainz
        m = folium.Map(location=[49.9929, 8.2473], zoom_start=11)
        
        # Filter data based on selected date
        filtered_data = filter_data_by_date(data, selected_date, frequency)
        
        if filtered_data.empty:
            st.warning(f"No data available for {selected_date.strftime('%B %Y' if frequency == 'Monthly' else '%Y')}")
            return m
        
        # Calculate and display mean temperature if weather data is provided
        if weather_data is not None:
            filtered_weather = filter_data_by_date(weather_data, selected_date, frequency)
            if not filtered_weather.empty:
                mean_temp = filtered_weather['TT_10'].mean()
                temp_html = f"""
                    <div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000; background-color: white; 
                    padding: 10px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.2);">
                        <b>Mean Temperature: {mean_temp:.1f}°C</b>
                    </div>
                """
                m.get_root().html.add_child(folium.Element(temp_html))
        
        # Add markers for each station
        for idx, row in filtered_data.drop_duplicates('station_name').iterrows():
            if data_type == 'Patients':
                value = row['patient_count']
                unit = 'patients'
            else:  # Aircraft Noise
                value = row['db_a']
                unit = 'dB'
            
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=f"{row['station_name']} - {data_type} - Value: {value:.1f}{unit}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        
        # Prepare data for heatmap with weights
        heat_data = []
        for _, row in filtered_data.iterrows():
            if data_type == 'Patients':
                value = row['patient_count']
            else:  # Aircraft Noise
                value = row['db_a']
            
            # Normalize the value for better visualization
            min_val = filtered_data['patient_count'].min() if data_type == 'Patients' else filtered_data['db_a'].min()
            max_val = filtered_data['patient_count'].max() if data_type == 'Patients' else filtered_data['db_a'].max()
            normalized_value = (value - min_val) / (max_val - min_val) if max_val != min_val else 0.5
            
            heat_data.append([row['latitude'], row['longitude'], normalized_value])
        
        # Add heatmap layer
        plugins.HeatMap(heat_data).add_to(m)
        
        return m
    except Exception as e:
        logging.error(f"Error creating heatmap: {str(e)}")
        st.error(f"Error creating heatmap: {str(e)}")
        return folium.Map(location=[49.9929, 8.2473], zoom_start=11)

def main():
    try:
        st.title('Station Data Visualization')
        
        # Load data
        _, weather, patients, noise_data = load_data()
        
        if weather is None or patients is None or noise_data is None:
            st.error("Failed to load data. Please check the logs for more details.")
            return
        
        # Sidebar for options
        st.sidebar.header('Options')
        data_type = st.sidebar.selectbox('Select Data Type', ['Aircraft Noise', 'Patients'])
        frequency = st.sidebar.selectbox('Select Frequency', ['Annual', 'Monthly'])
        
        # Date selection based on frequency
        if frequency == 'Monthly':
            year = st.sidebar.selectbox('Select Year', range(2012, 2025))
            month = st.sidebar.selectbox('Select Month', range(1, 13))
            selected_date = datetime(year, month, 1)
        else:  # Annual
            year = st.sidebar.selectbox('Select Year', range(2012, 2025))
            selected_date = datetime(year, 1, 1)
        
        # Filter data based on selection
        if data_type == 'Aircraft Noise':
            data = noise_data
        else:  # Patients
            data = patients
        
        # Create heatmap
        heatmap = create_heatmap(data, data_type, frequency, selected_date, weather)
        
        # Display the map
        folium_static(heatmap)
        
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    main() 