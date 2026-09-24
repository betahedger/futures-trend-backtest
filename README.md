# 선물 추세추종 전략 백테스트

> 단순 이동평균 추세 신호를 이용해 선물 가격 데이터에서 전략의 수익·위험 특성을 검증하는 Python 프로젝트

## 프로젝트 목적

선물 시장에서 가장 기본적인 추세추종 신호가 어떤 수익·위험 특성을 보이는지 직접 확인하기 위해 만든 연구용 백테스트입니다.

이 프로젝트의 목적은 복잡한 모형으로 높은 과거수익률을 만드는 것이 아닙니다. 대신 금융 아이디어를 코드로 옮기는 전 과정을 재현 가능하게 구현하는 데 초점을 두었습니다.

```text
가설 설정
  ↓
시장 데이터 수집
  ↓
매매 신호 생성
  ↓
포지션 적용
  ↓
거래비용 반영
  ↓
성과 및 위험지표 계산
  ↓
전략의 한계 검토
```

특히 백테스트에서 흔히 발생하는 **미래정보 참조(Look-ahead Bias)** 문제와 거래비용 누락을 피하도록 설계했습니다.

## 전략 아이디어

기본 전략은 **20일 / 60일 단순이동평균 교차 전략**입니다.

```text
20일 이동평균 > 60일 이동평균  →  Long (+1)
20일 이동평균 < 60일 이동평균  →  Short (-1)
```

당일 종가로 계산한 신호를 당일 수익률에 바로 적용하면 미래정보를 사용한 것과 같은 문제가 생길 수 있습니다. 따라서 이 프로젝트에서는 신호를 한 시점 늦춰 실제 포지션에 반영합니다.

```text
t 시점 종가로 신호 계산
        ↓
t+1 시점부터 포지션 적용
```

코드에서는 `signal.shift(1)`을 사용합니다.

## 기본 백테스트 가정

- 데이터 주기: 일별
- 기본 종목: S&P 500 E-mini 선물 연속가격 대용 티커 `ES=F`
- 단기 이동평균: 20거래일
- 장기 이동평균: 60거래일
- 기본 포지션: Long / Short
- 수수료: 회전율 1단위당 1bp
- 슬리피지: 회전율 1단위당 1bp
- Short `-1` → Long `+1` 전환 시 회전율을 `2`로 계산

모든 주요 파라미터는 실행 시 변경할 수 있습니다.

## 계산하는 성과지표

- 누적수익률(Total Return)
- 연환산수익률(CAGR)
- 연환산 변동성
- 샤프지수(Sharpe Ratio)
- 최대낙폭(MDD)
- 포지션 보유일 기준 승률
- 평균 절대 익스포저
- 총 회전율
- 누적 거래비용

## 프로젝트 구조

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

## 실행 방법

가상환경 생성:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
python main.py --symbol "ES=F" --start 2020-01-01
```

다른 선물 예시:

```bash
# 금 선물
python main.py --symbol "GC=F" --start 2020-01-01

# 원유 선물
python main.py --symbol "CL=F" --start 2020-01-01

# Long-only 전략
python main.py --symbol "ES=F" --long-only

# 이동평균 기간 변경
python main.py --symbol "ES=F" --fast 10 --slow 100

# 직접 보유한 CSV 사용
python main.py --csv data/my_futures_data.csv
```

테스트 실행:

```bash
pytest -q
```

## 실행 결과

`main.py`를 실행하면 다음 결과물이 자동으로 생성됩니다.

- `results/metrics.csv` : 주요 성과지표
- `results/backtest_output.csv` : 일별 포지션·수익률·비용
- `results/equity_curve.png` : 전략과 Buy & Hold 누적성과 비교
- `results/price_and_moving_averages.png` : 가격과 이동평균선

최종 수익률 숫자만 보는 것이 아니라 **언제 포지션이 바뀌었고, 얼마의 회전율과 거래비용이 발생했는지**까지 확인할 수 있도록 구성했습니다.

## 코드에서 신경 쓴 부분

### 1. 미래정보 참조 방지

```python
out["position"] = out["signal"].shift(1).fillna(0.0)
```

오늘 종가로 만든 신호가 오늘 수익률에 적용되지 않도록 포지션을 한 시점 지연했습니다.

### 2. 포지션 전환에 따른 회전율 계산

```python
out["turnover"] = out["position"].diff().abs()
```

예를 들어 Short `-1`에서 Long `+1`로 바뀌면 포지션 변화량은 `2`이므로 회전율도 `2`로 계산합니다.

### 3. 거래비용 반영

```python
out["trading_cost"] = out["turnover"] * one_way_cost
out["strategy_return"] = out["strategy_return_gross"] - out["trading_cost"]
```

수수료와 슬리피지를 제외한 총수익률만 제시하지 않고 비용 차감 후 전략수익률을 계산합니다.

## 테스트

단위 테스트를 통해 다음 항목을 확인합니다.

- 신호가 실제 포지션에 한 시점 늦게 반영되는지
- Short ↔ Long 전환 시 회전율이 2로 계산되는지
- 성과지표가 정상적으로 계산되는지

현재 제공된 테스트는 `pytest` 기준으로 통과하도록 구성했습니다.

## 향후 개선 방향

현재 이동평균 교차 전략은 **기준선(Baseline)** 입니다. 이후에는 다음과 같은 방향으로 확장할 수 있습니다.

1. 하나의 이동평균 조합을 고정하지 않고 Walk-forward 방식으로 파라미터 검증
2. 주가지수·원자재·금리 등 여러 선물시장으로 확장
3. 변동성 조정(Volatility Targeting) 포지션 사이징
4. 실제 선물 만기교체(Roll) 처리를 반영한 연속가격 데이터 활용
5. 시장 국면별 성능 분석
6. 정규화 수익률을 이용한 Time-Series Momentum 전략과 비교
7. 증권사/선물사 REST API와 연결해 모의주문 및 모니터링 구조로 확장

## 한계

- Yahoo Finance 연속선물 티커는 빠른 연구에는 편리하지만 거래소 수준의 정교한 과거 선물 데이터와 동일하지 않습니다.
- 선물 만기교체 방식에 따라 과거 가격계열과 성과가 달라질 수 있습니다.
- 현재 거래비용 모형은 단순화되어 있으며 스프레드·시장충격·증거금·자금조달비용을 완전히 반영하지 않습니다.
- 과거 백테스트 수익이 미래 수익을 의미하지 않습니다.
- 같은 데이터에서 이동평균 기간을 반복적으로 조정하면 파라미터 과적합이 발생할 수 있습니다.

## 이 프로젝트에서 보여주고자 한 역량

단순히 Python 코드를 작성하는 것보다, **시장 아이디어를 명확한 가정으로 정의하고 → 코드로 구현하고 → 백테스트 편향과 비용을 점검하고 → 결과의 한계를 설명하는 과정**을 보여주는 것을 목표로 했습니다.

## 유의사항

본 프로젝트는 학습 및 연구 목적이며 특정 금융상품의 매수·매도를 권유하지 않습니다.
