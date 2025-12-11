import os
import glob
import xarray as xr
import geopandas as gpd
import regionmask
import pandas as pd
import numpy as np
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
ERA5_DIR = "data/raw/era5"
SHAPEFILE_PATH = "data/raw/gadm/gadm41_PAK_3.shp"
OUTPUT_DIR = "data/interim"
os.makedirs(OUTPUT_DIR, exist_ok=True)

VAR_MAP = {
    't2m': 'temp_2m',       # Temperature
    'd2m': 'dew_point',     # Dewpoint
    'u10': 'wind_u',        # Wind Component
    'v10': 'wind_v',        # Wind Component
    'ssrd': 'solar_rad'     # Solar Radiation
}

def preprocess_era5():
    print(f"🗺️  Loading District Map from {SHAPEFILE_PATH}...")
    districts = gpd.read_file(SHAPEFILE_PATH)
    districts = districts.reset_index(drop=True)
    districts['district_id'] = districts.index 
    districts = districts[['district_id', 'NAME_3', 'geometry']]
    print(f"   ✅ Map Loaded. Found {len(districts)} districts.")
    
    nc_files = sorted(glob.glob(os.path.join(ERA5_DIR, "*.nc")))
    print(f"found {len(nc_files)} weather files to process.")

    all_data = []

    print("   🎭 Creating Spatial Mask...")
    first_ds = xr.open_dataset(nc_files[0], engine="netcdf4")
    mask = regionmask.mask_geopandas(
        districts, 
        first_ds.longitude, 
        first_ds.latitude, 
        numbers='district_id'
    )
    mask.name = 'region' 
    first_ds.close()

    for f in nc_files:
        filename = os.path.basename(f)
        print(f"   ⚡ Processing: {filename}...")
        
        try:
            ds = xr.open_dataset(f, engine="netcdf4")
            ds = ds.rename({k: v for k, v in VAR_MAP.items() if k in ds})
            
            ds_district = ds.groupby(mask).mean('stacked_latitude_longitude')
            df = ds_district.to_dataframe().reset_index()
            
            # --- FIX: Standardize Time Column Name ---
            if 'valid_time' in df.columns:
                df = df.rename(columns={'valid_time': 'time'})
            
            # Identify the ID column
            possible_id_cols = ['region', 'district_id', 'mask']
            id_col = next((c for c in possible_id_cols if c in df.columns), None)
            
            if id_col is None:
                print(f"       Could not find ID column. Available: {df.columns}")
                continue

            # Map Name
            district_mapper = districts.set_index('district_id')['NAME_3']
            df['district_name'] = df[id_col].map(district_mapper)
            
            # Cleanup
            df = df.dropna(subset=['district_name'])
            if id_col in df.columns:
                df = df.drop(columns=[id_col])
                
            cols = [c for c in df.columns if df[c].dtype == 'float64']
            df[cols] = df[cols].astype('float32')
            
            all_data.append(df)
            ds.close()
            
        except Exception as e:
            print(f"    Error processing {filename}: {e}")

    if not all_data:
        print(" No data processed! Check your inputs.")
        return

    print("\n🔗 Merging all months together...")
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Debug print to be sure
    print(f"   Columns available: {list(final_df.columns)}")
    
    # Sort
    final_df = final_df.sort_values(['time', 'district_name'])
    
    output_path = os.path.join(OUTPUT_DIR, "pakistan_district_climate_history.csv")
    final_df.to_csv(output_path, index=False)
    
    print(f"🎉 SUCCESS! Master Dataset saved to: {output_path}")
    print(f"   Rows: {len(final_df)}")

if __name__ == "__main__":
    preprocess_era5()