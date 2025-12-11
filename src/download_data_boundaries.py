import os
import requests
import zipfile
import io

# --- CONFIGURATION ---
GEO_DIR = "data/raw/geospatial"
os.makedirs(GEO_DIR, exist_ok=True)

# 1. GADM (District Boundaries)
# Direct link to GADM v4.1 Shapefiles for Pakistan
GADM_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_PAK_shp.zip"

# 2. WorldPop (Population Count)
# 2020 Population Count (1km resolution) - Perfect for district aggregation
WPOP_URL = "https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/PAK/pak_ppp_2020_1km_Ascii_XYZ.zip"

def download_and_extract(url, target_folder, name):
    print(f"⬇️  Downloading {name}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Unzip directly from memory
        print(f"📦 Extracting {name}...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(target_folder)
        print(f"✅ {name} saved to {target_folder}")
        
    except Exception as e:
        print(f"❌ Error downloading {name}: {e}")

print(f"🚀 Starting Static Data Download to: {os.path.abspath(GEO_DIR)}\n")

# --- EXECUTE ---
download_and_extract(GADM_URL, os.path.join(GEO_DIR, "gadm_pakistan"), "GADM Shapefiles")
download_and_extract(WPOP_URL, os.path.join(GEO_DIR, "worldpop_pakistan"), "WorldPop Data")

print("\n🎉 Static datasets acquired! You are ready for Preprocessing.")