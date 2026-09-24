from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BacktestConfig:
    fast_window: int = 20
    slow_window: int = 60
    fee_bps: float = 1.0
    slippage_bps: float = 1.0
    allow_short: bool = True
    periods_per_year: int = 252

    def validate(self) -> None:
        if self.fast_window <= 0 or self.slow_window <= 0:
            raise ValueError("Moving-average windows must be positive.")
        if self.fast_window >= self.slow_window:
            raise ValueError("fast_window must be smaller than slow_window.")
        if self.fee_bps < 0 or self.slippage_bps < 0:
            raise ValueError("Trading costs cannot be negative.")


def _validate_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    if "Close" not in df.columns:
        raise ValueError("Input data must contain a 'Close' column.")

    out = df.copy()
    out = out.sort_index()
    out["Close"] = pd.to_numeric(out["Close"], errors="coerce")
    out = out.dropna(subset=["Close"])

    if len(out) < 3:
        raise ValueError("Not enough valid observations.")
    if (out["Close"] <= 0).any():
        raise ValueError("Close prices must be positive.")
    return out


def run_backtest(df: pd.DataFrame, config: BacktestConfig) -> pd.DataFrame:
    """Run a moving-average trend-following backtest.

    Signal at t is applied from t+1 by shifting the position one period.
    This prevents the strategy from trading on information from the same
    closing price used to compute the moving averages.
    """
    config.validate()
    out = _validate_price_frame(df)

    out["fast_ma"] = out["Close"].rolling(config.fast_window).mean()
    out["slow_ma"] = out["Close"].rolling(config.slow_window).mean()

    if config.allow_short:
        signal = np.where(out["fast_ma"] > out["slow_ma"], 1.0, -1.0)
    else:
        signal = np.where(out["fast_ma"] > out["slow_ma"], 1.0, 0.0)

    # No position until the slow moving average is available.
    out["signal"] = pd.Series(signal, index=out.index).where(out["slow_ma"].notna(), 0.0)

    # Critical anti-look-ahead step: today's signal becomes tomorrow's position.
    out["position"] = out["signal"].shift(1).fillna(0.0)
    out["asset_return"] = out["Close"].pct_change().fillna(0.0)

    # Turnover is the absolute change in exposure. Switching -1 -> +1 = 2 units.
    out["turnover"] = out["position"].diff().abs().fillna(out["position"].abs())
    one_way_cost = (config.fee_bps + config.slippage_bps) / 10_000.0
    out["trading_cost"] = out["turnover"] * one_way_cost

    out["strategy_return_gross"] = out["position"] * out["asset_return"]
    out["strategy_return"] = out["strategy_return_gross"] - out["trading_cost"]

    out["strategy_equity"] = (1.0 + out["strategy_return"]).cumprod()
    out["buy_hold_equity"] = (1.0 + out["asset_return"]).cumprod()
    return out


def performance_metrics(result: pd.DataFrame, periods_per_year: int = 252) -> dict[str, float]:
    r = result["strategy_return"].dropna()
    if r.empty:
        raise ValueError("No strategy returns available.")

    equity = (1.0 + r).cumprod()
    n = len(r)
    years = n / periods_per_year

    total_return = float(equity.iloc[-1] - 1.0)
    cagr = float(equity.iloc[-1] ** (1.0 / years) - 1.0) if years > 0 and equity.iloc[-1] > 0 else np.nan
    ann_vol = float(r.std(ddof=1) * np.sqrt(periods_per_year)) if n > 1 else np.nan
    sharpe = float((r.mean() / r.std(ddof=1)) * np.sqrt(periods_per_year)) if n > 1 and r.std(ddof=1) > 0 else np.nan

    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    max_drawdown = float(drawdown.min())

    turnover = float(result["turnover"].sum())
    trading_cost = float(result["trading_cost"].sum())
    exposure = float(result["position"].abs().mean())

    active = result["position"] != 0
    active_returns = result.loc[active, "strategy_return"]
    hit_rate = float((active_returns > 0).mean()) if len(active_returns) else np.nan

    return {
        "total_return": total_return,
        "cagr": cagr,
        "annualized_volatility": ann_vol,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_drawdown,
        "hit_rate_active_days": hit_rate,
        "average_abs_exposure": exposure,
        "total_turnover": turnover,
        "cumulative_trading_cost": trading_cost,
        "observations": float(n),
    }
