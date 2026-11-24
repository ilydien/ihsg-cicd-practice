"""Pengambilan data harga dari Yahoo Finance lewat ``yfinance``."""

from __future__ import annotations

import logging
import time

import pandas as pd
import yfinance as yf

from src.config import TICKERS, default_start_date

LOGGER = logging.getLogger(__name__)

PRICE_COLUMNS = ("Open", "High", "Low", "Close", "Adj Close", "Volume")


def _extract(raw: pd.DataFrame, symbol: str, single: bool) -> pd.DataFrame:
    """Ambil satu ticker dari hasil ``yf.download`` multi-ticker."""
    if raw is None or raw.empty:
        return pd.DataFrame()

    if single:
        data = raw.copy()
        if isinstance(raw.columns, pd.MultiIndex) and symbol in raw.columns.get_level_values(0):
            data = raw[symbol].copy()
    elif isinstance(raw.columns, pd.MultiIndex):
        if symbol in raw.columns.get_level_values(0):
            data = raw[symbol].copy()
        elif symbol in raw.columns.get_level_values(1):
            data = raw.xs(symbol, axis=1, level=1).copy()
        else:
            return pd.DataFrame()
    else:
        data = raw.copy()

    data = data.reset_index()
    data = data.rename(columns={data.columns[0]: "Date"})

    return data


def fetch_prices(
    tickers: dict[str, str] | None = None,
    start: str | None = None,
    retries: int = 2,
) -> pd.DataFrame:
    """Unduh data harian semua ticker dan gabungkan menjadi satu DataFrame.

    Kolom hasil: ``Date``, ``Open``, ``High``, ``Low``, ``Close``,
    ``Adj Close``, ``Volume``, ``Ticker``, dan ``Instrument``.
    """
    tickers = tickers or TICKERS
    start = start or default_start_date()
    symbols = list(tickers)

    LOGGER.info("Mengunduh %s ticker sejak %s", len(symbols), start)

    raw: pd.DataFrame | None = None

    for attempt in range(1, retries + 1):
        try:
            raw = yf.download(
                symbols,
                start=start,
                progress=False,
                auto_adjust=False,
                group_by="ticker",
                threads=True,
            )
            break
        except Exception as error:  # noqa: BLE001 - dicoba ulang lalu dilempar
            LOGGER.warning("Percobaan %s gagal: %s", attempt, error)

            if attempt == retries:
                raise RuntimeError(f"Gagal mengunduh data: {error}") from error

            time.sleep(2 * attempt)

    if raw is None or raw.empty:
        raise RuntimeError("Yahoo Finance tidak mengembalikan data.")

    single = len(symbols) == 1
    frames: list[pd.DataFrame] = []

    for symbol, label in tickers.items():
        data = _extract(raw, symbol, single)

        if data.empty:
            LOGGER.warning("Ticker %s tidak memiliki data, dilewati.", symbol)
            continue

        for column in PRICE_COLUMNS:
            if column not in data.columns:
                data[column] = pd.NA

        # Beberapa emiten tidak punya Adj Close; pakai Close sebagai pengganti.
        if data["Adj Close"].isna().all():
            data["Adj Close"] = data["Close"]

        data["Ticker"] = symbol
        data["Instrument"] = label
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")

        frames.append(data[["Date", *PRICE_COLUMNS, "Ticker", "Instrument"]])

    if not frames:
        raise RuntimeError("Tidak ada ticker yang berhasil diunduh.")

    return pd.concat(frames, ignore_index=True)
