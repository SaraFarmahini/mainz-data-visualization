# Mainz Data Visualization

This Streamlit application visualizes the relationship between aircraft noise levels and patient data across different stations in Mainz, Germany.

## Features

- Interactive map showing patient counts and noise levels
- Time-based visualization with monthly data
- Heatmap representation of noise levels
- Circle markers for patient counts
- Detailed station-wise breakdown
- Comprehensive data summary

## Data Structure

The application uses the following data files:
- `monthly_means_weather.csv`: Weather data
- `monthly_patients_by_station.csv`: Patient data by station
- `monthly_means_*.csv`: Aircraft noise data for different stations

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run src/spatiotemporal_viz.py
```

## Deployment

This application is deployed on Streamlit Community Cloud. You can access it at: [Your Streamlit URL will appear here after deployment]

## Project Structure

```
.
├── data/                  # Data files
│   ├── monthly_means_*.csv    # Monthly means for each station
│   ├── monthly_patients_by_station.csv
│   └── monthly_means_weather.csv
├── src/                   # Source code
│   ├── streamlit_app.py   # Main Streamlit application
│   ├── run_network.py     # Script for local network access
│   └── run_public.py      # Script for public access (requires ngrok)
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore file
└── README.md             # This file
```

## Data Sources

- Weather data: Monthly mean temperatures
- Aircraft noise data: Monthly mean noise levels (dB)
- Patient data: Monthly patient counts by station

## Visualization Features

- Interactive map showing station locations
- Heatmap visualization of data
- Options to view different data types:
  - Weather
  - Aircraft Noise
  - Patient counts
- Time period selection:
  - Monthly view
  - Annual view

## License

[Add your license information here]

## Contact

[Add your contact information here] 