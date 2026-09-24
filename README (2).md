# Futures Trend-Following Backtest

> A transparent Python backtest of a moving-average trend strategy on futures price data.

## Why I Built This

선물 시장에서 가장 단순한 추세 신호가 실제로 어떤 위험·수익 특성을 보이는지 확인하기 위해 만든 연구용 백테스트입니다. 목표는 복잡한 모델로 높은 과거수익률을 만드는 것이 아니라, **신호 생성 → 포지션 적용 → 거래비용 → 성과평가**의 전 과정을 재현 가능하게 구현하는 것입니다.

이 프로젝트는 금융 아이디어를 Python 코드로 검증하고, 백테스트에서 흔히 발생하는 look-ahead bias와 거래비용 누락을 피하는 데 초점을 둡니다.

## Strategy

기본 전략은 20일/60일 단순이동평균 교차입니다.

```text
Fast MA > Slow MA  → +1 Long
Fast MA < Slow MA  → -1 Short
```

중요한 점은 당일 종가로 계산된 신호를 당일 수익률에 적용하지 않는 것입니다.

```text
Signal at t → Position from t+1
```

코드에서는 `signal.shift(1)`을 사용해 한 기간 지연된 포지션을 적용합니다.

## Backtest Assumptions

- Daily price data
- Default instrument: S&P 500 E-mini continuous futures proxy ticker `ES=F`
- Fast MA: 20 trading days
- Slow MA: 60 trading days
- Default position: long / short
- Fee: 1 bp per unit of turnover
- Slippage: 1 bp per unit of turnover
- A switch from short `-1` to long `+1` is treated as turnover `2`

All parameters can be changed from the command line.

## Metrics

The program calculates:

- Total return
- CAGR
- Annualized volatility
- Sharpe ratio
- Maximum drawdown
- Hit rate on active days
- Average absolute exposure
- Total turnover
- Cumulative modeled trading cost

## Project Structure

```text
futures-trend-backtest/
├── README.md
├── main.py
├── requirements.txt
├── src/
│   ├── backtest.py
│   ├── data.py
│   └── reporting.py
├── notebooks/
│   └── 01_backtest_walkthrough.ipynb
├── tests/
│   └── test_backtest.py
├── data/
│   └── README.md
└── results/
    └── README.md
```

## Quick Start

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
python main.py --symbol "ES=F" --start 2020-01-01
```

Other examples:

```bash
# Gold futures
python main.py --symbol "GC=F" --start 2020-01-01

# Crude oil futures
python main.py --symbol "CL=F" --start 2020-01-01

# Long-only version
python main.py --symbol "ES=F" --long-only

# Different moving-average windows
python main.py --symbol "ES=F" --fast 10 --slow 100

# Local CSV
python main.py --csv data/my_futures_data.csv
```

Run tests:

```bash
pytest -q
```

## Outputs

After execution, the program generates:

- `results/metrics.csv`
- `results/backtest_output.csv`
- `results/equity_curve.png`
- `results/price_and_moving_averages.png`

These files make it possible to inspect not only the final performance number but also positions, turnover, trading costs, and the full return path.

## What I Would Test Next

A moving-average crossover is only a baseline. The next research steps are:

1. Walk-forward parameter evaluation instead of choosing one fixed pair of windows
2. Multiple futures markets rather than one instrument
3. Volatility-targeted position sizing
4. Contract-roll treatment using higher-quality continuous futures data
5. Regime analysis across equity, commodity, and rate futures
6. Comparison with time-series momentum using normalized returns
7. Integration with a brokerage REST API for paper-trading execution and monitoring

## Limitations

- Yahoo Finance continuous futures tickers are convenient for research but are not a substitute for exchange-grade historical contract data.
- Futures contract rolls can materially affect historical price series.
- Transaction costs here are simplified and do not model spread, market impact, margin, or financing in full detail.
- A profitable historical backtest does not establish future profitability.
- Moving-average parameters can themselves be overfit if repeatedly tuned on the same sample.

## Design Principle

The purpose of this repository is not to claim that a simple trend rule is an investment edge. It is to demonstrate a reproducible process for turning a market hypothesis into code, testing it with explicit assumptions, and identifying where a backtest can fail.

## Disclaimer

Educational and research use only. This repository is not investment advice.
