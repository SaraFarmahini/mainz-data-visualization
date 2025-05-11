import pandas as pd

# Read Weather.csv with the correct delimiter
weather = pd.read_csv('Weather.csv', delimiter=';')

# Parse the date column
weather['MESS_DATUM'] = pd.to_datetime(weather['MESS_DATUM'])

# Extract month and year
weather['month_year'] = weather['MESS_DATUM'].dt.strftime('%B %Y')

# Group by month_year and calculate mean of TT_10
monthly_means = weather.groupby('month_year')['TT_10'].mean().reset_index()

# Sort by date
monthly_means['sort_date'] = pd.to_datetime(monthly_means['month_year'], format='%B %Y')
monthly_means = monthly_means.sort_values('sort_date')
monthly_means = monthly_means.drop('sort_date', axis=1)

# Save to new CSV file
monthly_means.to_csv('monthly_means_weather.csv', index=False)
print('Created monthly_means_weather.csv') 