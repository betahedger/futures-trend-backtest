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

    # Accept common lowercase column names.
    rename = {c: c.title() for c in df.columns if c.lower() in {"open", "high", "low", "close", "volume"}}
    return df.rename(columns=rename).sort_index()


def download_yfinance(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError("Install yfinance with: pip install -r requirements.txt") from exc

    df = yf.download(symbol, start=start, end=end, auto_adjust=False, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for symbol={symbol!r}")

    # yfinance can return a MultiIndex even for one ticker.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df.sort_index()
