import numpy as np
import pandas as pd

from src.backtest import BacktestConfig, performance_metrics, run_backtest


def sample_prices(n=200):
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    # Deterministic, smooth synthetic series for unit testing only.
    trend = np.linspace(100.0, 130.0, n)
    wave = 2.0 * np.sin(np.linspace(0, 10, n))
    return pd.DataFrame({"Close": trend + wave}, index=idx)


def test_position_is_shifted_one_period():
    df = sample_prices()
    cfg = BacktestConfig(fast_window=5, slow_window=15)
    result = run_backtest(df, cfg)
    expected = result["signal"].shift(1).fillna(0.0)
    pd.testing.assert_series_equal(result["position"], expected, check_names=False)


def test_switching_direction_costs_two_units_of_turnover():
    df = sample_prices()
    cfg = BacktestConfig(fast_window=5, slow_window=15, fee_bps=1, slippage_bps=1)
    result = run_backtest(df, cfg)
    changes = result["position"].diff().abs()
    switches = changes[changes == 2.0]
    if len(switches):
        idx = switches.index[0]
        assert result.loc[idx, "turnover"] == 2.0


def test_metrics_are_finite_when_returns_vary():
    df = sample_prices()
    cfg = BacktestConfig(fast_window=5, slow_window=15)
    result = run_backtest(df, cfg)
    metrics = performance_metrics(result)
    assert "sharpe_ratio" in metrics
    assert "max_drawdown" in metrics
    assert np.isfinite(metrics["max_drawdown"])
