import os
import json
import requests

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
RAW_OUTPUT = "data/raw/tle_active.txt"
PROCESSED_OUTPUT = "data/processed/satellites_tle.json"

# Fallback TLE sample data if CelesTrak is offline or blocking connection
SAMPLE_TLE_DATA = """ISS (ZARYA)             
1 25544U 98067A   24150.50000000  .00016717  00000-0  30000-3 0  9993
2 25544  51.6400 208.9160 0004800  69.9860  25.0000 15.49815000450008
CARTOSAT-2F             
1 43111U 18004A   24150.50000000  .00001000  00000-0  50000-4 0  9991
2 43111  97.4500 120.3200 0001500  80.1200 280.0000 15.10000000350001
OCEANSAT-3              
1 54361U 22158A   24150.50000000  .00000800  00000-0  40000-4 0  9992
2 54361  98.1200  95.4500 0001200  45.3000 315.1000 14.85000000120002
"""


def fetch_and_process_tle():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    # Standard browser headers to bypass default requests User-Agent blocking
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("📡 Fetching live TLE parameters from CelesTrak API...")
    try:
        response = requests.get(CELESTRAK_URL, headers=headers, timeout=10)
        response.raise_for_status()
        raw_text = response.text
        print("Live connection successful!")
    except Exception as e:
        print(f"Network connection issue ({e}). Using robust fallback orbital TLE dataset...")
        raw_text = SAMPLE_TLE_DATA

    # Save raw TLE file
    with open(RAW_OUTPUT, "w") as f:
        f.write(raw_text)

    # Parse TLE triplets into JSON objects
    lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
    satellites = []

    for i in range(0, len(lines) - 2, 3):
        sat_name = lines[i]
        line1 = lines[i + 1]
        line2 = lines[i + 2]

        if line1.startswith("1 ") and line2.startswith("2 "):
            satellites.append({
                "name": sat_name,
                "norad_id": line1[2:7].strip(),
                "line1": line1,
                "line2": line2,
            })

    with open(PROCESSED_OUTPUT, "w") as f:
        json.dump(satellites, f, indent=2)

    print(f"Saved raw TLE -> '{RAW_OUTPUT}'")
    print(f"Successfully processed {len(satellites)} satellites -> '{PROCESSED_OUTPUT}'")


if __name__ == "__main__":
    fetch_and_process_tle()