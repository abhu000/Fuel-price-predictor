"""
Downloads the NSW FuelCheck monthly price history files into data/fuelcheck jan 2020-present/.

Run from the project folder:
    python download_fuelcheck.py

Files that are already downloaded are skipped, so if it stops halfway
(the NSW server is sometimes slow), just run it again.
"""
import os
import re
import requests

START_YEAR = 2020                      # study period starts January 2020 (FuelCheck history goes back to Aug 2016)
SAVE_DIR = os.path.join("data", "fuelcheck jan 2020-present")
API = "https://data.nsw.gov.au/data/api/3/action/package_show?id=fuel-check"

os.makedirs(SAVE_DIR, exist_ok=True)

# Ask the NSW data portal for the list of every file in the FuelCheck dataset
resources = requests.get(API, timeout=60).json()["result"]["resources"]
print("Files listed on the portal:", len(resources))

for r in resources:
    name, url = r["name"], r["url"]

    # Skip anything that isn't a monthly price file (website links, PDF/XML quality statements)
    if "price history" not in name.lower():
        continue

    # Pull the year out of the name, e.g. "FuelCheck Price History Apr 2025" -> 2025
    year = re.search(r"20\d\d", name)
    if year is None or int(year.group()) < START_YEAR:
        continue

    filename = os.path.join(SAVE_DIR, url.split("/")[-1])
    if os.path.exists(filename):
        continue

    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()            # stop if the server returned an error page
        with open(filename, "wb") as f:
            f.write(response.content)
        print("Downloaded:", name)
    except Exception as e:
        print("FAILED:", name, "->", e)

print("Done. Files in folder:", len(os.listdir(SAVE_DIR)))
