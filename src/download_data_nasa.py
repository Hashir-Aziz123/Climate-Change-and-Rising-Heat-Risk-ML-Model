import requests
import pandas as pd
import os
import time

# --- CONFIGURATION ---
OUTPUT_FOLDER = "data/raw/nasa_power"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 1. The Variables we want (Solar + Humidity + Temp for validation)
# ALLSKY_SFC_SW_DWN = Solar Irradiance (The key missing piece for WBGT)
# RH2M = Relative Humidity at 2 meters
# T2M = Temperature at 2 meters
PARAMETERS = "ALLSKY_SFC_SW_DWN,RH2M,T2M"

# 2. The Time Range (Matches our ERA5 data)
START_DATE = "20150401" # April 1st, 2015
END_DATE = "20240930"   # Sept 30th, 2024

# 3. The Locations (Lat/Lon)
LOCATIONS = {
    "Jacobabad": {"lat": 28.2833, "lon": 68.4333},
    "Sibbi":     {"lat": 29.5442, "lon": 67.8764},
    "Lahore":    {"lat": 31.5204, "lon": 74.3587},
    "Karachi":   {"lat": 24.8607, "lon": 67.0011},
    "Multan":    {"lat": 30.1575, "lon": 71.5249}
}

BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

print(f"🚀 Starting NASA POWER Download for Validation Cities...")

for city, coords in LOCATIONS.items():
    print(f"🌍 Fetching data for {city}...")
    
    # Construct the API Request
    params = {
        "parameters": PARAMETERS,
        "community": "AG", # Agroclimatology (Good for surface data)
        "longitude": coords["lon"],
        "latitude": coords["lat"],
        "start": START_DATE,
        "end": END_DATE,
        "format": "JSON"
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        # Parse the nested JSON response
        # NASA returns data like: data['properties']['parameter']['T2M']['20150401'] = 30.5
        features = data['properties']['parameter']
        
        # Convert to DataFrame
        df = pd.DataFrame(features)
        df.index.name = 'Date'
        df.reset_index(inplace=True)
        
        # Save to CSV
        filename = f"{OUTPUT_FOLDER}/nasa_{city}.csv"
        df.to_csv(filename, index=False)
        print(f"   ✅ Saved {filename}")
        
    except Exception as e:
        print(f"   ❌ Error for {city}: {e}")
    
    # Be nice to the API
    time.sleep(2)

print("\n🎉 NASA Validation Data Downloaded!")