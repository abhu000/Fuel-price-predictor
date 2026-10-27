# Data

All files in this folder are raw downloads, unchanged from the source, except `blacktown_u91_price_changes.csv` (created by the notebook, see below). All cleaning happens inside `fuel_price_predictor.ipynb`.

## Files

### `AIP_Terminal_gate_prices_Data_09-Oct-2026.xlsx`
- **Source:** Australian Institute of Petroleum, *Historical ULP and Diesel TGP Data* — https://www.aip.com.au/resources/historical-ulp-and-diesel-tgp-data
- **Downloaded:** 11 October 2026 (data up to 9 October 2026)
- **Contents:** daily average terminal gate prices (wholesale) for petrol and diesel in each capital city, cents per litre **including GST and excise**, from 2004.
- **Used:** sheet `Petrol TGP`, column `Sydney` only.
- **Notes:** business days only (no weekends or public holidays).

### `exchange_rate_2014-2017.xls`, `exchange_rate_2018-2022.xls`, `exchange_rate_2023-current.xls`
- **Source:** Reserve Bank of Australia, statistical table F11.1 *Exchange Rates – Daily* — https://www.rba.gov.au/statistics/historical-data.html
- **Downloaded:** 11 October 2026 (data up to 9 October 2026)
- **Contents:** daily exchange rates of the Australian dollar against 20+ currencies. The first 11 rows of each file are header information.
- **Used:** column `A$1=USD` (series ID FXRUSD) only.
- **Notes:** business days only. One missing value (25 May 2015) falls outside the study period.

### `DCOILBRENTEU.csv`
- **Source:** Federal Reserve Bank of St. Louis (FRED), *Crude Oil Prices: Brent – Europe* — https://fred.stlouisfed.org/series/DCOILBRENTEU (original source: U.S. Energy Information Administration)
- **Downloaded:** 11 October 2026 (data up to 6 October 2026)
- **Contents:** daily Brent crude price in US dollars per barrel, from May 1987.
- **Notes:** blank values are days the oil market was closed (holidays).

### `fuelcheck jan 2020-present/` (not stored on GitHub)
- **Source:** NSW Government, *FuelCheck* price history — https://data.nsw.gov.au/data/dataset/fuel-check
- **Contents:** one file per month (Excel or CSV) from August 2016. Each row is one station changing the price of one fuel type.
- **Used:** January 2020 – August 2026; stations in the suburb Blacktown (postcode 2148), fuel code `U91`.
- **How to get it:** run `python download_fuelcheck.py` from the project folder. The files total several hundred MB, so they aren't uploaded to this repository.
- **Formats:** files from 2020–2023 (`price_history_checks_…`) have two title rows, merged (blank) station cells, and text dates like `1/04/2021 12:10:33 AM`. Files from 2024 onwards (`fuelcheck_pricehistory_…`) have the header on row 1, every cell filled, and real dates. Some months are CSV files instead (with a hidden BOM character at the start, and dates like `1/06/2025 14:30`). The notebook handles all three formats and all three date styles (0 dates failed to parse).

### `blacktown_u91_price_changes.csv`
- **Created by** the notebook (Step 10) from the FuelCheck files: only the Blacktown U91 rows (station, address, time of change, price).
- **Why:** reading all the monthly Excel files takes several minutes; this small file lets the notebook re-run in seconds, and lets anyone run it without downloading FuelCheck. Delete it to rebuild from the raw files.

## Fuel excise (no file)
Excise rates only change about twice a year, so they are entered directly in the notebook (Step 5) rather than loaded from a file.
- **Source:** Australian Taxation Office, fuel tax credit rates for "all other business uses" (equal to the excise rate on petrol) — https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/incentives-and-concessions/fuel-schemes/fuel-tax-credits-business/rates-business
- **Units:** cents per litre, **excluding** GST.
- **Notable changes:** excise halved 30 March – 28 September 2022; cut by 60.9% from 1 April 2026 and 30.4% from 1 July 2026, restored in full on 3 August 2026.
