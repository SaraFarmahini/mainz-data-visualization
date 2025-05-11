import pandas as pd
import glob

# Get all monthly mean CSV files for stations
csv_files = glob.glob('monthly_means_*.csv')

# Exclude the weather file
csv_files = [f for f in csv_files if f != 'monthly_means_weather.csv']

# Initialize an empty DataFrame to hold the merged data
merged_data = pd.DataFrame()

for file in csv_files:
    # Read the CSV file
    df = pd.read_csv(file)
    
    # Extract station name from the file name
    station_name = file.replace('monthly_means_', '').replace('.csv', '')
    
    # Add a new column for station name
    df['station_name'] = station_name
    
    # Append to the merged DataFrame
    merged_data = pd.concat([merged_data, df], ignore_index=True)

# Save the merged data to a new CSV file
merged_data.to_csv('merged_station_means.csv', index=False)
print('Created merged_station_means.csv') 