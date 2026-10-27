"""
Tests for fuel_model.py. Run from the repository folder with:

    pytest -v

Each test checks one thing we know the answer to, e.g. the ODE solvers against the exact solution.
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

# Let the tests import fuel_model.py from the folder above
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fuel_model import (load_fuelcheck, find_restorations, days_since_restoration,
                        ode_rhs, euler, rk4, exact, fit_ode, evaluate)


# ---------------------------------------------------------------------------
# ODE and solvers
# ---------------------------------------------------------------------------

def test_ode_rhs_zero_at_target():
    """If the price already equals wholesale + margin and wholesale is flat, the price shouldn't change."""
    assert ode_rhs(0, 180, 175, 0, 0.1, 5) == 0


def test_ode_rhs_sign():
    """Price above target -> falls (negative); price below target -> rises (positive)."""
    assert ode_rhs(0, 190, 175, 0, 0.1, 5) < 0
    assert ode_rhs(0, 170, 175, 0, 0.1, 5) > 0


def test_rk4_matches_exact_solution():
    """The check case from the notebook: 190 c/L, wholesale 175 flat, k = 0.1, m = 5, 3 days -> 187.41."""
    assert rk4(190, 175, 0, 0.1, 5, 3, 1) == pytest.approx(exact(190, 175, 0, 0.1, 5, 3), abs=1e-4)
    assert round(rk4(190, 175, 0, 0.1, 5, 3, 1), 2) == 187.41


def test_euler_and_rk4_converge_with_rising_wholesale():
    """With a small step, both solvers should agree closely with the exact solution (wholesale rising 0.5 c/L/day)."""
    true_value = exact(200, 170, 0.5, 0.03, -2.5, 40)
    assert euler(200, 170, 0.5, 0.03, -2.5, 40, 1 / 64) == pytest.approx(true_value, abs=0.01)
    assert rk4(200, 170, 0.5, 0.03, -2.5, 40, 1) == pytest.approx(true_value, abs=1e-6)


def _measured_order(solver):
    """Slope of log(error) vs log(step size): the measured order of accuracy."""
    step_sizes = np.array([8, 4, 2, 1, 0.5])
    true_value = exact(200, 170, 0.5, 0.03, -2.5, 40)
    errors = [abs(solver(200, 170, 0.5, 0.03, -2.5, 40, dt) - true_value) for dt in step_sizes]
    return np.polyfit(np.log(step_sizes), np.log(errors), 1)[0]


def test_euler_is_first_order():
    """Halving the step should roughly halve Euler's error (order ≈ 1)."""
    assert _measured_order(euler) == pytest.approx(1, abs=0.15)


def test_rk4_is_fourth_order():
    """Halving the step should cut RK4's error by about 16x (order ≈ 4)."""
    assert _measured_order(rk4) == pytest.approx(4, abs=0.2)


def test_vectorised_equals_loop():
    """Solving many days at once (numpy arrays) must give the same answers as one day at a time."""
    rng = np.random.default_rng(0)
    P = rng.uniform(150, 220, 50)
    C = rng.uniform(140, 200, 50)
    slope = rng.uniform(-1, 1, 50)
    vectorised = rk4(P, C, slope, 0.03, -2.5, 3, 1)
    loop = np.array([rk4(P[i], C[i], slope[i], 0.03, -2.5, 3, 1) for i in range(50)])
    assert np.allclose(vectorised, loop)


def test_fit_ode_recovers_known_parameters():
    """Make fake data with k = 0.05 and m = 4, then check the grid search finds those values again."""
    rng = np.random.default_rng(1)
    P = rng.uniform(150, 220, 200)
    C = rng.uniform(140, 200, 200)
    slope = rng.uniform(-1, 1, 200)
    future = exact(P, C, slope, 0.05, 4, 3)                 # "actual" prices from the true k and m
    k_fit, m_fit, grid = fit_ode(P, C, slope, future,
                                 np.arange(0.01, 0.1001, 0.01), np.arange(-5, 10.01, 1), horizon=3)
    assert k_fit == pytest.approx(0.05)
    assert m_fit == pytest.approx(4)
    assert grid.shape == (10, 16)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def test_evaluate_perfect_forecast():
    """A forecast equal to the actual change has MAE 0 and 100% direction."""
    actual = [3, -2, 5, -4]
    result = evaluate("perfect", actual, actual)
    assert result["MAE (c/L)"] == 0
    assert result["direction correct (%)"] == 100


