# Fuel Price Predictor: Parramatta U91

**MMA3001 individual project · Seth Bhurjhee · Monash University, Semester 2 2026**

Forecasting the average unleaded 91 (U91) pump price in Parramatta, NSW, **2–3 days ahead**, so drivers can decide which day to fill up.

---

## Problem

Petrol prices in Sydney move in an irregular cycle: they drift down for a few weeks, then jump sharply when retailers restore their margins. A driver who fills up the day before a jump can pay 20–30 c/L more than one who fills up just after it bottoms out. This project builds a model that uses wholesale costs, oil prices, the exchange rate, fuel excise and recent pump prices to forecast where the Parramatta price is heading over the next few days.

**Scope:** U91 only, stations in Parramatta, daily data from August 2016 to October 2026.

## Data

| Data | Source | Frequency | Used for |
|---|---|---|---|
| Station-level fuel prices | [NSW FuelCheck price history](https://data.nsw.gov.au/data/dataset/fuel-check) (NSW Government) | Every price change | Target variable and past prices |
| Terminal gate prices (Sydney, petrol) | [Australian Institute of Petroleum](https://www.aip.com.au/resources/historical-ulp-and-diesel-tgp-data) | Business days | Wholesale cost |
| AUD/USD exchange rate | [Reserve Bank of Australia, table F11.1](https://www.rba.gov.au/statistics/historical-data.html) | Business days | Converting oil prices to AUD |
| Brent crude oil price | [FRED series DCOILBRENTEU](https://fred.stlouisfed.org/series/DCOILBRENTEU) | Business days | Raw material cost |
| Fuel excise rates | [Australian Taxation Office](https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/excise-on-fuel-and-petroleum-products/excise-duty-rates-for-fuel-and-petroleum-products) | ~2 changes per year | Tax component of the price |

See [`data/README.md`](data/README.md) for file-by-file details, processing notes and how to download the FuelCheck files.

## Model inputs and output

**Output:** predicted average U91 price in Parramatta (c/L), 2–3 days ahead.

**Inputs:**
- past Parramatta U91 prices (1, 2, 3 and 7 days earlier)
- Sydney terminal gate price
- Brent crude oil, converted to Australian cents per litre using AUD/USD
- fuel excise rate
- retail margin (pump price minus terminal gate price) and days since the last price jump, which capture where we are in the price cycle

All inputs are lagged so the model only uses information that would be available on the day the forecast is made.

## Repository structure

```
fuel-price-predictor/
├── README.md                    ← this file
├── requirements.txt             ← Python packages needed
├── fuel_price_predictor.ipynb   ← main notebook: cleaning, EDA, modelling
├── download_fuelcheck.py        ← downloads the FuelCheck monthly files
└── data/
    ├── README.md                ← data sources and notes
    ├── AIP_Terminal_gate_prices_Data_09-Oct-2026.xlsx
    ├── exchange_rate_2014-2017.xls
    ├── exchange_rate_2018-2022.xls
    ├── exchange_rate_2023-current.xls
    ├── DCOILBRENTEU.csv
    └── fuelcheck/               ← FuelCheck files go here (not stored on GitHub, see below)
```

## How to run

1. Install Python 3 (e.g. via Anaconda), then install the packages:
   ```
   pip install -r requirements.txt
   ```
2. Download the FuelCheck files into `data/fuelcheck/`:
   ```
   python download_fuelcheck.py
   ```
   The FuelCheck files total several hundred MB, so they are **not stored in this repository**. The script downloads them directly from the NSW Government data portal.
3. Open `fuel_price_predictor.ipynb` in Jupyter or VS Code and choose **Run All**.

## Method

1. **Data cleaning:** load each source, keep only the needed columns, fix data types, check for missing values and duplicates, and cut everything to the same date range.
2. **Integration:** merge everything into one table with one row per calendar day. Weekend gaps in business-day data are forward-filled.
3. **Exploratory analysis:** price trends, the Sydney price cycle, the retail margin, and the effect of the 2022 and 2026 excise cuts.
4. **Modelling:** compare a naive baseline (price in 3 days = today's price) against regression and machine-learning models, using a time-based train/test split.
5. **Evaluation:** error in c/L, and accuracy at predicting whether the price will go up or down.

## Project status

- [x] Supporting data collected and cleaned (terminal gate price, AUD/USD, Brent, excise)
- [ ] FuelCheck data cleaned and merged
- [ ] Exploratory data analysis
- [ ] Modelling and evaluation
- [ ] Report

## Notes

- Excise rates were compiled manually from the ATO's published fuel tax credit rates and entered in the notebook as a step function.
- Fuel excise was cut twice during the study period (March–September 2022 and April–August 2026), which causes large step changes in pump prices.
