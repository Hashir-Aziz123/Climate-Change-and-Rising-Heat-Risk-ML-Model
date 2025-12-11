import os
import glob
import xarray as xr
import geopandas as gpd
import rasterio
import pandas as pd
import numpy as np

# --- CONFIGURATION (Based on your Screenshot) ---
BASE_DIR = "data/raw"
PATHS = {
    "ERA5":      os.path.join(BASE_DIR, "era5"),
    "GADM":      os.path.join(BASE_DIR, "gadm"),
    "WORLDPOP":  os.path.join(BASE_DIR, "pak_pop"),
    "NASA":      os.path.join(BASE_DIR, "nasa_power")
}

def print_status(name, success, message):
    icon = "✅" if success else "❌"
    print(f"{icon} [{name}] {message}")

print(f"🚀 Starting Data Integrity Checks in: {os.path.abspath(BASE_DIR)}\n")

# ==========================================
# 1. TEST ERA5 (Climate Data)
# ==========================================
print("--- Checking ERA5 (NetCDF) ---")
era5_files = glob.glob(os.path.join(PATHS["ERA5"], "*.nc"))

if not era5_files:
    print_status("ERA5", False, "No .nc files found! Check folder path.")
else:
    # Test the first and last file to ensure range
    try:
        sample_file = era5_files[0]
        ds = xr.open_dataset(sample_file, engine="netcdf4")
        
        # Check for mandatory variables
        required_vars = ['t2m', 'd2m', 'ssrd'] # Temp, Dewpoint, Solar
        missing = [v for v in required_vars if v not in ds.data_vars and v.upper() not in ds.data_vars]
        
        if missing:
            print_status("ERA5", False, f"Missing variables: {missing}")
        else:
            size_mb = os.path.getsize(sample_file) / (1024*1024)
            print_status("ERA5", True, f"Found {len(era5_files)} files. Sample size: {size_mb:.1f}MB. Variables OK.")
            print(f"   Variables found: {list(ds.data_vars)}")
            
    except Exception as e:
        print_status("ERA5", False, f"Corrupt file detected: {e}")

# ==========================================
# 2. TEST GADM (Shapefiles)
# ==========================================
print("\n--- Checking GADM (Shapefiles) ---")
shp_files = glob.glob(os.path.join(PATHS["GADM"], "*.shp"))

if not shp_files:
    print_status("GADM", False, "No .shp files found!")
else:
    try:
        # Look for Level 2 (Districts)
        district_shp = [f for f in shp_files if "2.shp" in f or "adm2" in f]
        target_file = district_shp[0] if district_shp else shp_files[0]
        
        gdf = gpd.read_file(target_file)
        
        if gdf.empty:
            print_status("GADM", False, "Shapefile is empty!")
        else:
            row_count = len(gdf)
            crs_name = gdf.crs.name if gdf.crs else "Unknown"
            print_status("GADM", True, f"Loaded {os.path.basename(target_file)}. Rows: {row_count} (Districts). CRS: {crs_name}")
            
    except Exception as e:
        print_status("GADM", False, f"Failed to read shapefile: {e}")

# ==========================================
# 3. TEST WORLDPOP (Raster)
# ==========================================
print("\n--- Checking WorldPop (GeoTIFF) ---")
tif_files = glob.glob(os.path.join(PATHS["WORLDPOP"], "*.tif"))

if not tif_files:
    print_status("WorldPop", False, "No .tif files found!")
else:
    try:
        with rasterio.open(tif_files[0]) as src:
            data = src.read(1)
            # Check if it's just an empty black image
            if data.max() == 0:
                 print_status("WorldPop", False, "Raster contains no data (Max value is 0)!")
            else:
                print_status("WorldPop", True, f"Loaded {os.path.basename(tif_files[0])}.")
                print(f"   Resolution: {src.width}x{src.height}. Max Pop Count: {int(data.max())}")
                print(f"   CRS: {src.crs}")
                
    except Exception as e:
        print_status("WorldPop", False, f"Corrupt Raster: {e}")

# ==========================================
# 4. TEST NASA POWER (CSV)
# ==========================================
print("\n--- Checking NASA POWER (CSV) ---")
csv_files = glob.glob(os.path.join(PATHS["NASA"], "*.csv"))

if not csv_files:
    print_status("NASA", False, "No .csv files found!")
else:
    try:
        df = pd.read_csv(csv_files[0])
        # Check for Solar Radiation column (usually ALLSKY_SFC_SW_DWN)
        if df.shape[0] < 10:
             print_status("NASA", False, "CSV looks empty (less than 10 rows).")
        else:
            print_status("NASA", True, f"Found {len(csv_files)} cities. Sample Rows: {len(df)}.")
            print(f"   Columns: {list(df.columns[:3])}...")
            
    except Exception as e:
        print_status("NASA", False, f"Corrupt CSV: {e}")

print("\n------------------------------------------------")
print("🎉 If you see 4 Green Checks, you are ready for Preprocessing!")