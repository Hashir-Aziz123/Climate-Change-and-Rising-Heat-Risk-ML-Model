import os
import zipfile
import shutil

# Path to your data (Use the relative path since you have the symlink)
DATA_DIR = "data/raw/era5"

print(f"🔧 Starting repair in: {os.path.abspath(DATA_DIR)}")

# Get list of all .nc files
files = [f for f in os.listdir(DATA_DIR) if f.endswith('.nc')]

for filename in files:
    file_path = os.path.join(DATA_DIR, filename)
    
    # 1. Check if it's actually a zip file
    try:
        if not zipfile.is_zipfile(file_path):
            print(f"✅ {filename} is already a valid NetCDF (skipped).")
            continue
    except Exception:
        continue # Skip if permission errors etc.

    print(f"📦 Unzipping: {filename}...")
    
    # 2. Rename .nc -> .zip so we can extract it
    zip_name = file_path.replace(".nc", ".zip")
    try:
        os.rename(file_path, zip_name)
    except OSError as e:
        print(f"   ❌ Could not rename {filename}: {e}")
        continue

    # 3. Extract contents
    try:
        with zipfile.ZipFile(zip_name, 'r') as zip_ref:
            # Usually contains 'data_0.nc' or similar
            inner_files = zip_ref.namelist()
            target_file = inner_files[0] # Take the first file found
            zip_ref.extract(target_file, DATA_DIR)
        
        # 4. Rename the extracted file (e.g., data_0.nc) to the proper name (era5_pakistan_2016_04.nc)
        extracted_path = os.path.join(DATA_DIR, target_file)
        
        # Remove the original zip to keep it clean
        os.remove(zip_name)
        
        # Rename extracted file to original name
        os.rename(extracted_path, file_path)
        
        print(f"   ✨ Fixed! {target_file} -> {filename}")

    except Exception as e:
        print(f"   ❌ Failed to unzip {zip_name}: {e}")
        # Attempt to restore name if failed
        if os.path.exists(zip_name):
            os.rename(zip_name, file_path)

print("\n🎉 All files processed. Try running your check script again!")