from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import pandas as pd

from src.backtest import BacktestConfig, performance_metrics, run_backtest
from src.data import download_yfinance, load_csv
from src.reporting import save_outputs


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="선물 가격 데이터에서 이동평균 추세추종 전략을 백테스트합니다.")
    source = p.add_mutually_exclusive_group()
    source.add_argument("--csv", type=str, help="Date와 Close 열을 포함한 로컬 CSV 파일")
    source.add_argument("--symbol", type=str, default="ES=F", help="Yahoo Finance 선물 티커 (기본값: ES=F)")
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
    print(f"\n결과 저장 위치: {Path(args.output_dir).resolve()}")


if __name__ == "__main__":
    main()
