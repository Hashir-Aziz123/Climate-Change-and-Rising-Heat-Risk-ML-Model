import os
import xarray as xr

# Relative path (Best Practice)
data_path = "data/raw/era5"

print(f"📂 Checking {os.path.abspath(data_path)}...")

files = [f for f in os.listdir(data_path) if f.endswith('.nc')]
print(f"✅ Found {len(files)} NetCDF files!")

if len(files) > 0:
    # Test opening the first file
    first_file = os.path.join(data_path, files[0])
    print(f"📖 Reading header of: {files[0]}...")
    
    ds = xr.open_dataset(first_file)
    print("\n--- DATA VARIABLES ---")
    print(ds.data_vars)
    print("----------------------")
    print("🎉 SUCCESS: Your local Python is reading directly from Google Drive!")