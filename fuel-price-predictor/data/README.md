# Data

All files in this folder are raw downloads, unchanged from the source. All cleaning happens inside `fuel_price_predictor.ipynb`.

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

### `fuelcheck/` (not stored on GitHub)
- **Source:** NSW Government, *FuelCheck* price history — https://data.nsw.gov.au/data/dataset/fuel-check
- **Contents:** one Excel file per month from August 2016. Each row is one station changing the price of one fuel type.
- **Used:** stations in Parramatta, fuel code `U91`.
- **How to get it:** run `python download_fuelcheck.py` from the project folder. The files total several hundred MB, so they aren't uploaded to this repository.
- **Notes:** column names and date formats change between years; the notebook handles each format.

## Fuel excise (no file)
Excise rates only change about twice a year, so they are entered directly in the notebook (Step 5) rather than loaded from a file.
- **Source:** Australian Taxation Office, fuel tax credit rates for "all other business uses" (equal to the excise rate on petrol) — https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/incentives-and-concessions/fuel-schemes/fuel-tax-credits-business/rates-business
- **Units:** cents per litre, **excluding** GST.
- **Notable changes:** excise halved 30 March – 28 September 2022; cut by 60.9% from 1 April 2026 and 30.4% from 1 July 2026, restored in full on 3 August 2026.
