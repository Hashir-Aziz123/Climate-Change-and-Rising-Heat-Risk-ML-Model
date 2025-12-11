import geopandas as gpd
import pandas as pd
import os

# --- CONFIGURATION ---
SHAPEFILE_PATH = "data/raw/gadm/gadm41_PAK_3.shp"
TRAINING_DATA_PATH = "data/processed/final_training_data.csv"
APP_DATA_DIR = "app/data"
# Create app data folder
os.makedirs(APP_DATA_DIR, exist_ok=True)

print("  PREPARING MAP DATA...")
# ... [This Map part stays exactly the same as before] ...
gdf = gpd.read_file(SHAPEFILE_PATH)
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)
gdf = gdf[['NAME_3', 'geometry']].rename(columns={'NAME_3': 'district_name'})

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
gdf.to_file(os.path.join(APP_DATA_DIR, "pakistan_districts.geojson"), driver="GeoJSON")
print(" Map saved.")

# --- THE UPGRADE: MULTI-MONTH BASELINE ---
print("\n PREPARING SEASONAL BASELINE CLIMATE DATA...")

df = pd.read_csv(TRAINING_DATA_PATH)
df['time'] = pd.to_datetime(df['time'])

# Filter for the most recent full year (2023)
# We want to capture the "Seasonal Cycle"
baseline_df = df[df['time'].dt.year == 2023].copy()
baseline_df['month'] = baseline_df['time'].dt.month

# Group by District AND Month
print("   Aggregating 12 months of data...")
app_df = baseline_df.groupby(['district_name', 'month'])[
    ['population_2020', 'pop_log', 'temp_c', 'humidity_relative', 'wind_speed_m_s', 'solar_w_m2', 'temp_roll_24h', 'hi_max_72h']
].mean().reset_index()

# Save
baseline_path = os.path.join(APP_DATA_DIR, "app_baseline.csv")
app_df.to_csv(baseline_path, index=False)
print(f" Seasonal Data saved to {baseline_path} ({len(app_df)} rows)")
print("   Now contains data for Jan, Feb... Dec for all districts.")