def test_evaluate_known_mae_and_direction():
    """Errors of 1, 1, 2, 6 -> MAE 2.5. Directions: 3 of 4 right (last one wrong) -> 75%."""
    result = evaluate("test", [2, -1, 3, 2], [3, -2, 5, -4])
    assert result["MAE (c/L)"] == 2.5
    assert result["direction correct (%)"] == 75


def test_evaluate_ignores_small_moves():
    """Days where the price moved less than 1 c/L don't count towards direction accuracy."""
    result = evaluate("test", [1, 1], [2, -0.5])     # 2nd day only moved 0.5 c/L -> ignored
    assert result["direction correct (%)"] == 100


def test_evaluate_baseline_has_no_direction():
    """The 'no change' baseline (all zeros) can't predict up or down, so direction is NaN."""
    result = evaluate("baseline", [0, 0, 0], [1, -2, 3])
    assert np.isnan(result["direction correct (%)"])
    assert result["MAE (c/L)"] == 2


# ---------------------------------------------------------------------------
# Price cycle
# ---------------------------------------------------------------------------

def test_find_restorations_counts_first_rise_only():
    """Two big rises in a row = one restoration. A big rise 7+ days later = a new one."""
    change = pd.Series([0, -1, 8, 6, -1, -1, -1, -1, -1, -1, -1, -1, 7, 0])
    flags = find_restorations(change)
    assert list(flags[flags].index) == [2, 12]


def test_days_since_restoration():
    """Count resets to 0 on a restoration day and is NaN before the first one."""
    result = days_since_restoration([False, True, False, False, True, False])
    assert np.isnan(result[0])
    assert result[1:] == [0, 1, 2, 0, 1]


# ---------------------------------------------------------------------------
# Data loading (uses small fake FuelCheck files, so the real data isn't needed)
# ---------------------------------------------------------------------------

HEADER = ["ServiceStationName", "Address", "Suburb", "Postcode", "Brand", "FuelCode", "PriceUpdatedDate", "Price"]


def test_load_fuelcheck_csv_keeps_only_blacktown_u91(tmp_path):
    """New CSV format: keeps Blacktown U91 rows only (not other suburbs or fuels)."""
    rows = [HEADER,
            ["Station A", "1 MAIN ST, BLACKTOWN", "Blacktown", "2148", "Ampol", "U91", "01/06/2025 08:00", "189.9"],
            ["Station A", "1 MAIN ST, BLACKTOWN", "Blacktown", "2148", "Ampol", "E10", "01/06/2025 08:00", "187.9"],
            ["Station B", "5 HIGH ST, PARRAMATTA", "Parramatta", "2150", "BP", "U91", "01/06/2025 09:00", "195.9"]]
    path = tmp_path / "PriceHistory_June2025.csv"
    pd.DataFrame(rows).to_csv(path, header=False, index=False, encoding="utf-8-sig")   # with a BOM, like the real files

    df = load_fuelcheck(str(path))
    assert len(df) == 1
    assert df.iloc[0]["Price"] == "189.9"
    assert list(df.columns) == ["ServiceStationName", "Address", "PriceUpdatedDate", "Price"]


def test_load_fuelcheck_old_xlsx_with_title_rows_and_merged_cells(tmp_path):
    """Old Excel format: title rows above the header, and blank (merged) cells filled from the row above."""
    rows = [["Fuel price history", None, None, None, None, None, None, None],     # title rows
            [None] * 8,
            HEADER,
            ["Station A", "1 MAIN ST, BLACKTOWN", "BLACKTOWN", 2148, "Ampol", "U91", "01/03/2020 08:00:00 AM", 129.9],
            [None, None, None, None, None, None, "02/03/2020 08:00:00 AM", 127.9]]   # merged cells -> blank
    path = tmp_path / "price_history_checks_mar2020.xlsx"
    pd.DataFrame(rows).to_excel(path, header=False, index=False)

    df = load_fuelcheck(str(path))
    assert len(df) == 2                                       # the blank row was filled and kept
    assert (df["ServiceStationName"] == "Station A").all()
