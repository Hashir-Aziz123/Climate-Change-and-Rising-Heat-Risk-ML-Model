import geopandas as gpd
import rioxarray
import pandas as pd
import os
from rasterio.enums import Resampling

# --- CONFIGURATION ---
SHAPEFILE_PATH = "data/raw/gadm/gadm41_PAK_3.shp"
POP_RASTER_PATH = "data/raw/pak_pop/pak_ppp_2020_1km_Aggregated_UNadj.tif"
OUTPUT_DIR = "data/processed"

# 1. Define the Standard Name Dictionary
# This MUST match the cleaning you did in Notebook 02
name_corrections = {
    # Fix Typos
    "Jakobabad": "Jacobabad",
    "Attok": "Attock",
    "Mirphurkhas": "Mirpur Khas",
    "Dera Ghazi Kha": "Dera Ghazi Khan",
    "M. B. Din": "Mandi Bahauddin",
    "Tando M. Khan": "Tando Muhammad Khan",
    "Gujarat": "Gujrat", # Fix the duplicate/typo found in your list
    
    # Merge Split Districts
    "Gujranwala 1": "Gujranwala",
    "Gujranwala 2": "Gujranwala",
    "Narowal 1": "Narowal",
    "Narowal 2": "Narowal",
    "Okara 1": "Okara",
    
    # Standardize Tribal/Special Areas
    "Malakand P.A.": "Malakand",
    "N. Waziristan": "North Waziristan",
    "S. Waziristan": "South Waziristan",
    "Adam Khel": "Kohat",
    "Bhitani": "Lakki Marwat",
    "Largha Shirani": "Sherani"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"  Loading District Map from {SHAPEFILE_PATH}...")
gdf = gpd.read_file(SHAPEFILE_PATH)

# 2. Apply Name Standardization
print("🧹 Cleaning District Names...")
gdf['district_name'] = gdf['NAME_3'].replace(name_corrections)

# --- NEW FIX: Force Title Case ---
# This fixes "Karachi west" -> "Karachi West" to match GADM
gdf['district_name'] = gdf['district_name'].str.title() 

# 3. DISSOLVE: Merge shapes (e.g., Gujarat + Gujrat -> Gujrat)
print("🔗 Merging split geometries (Dissolving)...")
gdf = gdf.dissolve(by='district_name', as_index=False)

print(f"   Loaded and merged. Final Unique Districts: {len(gdf)}")

print("\n Loading Population Data (WorldPop)...")
try:
    pop_raster = rioxarray.open_rasterio(POP_RASTER_PATH, masked=True).squeeze()
except Exception as e:
    print(f" Error loading WorldPop: {e}")
    exit()

if gdf.crs != pop_raster.rio.crs:
    print("    Re-projecting Map to match Raster...")
    gdf = gdf.to_crs(pop_raster.rio.crs)

print("\n Calculating Population per District (Zonal Stats)...")
district_populations = []

for index, row in gdf.iterrows():
    try:
        clipped_raster = pop_raster.rio.clip([row['geometry']], gdf.crs, drop=True)
        total_pop = clipped_raster.sum().item()
        if total_pop is None or total_pop < 0: total_pop = 0
        district_populations.append(total_pop)
    except Exception:
        district_populations.append(0)

gdf['population_2020'] = district_populations
gdf['population_2020'] = gdf['population_2020'].astype(int)

# Sort for sanity check
gdf = gdf.sort_values(by='population_2020', ascending=False)

print("\n Saving Metadata...")
csv_path = os.path.join(OUTPUT_DIR, "district_metadata.csv")

# Save only the clean columns we need
gdf[['district_name', 'population_2020']].to_csv(csv_path, index=False)
print(f"    Saved: {csv_path}")

print("\n Top 5 Most Populous Districts (Cleaned):")
print(gdf[['district_name', 'population_2020']].head(5))