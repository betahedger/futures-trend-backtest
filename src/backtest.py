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
            raise ValueError("이동평균 기간은 0보다 커야 합니다.")
        if self.fast_window >= self.slow_window:
            raise ValueError("fast_window는 slow_window보다 작아야 합니다.")
        if self.fee_bps < 0 or self.slippage_bps < 0:
            raise ValueError("거래비용은 음수가 될 수 없습니다.")


def _validate_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    if "Close" not in df.columns:
        raise ValueError("입력 데이터에는 'Close' 열이 필요합니다.")

    out = df.copy()
    out = out.sort_index()
    out["Close"] = pd.to_numeric(out["Close"], errors="coerce")
    out = out.dropna(subset=["Close"])

    if len(out) < 3:
        raise ValueError("유효한 관측치가 부족합니다.")
    if (out["Close"] <= 0).any():
        raise ValueError("종가는 0보다 커야 합니다.")
    return out


def run_backtest(df: pd.DataFrame, config: BacktestConfig) -> pd.DataFrame:
    """이동평균 추세추종 전략 백테스트를 실행합니다.

    t 시점 종가로 계산한 신호를 한 시점 지연해 t+1부터 포지션에 반영합니다.
    이를 통해 이동평균 계산에 사용된 당일 종가 정보를 같은 날 수익률에
    적용하는 미래정보 참조 문제를 방지합니다.
    """
    config.validate()
    out = _validate_price_frame(df)

    out["fast_ma"] = out["Close"].rolling(config.fast_window).mean()
    out["slow_ma"] = out["Close"].rolling(config.slow_window).mean()

    if config.allow_short:
        signal = np.where(out["fast_ma"] > out["slow_ma"], 1.0, -1.0)
    else:
        signal = np.where(out["fast_ma"] > out["slow_ma"], 1.0, 0.0)

    # 장기 이동평균을 계산할 수 있기 전까지는 포지션을 보유하지 않습니다.
    out["signal"] = pd.Series(signal, index=out.index).where(out["slow_ma"].notna(), 0.0)

    # 핵심: 오늘 계산한 신호는 다음 거래일부터 포지션에 반영합니다.
    out["position"] = out["signal"].shift(1).fillna(0.0)
    out["asset_return"] = out["Close"].pct_change().fillna(0.0)

    # 회전율은 포지션 변화의 절댓값입니다. -1에서 +1로 전환하면 2로 계산합니다.
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
        raise ValueError("계산 가능한 전략수익률이 없습니다.")

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
