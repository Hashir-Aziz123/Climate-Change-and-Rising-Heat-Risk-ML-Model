import geopandas as gpd
import pandas as pd
import json
import os

# --- PATHS ---
GEOJSON_PATH = "app/data/pakistan_districts.geojson"
CSV_PATH = "app/data/app_baseline.csv"

print("🤝 STARTING DATA HANDSHAKE...")

# 1. Load Data
gdf = gpd.read_file(GEOJSON_PATH)
df = pd.read_csv(CSV_PATH)

# 2. Get Unique Names
geo_names = set(gdf['district_name'].unique())
csv_names = set(df['district_name'].unique())

# 3. Find Mismatches
# We only care about names in the CSV (Data) that are missing from the Map (GeoJSON)
missing_in_map = csv_names - geo_names
missing_in_data = geo_names - csv_names

print(f"   CSV Districts: {len(csv_names)}")
print(f"   Map Districts: {len(geo_names)}")

if not missing_in_map and not missing_in_data:
    print("✅ PERFECT MATCH! No fixes needed.")
else:
    print(f"⚠️ Mismatch Detected!")
    print(f"   In Data but not Map: {missing_in_map}")
    print(f"   In Map but not Data: {missing_in_data}")
    
    # 4. AUTO-FIX (The Magic)
    # We strip whitespace and Title Case both sides
    print("🔧 Applying Standardization Patch...")
    gdf['district_name'] = gdf['district_name'].str.strip().str.title()
    
    # Force specific overrides if "Karachi west" exists
    patch = {"Karachi west": "Karachi West", "Gujarat": "Gujrat"}
    gdf['district_name'] = gdf['district_name'].replace(patch)
    
    # Re-check
    geo_names_fixed = set(gdf['district_name'].unique())
    still_missing = csv_names - geo_names_fixed
    
    if still_missing:
        print(f"❌ CRITICAL: Still missing: {still_missing}")
        print("   (You might need to manually add these to the patch dict in this script)")
    else:
        print("✅ FIX SUCCESSFUL. Saving corrected Map...")
        gdf.to_file(GEOJSON_PATH, driver="GeoJSON")
        print("🎉 Ready for App Development.")