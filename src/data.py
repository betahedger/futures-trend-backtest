from __future__ import annotations

from pathlib import Path
import pandas as pd


def load_csv(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)
    date_candidates = [c for c in df.columns if c.lower() in {"date", "datetime", "timestamp"}]
    if date_candidates:
        date_col = date_candidates[0]
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col)
    else:
        df.index = pd.to_datetime(df.index)

    # 자주 사용되는 소문자 열 이름도 자동으로 인식합니다.
    rename = {c: c.title() for c in df.columns if c.lower() in {"open", "high", "low", "close", "volume"}}
    return df.rename(columns=rename).sort_index()


def download_yfinance(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError("yfinance가 필요합니다: pip install -r requirements.txt") from exc

    df = yf.download(symbol, start=start, end=end, auto_adjust=False, progress=False)
    if df.empty:
        raise ValueError(f"해당 종목의 데이터를 불러오지 못했습니다: symbol={symbol!r}")

    # yfinance는 단일 티커에서도 MultiIndex 열을 반환할 수 있습니다.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df.sort_index()
