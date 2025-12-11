import os

# Adjust path if needed to point to your data
file_path = "data/raw/era5/era5_pakistan_2016_04.nc"

print(f"File: {file_path}")

# 1. Check Size
size_bytes = os.path.getsize(file_path)
size_mb = size_bytes / (1024 * 1024)
print(f"Size: {size_mb:.2f} MB")

# 2. Check the "Magic Bytes" (The file signature)
try:
    with open(file_path, 'rb') as f:
        header = f.read(10)
        print(f"Header bytes: {header}")
        
        if b'CDF' in header or b'HDF' in header:
            print("✅ Format looks correct (NetCDF/HDF).")
        else:
            print("❌ INVALID FORMAT. This is likely a text file or empty.")
            # If it's text, print it to see the error
            f.seek(0)
            print("--- File Content Preview ---")
            print(f.read(200)) # Print first 200 characters
except Exception as e:
    print(f"Could not read file: {e}")