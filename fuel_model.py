"""
Core functions for the Blacktown U91 fuel price predictor (MMA3001 project, Seth Bhurjhee).

The notebook `fuel_price_predictor.ipynb` runs the full analysis step by step.
This module holds the same main functions in one importable file, so that they can be
documented (HTML docs made with pdoc, in `docs/`) and tested (pytest, in `tests/`).

Model
-----
Retail price P adjusts towards the wholesale cost C(t) plus a target margin m:

    dP/dt = k * (C(t) + m - P),      with C(s) = C0 + slope * s  (wholesale following its 3-day trend)

The ODE is solved with Euler's method (1st order) or the 4th-order Runge-Kutta method (RK4).
Because C(s) is a straight line, the ODE also has an exact solution, used to verify the solvers.
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_fuelcheck(path, suburb="BLACKTOWN", fuel="U91"):
    """Load one NSW FuelCheck monthly file and keep only one suburb and fuel type.

    Handles all three FuelCheck formats: old .xlsx files (title rows above the header,
    merged cells), newer .xlsx files, and .csv files (which start with a hidden BOM character).

    Parameters
    ----------
    path : str
        Path to a FuelCheck .xlsx or .csv file.
    suburb : str
        Suburb to keep (upper case), default "BLACKTOWN".
    fuel : str
        Fuel code to keep, default "U91".

    Returns
    -------
    pandas.DataFrame
        Columns ServiceStationName, Address, PriceUpdatedDate, Price (all still as text;
        dates and prices are converted later in the notebook).
    """
    # Read every cell as-is with no column names yet (the header row isn't always the first row)
    if path.endswith(".csv"):
        raw = pd.read_csv(path, header=None, dtype=str, encoding="utf-8-sig")   # utf-8-sig removes the BOM
    else:
        raw = pd.read_excel(path, header=None)

    # Find the header row: the one whose first cell is "ServiceStationName"
    first_col = raw.iloc[:, 0].astype(str).str.strip()
    header_row = raw.index[first_col == "ServiceStationName"][0]

    df = raw.iloc[header_row + 1:].copy()                        # everything below the header row
    df.columns = raw.iloc[header_row].astype(str).str.strip()    # use that row as the column names

    # Old files: merged cells are blank -> copy the value from the row above
    fill_cols = ["ServiceStationName", "Address", "Suburb", "Postcode", "Brand", "FuelCode", "PriceUpdatedDate"]
    df[fill_cols] = df[fill_cols].ffill()

    # Keep only the chosen suburb and fuel
    is_suburb = df["Suburb"].astype(str).str.upper().str.strip() == suburb
    is_fuel   = df["FuelCode"].astype(str).str.strip() == fuel
    df = df[is_suburb & is_fuel]

    return df[["ServiceStationName", "Address", "PriceUpdatedDate", "Price"]]


# ---------------------------------------------------------------------------
# Price cycle
# ---------------------------------------------------------------------------

def find_restorations(daily_change, threshold=5, gap=7):
    """Flag the first day of each price restoration (the sudden jump in the Sydney price cycle).

    A restoration is a daily rise bigger than `threshold` c/L with no such rise in the
    previous `gap` days (so a jump spread over 2-3 days is only counted once).

    Parameters
    ----------
    daily_change : pandas.Series
        Change in the average price from the day before (c/L), one value per day.
    threshold : float
        Size of a "big rise" in c/L (default 5).
    gap : int
        Number of earlier days that must have no big rise (default 7).

    Returns
    -------
    pandas.Series of bool
        True on the first day of each restoration.
    """
    big_rise = daily_change > threshold
    # Was there a big rise in the previous `gap` days? (shift(1) = only look at days BEFORE today)
    rise_before = big_rise.shift(1, fill_value=False).astype(int).rolling(gap, min_periods=1).max() > 0
    return big_rise & ~rise_before


def days_since_restoration(restoration):
    """Count the days since the last restoration.

    Parameters
    ----------
    restoration : sequence of bool
        True on restoration days (output of `find_restorations`).

    Returns
    -------
    list of float
        0 on a restoration day, then 1, 2, 3, ... until the next one.
        NaN before the first restoration (the count is unknown).
    """
    count = np.nan
    days_since = []
    for r in restoration:
        if r:
            count = 0                            # reset on a restoration day
        elif not np.isnan(count):
            count = count + 1                    # otherwise count up by 1 each day
        days_since.append(count)
    return days_since


# ---------------------------------------------------------------------------
# ODE model and numerical solvers
# ---------------------------------------------------------------------------

def ode_rhs(s, P, C0, slope, k, m):
    """Right-hand side of the price-adjustment ODE, f(s, P) = dP/dt.

    Parameters
    ----------
    s : float
        Time since the start of the forecast (days).
    P : float or numpy array
        Current retail price (c/L).
    C0 : float or numpy array
        Wholesale (terminal gate) price at s = 0 (c/L).
    slope : float or numpy array
        Recent wholesale trend (c/L per day), so that C(s) = C0 + slope * s.
    k : float
        Speed of adjustment (per day).
    m : float
        Target margin above wholesale (c/L).

    Returns
    -------
    float or numpy array
        dP/dt, the rate the retail price is changing (c/L per day).
    """
    # dP/dt = k * (C(s) + m - P), where C(s) = C0 + slope * s
    return k * (C0 + slope * s + m - P)


def euler(P0, C0, slope, k, m, days, dt):
    """Solve the ODE with Euler's method (1st order: one slope per step).

    Parameters
    ----------
    P0 : float or numpy array
        Starting retail price (c/L). Arrays solve the ODE for many days at once.
    C0, slope, k, m :
        As in `ode_rhs`.
    days : float
        How far ahead to forecast (days).
    dt : float
        Step size (days). `days / dt` should be a whole number.

    Returns
    -------
    float or numpy array
        Predicted retail price after `days` (c/L).
    """
    P, s = P0, 0.0
    for _ in range(round(days / dt)):                       # number of steps = days / step size
        P = P + dt * ode_rhs(s, P, C0, slope, k, m)          # one slope, at the start of the step
        s = s + dt
    return P


def rk4(P0, C0, slope, k, m, days, dt):
    """Solve the ODE with the classical 4th-order Runge-Kutta method (RK4).

    Parameters
    ----------
    P0, C0, slope, k, m, days, dt :
        As in `euler`.

    Returns
    -------
    float or numpy array
        Predicted retail price after `days` (c/L).
    """
    P, s = P0, 0.0
    for _ in range(round(days / dt)):
        k1 = ode_rhs(s,          P,               C0, slope, k, m)   # slope at the start
        k2 = ode_rhs(s + dt / 2, P + dt / 2 * k1, C0, slope, k, m)   # slope at the midpoint (using k1)
        k3 = ode_rhs(s + dt / 2, P + dt / 2 * k2, C0, slope, k, m)   # slope at the midpoint again (using k2)
        k4 = ode_rhs(s + dt,     P + dt * k3,     C0, slope, k, m)   # slope at the end
        P = P + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)                  # weighted average, midpoints count double
        s = s + dt
    return P


def exact(P0, C0, slope, k, m, s):
    """Exact solution of the ODE (possible because C(s) is a straight line). Used to verify the solvers.

    Parameters
    ----------
    P0, C0, slope, m :
        As in `euler`.
    k : float
        Speed of adjustment (per day), must be > 0.
    s : float
        Days ahead.

    Returns
    -------
    float or numpy array
        Exact retail price after `s` days (c/L).
    """
    return C0 + m + slope * s - slope / k + (P0 - C0 - m + slope / k) * np.exp(-k * s)


def fit_ode(P, C, slope, future_price, k_values, m_values, horizon=3, dt=1):
    """Fit k and m by grid search: try every (k, m) pair and keep the one with the lowest MAE.

    Only training data should be passed in, so the test period is never used to choose k and m.

    Parameters
    ----------
    P, C, slope : numpy arrays
        Retail price, wholesale price and wholesale trend on each training day.
    future_price : numpy array
        Actual retail price `horizon` days later.
    k_values, m_values : numpy arrays
        Values of k and m to try.
    horizon : int
        Forecast length in days (default 3).
    dt : float
        RK4 step size in days (default 1).

    Returns
    -------
    (float, float, numpy array)
        Best k, best m, and the table of MAEs (one row per k, one column per m).
    """
    grid_mae = np.zeros((len(k_values), len(m_values)))
    for i, k in enumerate(k_values):
        for j, m in enumerate(m_values):
            forecast = rk4(P, C, slope, k, m, horizon, dt)          # all training days at once (vectorised)
            grid_mae[i, j] = np.mean(np.abs(forecast - future_price))
    best_i, best_j = np.unravel_index(grid_mae.argmin(), grid_mae.shape)   # position of the smallest MAE
    return k_values[best_i], m_values[best_j], grid_mae


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(name, predicted_change, actual_change, min_move=1):
    """Score a forecast with the mean absolute error (MAE) and direction accuracy.

    Parameters
    ----------
    name : str
        Model name (for the results table).
    predicted_change : array-like
        Predicted price change over the forecast horizon (c/L).
    actual_change : array-like
        Actual price change over the same horizon (c/L).
    min_move : float
        Only days where the price moved by at least this much (c/L) count towards
        direction accuracy (default 1).

    Returns
    -------
    dict
        {"model", "MAE (c/L)", "direction correct (%)"}. Direction is NaN for a forecast
        that is always 0 (it never predicts up or down).
    """
    predicted_change = np.asarray(predicted_change, dtype=float)
    actual_change    = np.asarray(actual_change, dtype=float)
    mae = np.mean(np.abs(predicted_change - actual_change))      # average size of the error (c/L)

    moved = np.abs(actual_change) >= min_move                    # ignore days where the price barely moved
    if np.all(predicted_change == 0):
        direction = np.nan                                       # "no change" never predicts a direction
    else:
        direction = np.mean(np.sign(predicted_change[moved]) == np.sign(actual_change[moved])) * 100

    return {"model": name, "MAE (c/L)": round(mae, 2), "direction correct (%)": round(direction, 1)}
