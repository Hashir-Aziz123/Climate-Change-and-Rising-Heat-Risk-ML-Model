import geopandas as gpd
import pandas as pd
import os

# --- CONFIGURATION ---
SHAPEFILE_PATH = "data/raw/gadm/gadm41_PAK_3.shp"
TRAINING_DATA_PATH = "data/processed/final_training_data.csv"
APP_DATA_DIR = "app/data"
# Create app data folder
os.makedirs(APP_DATA_DIR, exist_ok=True)
print("  PREPARING MAP & COORDINATES...")

# 1. Load & Simplify
gdf = gpd.read_file(SHAPEFILE_PATH)
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)
gdf = gdf[['NAME_3', 'geometry']].rename(columns={'NAME_3': 'district_name'})

# 2. Clean Names
name_corrections = {
    "Jakobabad": "Jacobabad", "Attok": "Attock", "Mirphurkhas": "Mirpur Khas",
    "Dera Ghazi Kha": "Dera Ghazi Khan", "M. B. Din": "Mandi Bahauddin",
    "Tando M. Khan": "Tando Muhammad Khan", "Gujarat": "Gujrat", "Karachi west": "Karachi West", 
    "Gujranwala 1": "Gujranwala", "Gujranwala 2": "Gujranwala",
    "Narowal 1": "Narowal", "Narowal 2": "Narowal", "Okara 1": "Okara",
    "Malakand P.A.": "Malakand", "N. Waziristan": "North Waziristan",
    "S. Waziristan": "South Waziristan", "Adam Khel": "Kohat",
    "Bhitani": "Lakki Marwat", "Largha Shirani": "Sherani"
}

gdf['district_name'] = gdf['district_name'].replace(name_corrections).str.strip().str.title()
gdf = gdf.dissolve(by='district_name', as_index=False)

# 3. [NEW] Extract Centroids for API Calls (Tab 2)
# We need Lat/Lon to ask Open-Meteo: "What is the weather in Lahore?"
# Centroids give us the center point of the shape.
print("   Extracting district centroids (Lat/Lon)...")
# Calculate centroids on the geometry
centroids = gdf.geometry.centroid
gdf['lat'] = centroids.y
gdf['lon'] = centroids.x

# Save Coordinates Lookup File
coords_path = os.path.join(APP_DATA_DIR, "district_coords.csv")
gdf[['district_name', 'lat', 'lon']].to_csv(coords_path, index=False)
print(f"    Coordinates saved to {coords_path}")

# 4. Save Map (GeoJSON)
geojson_path = os.path.join(APP_DATA_DIR, "pakistan_districts.geojson")
gdf.to_file(geojson_path, driver="GeoJSON")
print(f"    Map saved to {geojson_path}")


# ==========================================
# PART 2: CLIMATE DATA (Baseline & History)
# ==========================================
print("\n PREPARING APP DATASETS...")

df = pd.read_csv(TRAINING_DATA_PATH)
df['time'] = pd.to_datetime(df['time'])

# 1. Baseline Data (For Tab 1: Simulation)
print("   Creating Seasonal Baseline (2023)...")
baseline_df = df[df['time'].dt.year == 2023].copy()
baseline_df['month'] = baseline_df['time'].dt.month

app_baseline = baseline_df.groupby(['district_name', 'month'])[
    ['population_2020', 'pop_log', 'temp_c', 'humidity_relative', 
     'wind_speed_m_s', 'solar_w_m2', 'temp_roll_24h', 'hi_max_72h']
].mean().reset_index()

baseline_path = os.path.join(APP_DATA_DIR, "app_baseline.csv")
app_baseline.to_csv(baseline_path, index=False)
print(f"Baseline saved to {baseline_path}")

# 2. [NEW] Historical Slice (For Tab 3: Animation)
# We extract the famous June 2015 Heatwave (June 15 - June 30)
# This keeps the file size small/fast for the app.
print("   Creating Historical Slice (June 2015 Heatwave)...")
start_date = "2015-06-15"
end_date = "2015-06-30"

history_df = df[
    (df['time'] >= start_date) & 
    (df['time'] <= end_date)
].copy()

# Keep only necessary columns for the animation
# We need 'risk_lag_1h' here because the animation runs the model prediction live!
history_cols = [
    'time', 'district_name', 'population_2020', 'pop_log',
    'temp_c', 'humidity_relative', 'wind_speed_m_s', 'solar_w_m2',
    'temp_roll_24h', 'hi_max_72h', 'risk_lag_1h'
]
app_history = history_df[history_cols].copy()

# Format time as string for the slider (YYYY-MM-DD HH:00)
app_history['time_str'] = app_history['time'].dt.strftime('%Y-%m-%d %H:00')

history_path = os.path.join(APP_DATA_DIR, "app_history_2015.csv")
app_history.to_csv(history_path, index=False)
print(f"   History slice saved to {history_path} ({len(app_history)} rows)")

print("\n All App Data Ready! Proceed to streamlit_app.py")