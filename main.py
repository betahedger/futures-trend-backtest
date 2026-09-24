from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import pandas as pd

from src.backtest import BacktestConfig, performance_metrics, run_backtest
from src.data import download_yfinance, load_csv
from src.reporting import save_outputs


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backtest a moving-average trend strategy on futures data.")
    source = p.add_mutually_exclusive_group()
    source.add_argument("--csv", type=str, help="Local CSV with Date and Close columns.")
    source.add_argument("--symbol", type=str, default="ES=F", help="Yahoo Finance futures ticker. Default: ES=F")
    p.add_argument("--start", default="2020-01-01")
    p.add_argument("--end", default=None)
    p.add_argument("--fast", type=int, default=20)
    p.add_argument("--slow", type=int, default=60)
    p.add_argument("--fee-bps", type=float, default=1.0)
    p.add_argument("--slippage-bps", type=float, default=1.0)
    p.add_argument("--long-only", action="store_true")
    p.add_argument("--output-dir", default="results")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.csv:
        data = load_csv(args.csv)
        label = Path(args.csv).stem
    else:
        data = download_yfinance(args.symbol, args.start, args.end)
        label = args.symbol

    config = BacktestConfig(
        fast_window=args.fast,
        slow_window=args.slow,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        allow_short=not args.long_only,
    )

    result = run_backtest(data, config)
    metrics = performance_metrics(result, config.periods_per_year)
    metrics = {"instrument": label, "run_date": date.today().isoformat(), **metrics}

    save_outputs(result, metrics, args.output_dir)

    display = pd.Series(metrics, name="value")
    print(display.to_string())
    print(f"\nSaved outputs to: {Path(args.output_dir).resolve()}")


if __name__ == "__main__":
    main()
