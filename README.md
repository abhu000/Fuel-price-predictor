# Fuel Price Predictor: Blacktown U91

**MMA3001 individual project · Aryan Bhurjhee · Monash University, Semester 2 2026**

Forecasting the average unleaded 91 (U91) pump price in Blacktown, NSW, **2–3 days ahead**, so drivers can decide which day to fill up.

---

## Problem

Petrol prices in Sydney move in an irregular cycle: they drift down for a few weeks, then jump sharply when retailers restore their margins. A driver who fills up the day before a jump can pay 20–30 c/L more than one who fills up just after it bottoms out. This project builds a model that uses wholesale costs, oil prices, the exchange rate, fuel excise and recent pump prices to forecast where the Blacktown price is heading over the next few days.

**Scope:** U91 only, stations in Blacktown, daily data from Jan 2020 to October 2026.

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

**Output:** predicted average U91 price in Blacktown (c/L), 2–3 days ahead.

**Inputs:**
- past Blacktown U91 prices (1, 2, 3 and 7 days earlier)
- Sydney terminal gate price
- Brent crude oil, converted to Australian cents per litre using AUD/USD
- fuel excise rate
- retail margin (pump price minus terminal gate price) and days since the last price jump, which capture where we are in the price cycle

All inputs are lagged so the model only uses information that would be available on the day the forecast is made.

## Repository structure

```
Fuel-price-predictor/
├── README.md                    ← this file
├── LICENSE                      ← MIT licence
├── requirements.txt             ← Python packages needed
├── fuel_price_predictor.ipynb   ← main notebook: cleaning, modelling, validation, performance
├── fuel_model.py                ← main functions (loading, ODE solvers, fitting, evaluation) with docstrings
├── download_fuelcheck.py        ← downloads the raw FuelCheck files
├── tests/
│   └── test_fuel_model.py       ← pytest test functions
├── test_report.html             ← pytest report (also test_report.txt)
├── docs/                        ← HTML documentation of fuel_model.py (made with pdoc)
└── data/                        ← supporting data + blacktown_u91_price_changes.csv (see data/README.md)
```



## Method

1. clean and merge data/load each source sure consistency with data (i.e convert USD to AUD etc)
2. compare a naive baseline (price in 3 days = today's price) against regression and machine-learning models, using a time-based train/test split. RK4 and euler via ODE: dP/dt = k(C(t) + m − P), fit k and m by grid search on 2020–2024, and solve with RK4 and euler to compare RK4 effectiveness. 
3. compare RK4 method with a baseline (original data), linear regression model and random forest model to compare MAE and effectiveness in predicting price increases/ decreases (on testing data

## Results

Trained on 2020–2024, tested on withheld data from Jan 2025 – Aug 2026 (3 days ahead).
Direction = share of days (price moved ≥ 1 c/L) where up/down was predicted correctly.

| Model | MAE (c/L) | Direction accuracy (%) |
|---|---|---|
| Baseline: no change | 5.42 | – |
| ODE (RK4) | 4.95 | 65.6% |
| ODE (Euler) | 4.96 | 65.3% |
| Linear regression | **4.41** | 77.0% |
| Random forest | 4.74 | **80.7%** |

Fitted ODE: k = 0.030 per day, m = −2.5 c/L (half-life ≈ 23 days).

## Validation and acceptance criteria

- Every model must beat the no-change baseline (MAE 5.42 c/L) on the withheld test data: all do.
- RK4 must match the exact solution of the ODE; measured order of accuracy: Euler 1.03, RK4 4.07 (theory 1 and 4).
- RK4 reaches 0.01 c/L accuracy with 49× fewer FLOPs than Euler.

## Tests

`tests/test_fuel_model.py` has 16 pytest tests: solvers vs the exact solution, order of accuracy,
vectorised vs loop, grid-search fitting, evaluation metrics, restoration detection and both FuelCheck file formats.

Run from the repository folder:
    pytest -v --html=test_report.html --self-contained-html

Latest result: 16 passed (see `test_report.html`).

## Documentation

HTML documentation of `fuel_model.py` is in `docs/` (generated with pdoc). Rebuild with:
    pdoc fuel_model.py -o docs

## Licence

MIT – see `LICENSE`.
## Notes

- Excise rates were compiled manually from the ATO's published fuel tax credit rates and entered in the notebook as a step function.
- Fuel excise was cut twice during the study period (March–September 2022 and April–August 2026), which causes large step changes in pump prices.
