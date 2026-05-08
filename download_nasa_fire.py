import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta

MAP_KEY = "34a958cedc81272c35ba318660ea77b4"

# India bounding box: west, south, east, north
INDIA_BBOX = "68.1,8.4,97.4,37.6"

# We want October + November 2023 (peak stubble burning)
# API allows max 5 days per request — so we request in 5-day chunks

def get_dates(start_str, end_str):
    """Generate list of start dates in 5-day chunks"""
    start = datetime.strptime(start_str, "%Y-%m-%d")
    end   = datetime.strptime(end_str,   "%Y-%m-%d")
    dates = []
    current = start
    while current < end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=5)
    return dates

dates = get_dates("2023-10-01", "2023-11-30")

print(f"Downloading NASA FIRMS MODIS_SP fire data for India")
print(f"Period: October–November 2023 ({len(dates)} requests)")
print(f"Bounding box: India ({INDIA_BBOX})")
print()

all_dfs = []

for i, date in enumerate(dates):
    url = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
        f"{MAP_KEY}/MODIS_SP/{INDIA_BBOX}/5/{date}"
    )
    r = requests.get(url)
    if r.status_code == 200 and "latitude" in r.text.lower():
        lines = r.text.strip().split("\n")
        if len(lines) > 1:
            from io import StringIO
            df_chunk = pd.read_csv(StringIO(r.text))
            all_dfs.append(df_chunk)
            print(f"  [{i+1}/{len(dates)}] {date} → {len(df_chunk)} detections")
        else:
            print(f"  [{i+1}/{len(dates)}] {date} → 0 detections")
    else:
        print(f"  [{i+1}/{len(dates)}] {date} → Error: {r.text[:100]}")
    time.sleep(0.5)  # be polite to NASA servers

if all_dfs:
    df_final = pd.concat(all_dfs, ignore_index=True)
    df_final = df_final.drop_duplicates()
    os.makedirs("data", exist_ok=True)
    df_final.to_csv("data/india_fire_2023.csv", index=False)
    print(f"\n✓ SUCCESS!")
    print(f"  Total fire detections: {len(df_final)}")
    print(f"  Saved to: data/india_fire_2023.csv")
    print(f"\nColumns: {list(df_final.columns)}")
    print(f"\nSample row:")
    print(df_final.iloc[0])
else:
    print("\nNo data downloaded.")