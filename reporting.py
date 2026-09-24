from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def save_outputs(result: pd.DataFrame, metrics: dict[str, float], output_dir: str | Path) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result.to_csv(output_dir / "backtest_output.csv")
    pd.DataFrame([metrics]).to_csv(output_dir / "metrics.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    result[["strategy_equity", "buy_hold_equity"]].plot(ax=ax)
    ax.set_title("Trend Strategy vs Buy & Hold")
    ax.set_ylabel("Growth of $1")
    ax.set_xlabel("")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "equity_curve.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    result["Close"].plot(ax=ax, label="Close", linewidth=1)
    result["fast_ma"].plot(ax=ax, label="Fast MA", linewidth=1)
    result["slow_ma"].plot(ax=ax, label="Slow MA", linewidth=1)
    ax.set_title("Price and Moving Averages")
    ax.set_xlabel("")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "price_and_moving_averages.png", dpi=160)
    plt.close(fig)
