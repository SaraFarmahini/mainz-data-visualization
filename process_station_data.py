import pandas as pd
import glob
import os

# Get all CSV files in the current directory
csv_files = glob.glob('*.csv')

# Exclude specific files
exclude_files = ['patients.csv', 'monthly_patients_by_station.csv', 'process_patients.py', 'process_station_data.py']
csv_files = [f for f in csv_files if f not in exclude_files]

for file in csv_files:
    # Read the CSV file
    df = pd.read_csv(file)
    
    # Use 'datetime' if available, otherwise use 'date'
    if 'datetime' in df.columns:
        date_col = 'datetime'
    elif 'date' in df.columns:
        date_col = 'date'
    else:
        print(f"No date column found in {file}, skipping.")
        continue
    
    # Check for db_a column
    if 'db_a' not in df.columns:
        print(f"No db_a column found in {file}, skipping.")
        continue
    
    # Convert the date column to datetime format
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Extract month and year
    df['month_year'] = df[date_col].dt.strftime('%B %Y')
    
    # Group by month_year and calculate mean of db_a
    monthly_means = df.groupby('month_year')['db_a'].mean().reset_index()
    
    # Sort by date
    monthly_means['sort_date'] = pd.to_datetime(monthly_means['month_year'], format='%B %Y')
    monthly_means = monthly_means.sort_values('sort_date')
    monthly_means = monthly_means.drop('sort_date', axis=1)
    
    # Get station name from the original file name
    station_name = os.path.splitext(file)[0]
    
    # Save to new CSV file
    output_file = f'monthly_means_{station_name}.csv'
    monthly_means.to_csv(output_file, index=False)
    print(f'Created {output_file}') 