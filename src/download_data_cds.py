import cdsapi
import os

# --- CONFIGURATION ---
OUTPUT_FOLDER = "data/raw/era5"
START_YEAR = 2015
END_YEAR = 2024
# Only download the heat season months
MONTHS = ['04', '05', '06', '07', '08', '09'] 

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize Client
c = cdsapi.Client(
    url="https://cds.climate.copernicus.eu/api",
    key="a13dbcfa-d696-41f6-a53e-ea04006336b5"
)

print(f"Starting granular download for years: {START_YEAR}-{END_YEAR}")
print(f"Saving to: {os.path.abspath(OUTPUT_FOLDER)}\n")

for year in range(START_YEAR, END_YEAR + 1):
    for month in MONTHS:
        # Create a filename like: era5_pakistan_2015_04.nc
        filename = f"era5_pakistan_{year}_{month}.nc"
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        
        if os.path.exists(filepath):
            print(f"✅ Found {filename}, skipping...")
            continue

        print(f"⬇️  Requesting {year}-{month}...")
        
        try:
            c.retrieve(
                'reanalysis-era5-land',
                {
                    'format': 'netcdf',
                    'variable': [
                        '2m_temperature',
                        '2m_dewpoint_temperature',
                        'total_precipitation',
                        '10m_u_component_of_wind',
                        '10m_v_component_of_wind',
                        'surface_solar_radiation_downwards',
                    ],
                    'year': str(year),
                    'month': month,
                    # Retrieve all days in the month
                    'day': [
                        '01', '02', '03', '04', '05', '06',
                        '07', '08', '09', '10', '11', '12',
                        '13', '14', '15', '16', '17', '18',
                        '19', '20', '21', '22', '23', '24',
                        '25', '26', '27', '28', '29', '30', '31',
                    ],
                    'time': [
                        '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
                        '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
                        '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
                        '18:00', '19:00', '20:00', '21:00', '22:00', '23:00',
                    ],
                    'area': [
                        37.5, 60.5, 23.5, 77.5, # Pakistan Bounding Box
                    ],
                },
                filepath
            )
            print(f"   --> Saved {filename}")
            
        except Exception as e:
            print(f"❌ Error on {year}-{month}: {e}")

print("\n🎉 All downloads complete!")