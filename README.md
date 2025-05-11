# Mainz Data Visualization

This project visualizes various data types (weather, aircraft noise, and patient data) for different stations in Mainz, Germany.

## Data Description

The project uses three types of data:
1. Weather data (monthly means)
2. Aircraft noise data (monthly means)
3. Patient data (monthly counts by station)

## Setup Instructions

1. Clone the repository:
```bash
git clone <your-repository-url>
cd <repository-name>
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

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