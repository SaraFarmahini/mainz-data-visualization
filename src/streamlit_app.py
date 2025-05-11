import streamlit as st
import pandas as pd
import folium
from folium import plugins
from streamlit_folium import folium_static
import glob
import logging
from datetime import datetime
import numpy as np

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define station coordinates directly (temporary solution)
station_coords = {
    'Bretzenheim': [49.9833, 8.2667],
    'Finthen': [49.9833, 8.2333],
    'Gonsenheim': [49.9833, 8.2667],
    'Hechtsheim': [49.9833, 8.2667],
    'Laubenheim': [49.9667, 8.2833],
    'Lerchenberg': [49.9833, 8.2333],
    'Oberstadt': [49.9833, 8.2667],
    'Weisenau': [49.9667, 8.2833]
}

# Load the data
@st.cache_data
def load_data():
    try:
        logging.info("Starting to load data...")
        
        # Load weather data first
        logging.info("Loading weather data...")
        weather = pd.read_csv('monthly_means_weather.csv')
        weather['date'] = pd.to_datetime(weather['month_year'], format='%B %Y')
        
        # Create a DataFrame for all stations with weather data
        stations = pd.DataFrame()
        
        # For each station, create a copy of the weather data
        for station_name, coords in station_coords.items():
            station_data = weather.copy()
            station_data['station_name'] = station_name
            station_data['latitude'] = coords[0]
            station_data['longitude'] = coords[1]
            stations = pd.concat([stations, station_data], ignore_index=True)
        
        # Load patient data
        logging.info("Loading patient data...")
        patients = pd.read_csv('monthly_patients_by_station.csv')
        patients['date'] = pd.to_datetime(patients['month_year'], format='%B %Y')
        
        # Extract station name from closest_station (remove 'Mainz/' prefix)
        patients['station_name'] = patients['closest_station'].str.replace('Mainz/', '')
        
        # Add coordinates to patient data
        patients['latitude'] = patients['station_name'].map(lambda x: station_coords.get(x, [None, None])[0])
        patients['longitude'] = patients['station_name'].map(lambda x: station_coords.get(x, [None, None])[1])
        
        # Load aircraft noise data
        logging.info("Loading aircraft noise data...")
        noise_files = glob.glob('monthly_means_*.csv')
        noise_files = [f for f in noise_files if f != 'monthly_means_weather.csv']
        
        noise_data = pd.DataFrame()
        for file in noise_files:
            try:
                df = pd.read_csv(file)
                # Extract base station name (remove any suffixes)
                station_name = file.replace('monthly_means_', '').replace('.csv', '')
                base_station = station_name.split('_')[0]  # Get the base station name
                
                if base_station in station_coords:
                    df['station_name'] = base_station
                    df['date'] = pd.to_datetime(df['month_year'], format='%B %Y')
                    df['latitude'] = station_coords[base_station][0]
                    df['longitude'] = station_coords[base_station][1]
                    noise_data = pd.concat([noise_data, df], ignore_index=True)
                else:
                    logging.warning(f"Skipping unknown station: {base_station}")
            except Exception as e:
                logging.error(f"Error processing file {file}: {str(e)}")
                continue
        
        logging.info("Data loading completed successfully")
        return stations, weather, patients, noise_data
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
def create_heatmap(data, data_type, frequency, selected_date):
    try:
        logging.info(f"Creating heatmap for {data_type} with {frequency} frequency for date {selected_date}")
        
        # Create a map centered at Mainz
        m = folium.Map(location=[49.9929, 8.2473], zoom_start=11)
        
        # Filter data based on selected date
        filtered_data = filter_data_by_date(data, selected_date, frequency)
        
        if filtered_data.empty:
            st.warning(f"No data available for {selected_date.strftime('%B %Y' if frequency == 'Monthly' else '%Y')}")
            return m
        
        # Add markers for each station
        for idx, row in filtered_data.drop_duplicates('station_name').iterrows():
            if data_type == 'Weather':
                value = row['TT_10']
                unit = '°C'
            elif data_type == 'Patients':
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
            if data_type == 'Weather':
                value = row['TT_10']
            elif data_type == 'Patients':
                value = row['patient_count']
            else:  # Aircraft Noise
                value = row['db_a']
            
            # Normalize the value for better visualization
            min_val = filtered_data['TT_10'].min() if data_type == 'Weather' else filtered_data['patient_count'].min() if data_type == 'Patients' else filtered_data['db_a'].min()
            max_val = filtered_data['TT_10'].max() if data_type == 'Weather' else filtered_data['patient_count'].max() if data_type == 'Patients' else filtered_data['db_a'].max()
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
        stations, weather, patients, noise_data = load_data()
        
        if stations is None or weather is None or patients is None or noise_data is None:
            st.error("Failed to load data. Please check the logs for more details.")
            return
        
        # Sidebar for options
        st.sidebar.header('Options')
        data_type = st.sidebar.selectbox('Select Data Type', ['Weather', 'Aircraft Noise', 'Patients'])
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
        if data_type == 'Weather':
            data = stations
        elif data_type == 'Aircraft Noise':
            data = noise_data
        else:
            data = patients
        
        # Create heatmap
        heatmap = create_heatmap(data, data_type, frequency, selected_date)
        
        # Display the map
        folium_static(heatmap)
        
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    main() 