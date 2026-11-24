"""Pembersihan dan pemeriksaan kualitas data sebelum disimpan."""

from __future__ import annotations

import logging

import pandas as pd

LOGGER = logging.getLogger(__name__)

REQUIRED_COLUMNS = (
    "Date",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "Ticker",
    "Instrument",
)
NUMERIC_COLUMNS = ("Open", "High", "Low", "Close", "Adj Close", "Volume")
KEY_COLUMNS = ("Date", "Ticker")

# Toleransi kecil untuk pembulatan harga dari Yahoo Finance.
PRICE_TOLERANCE = 1e-6


def _repair_price_range(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Lebarkan High/Low agar mencakup Open dan Close.

    Yahoo Finance (terutama ticker FX seperti ``IDR=X``) kadang mengembalikan
    Open/Close dari snapshot yang berbeda dengan High/Low harian. Secara
    definisi High tidak mungkin lebih rendah dari Open/Close, jadi rentangnya
    dilebarkan dan jumlah baris yang diperbaiki dikembalikan.
    """
    outside = (
        (frame["Open"] < frame["Low"] - PRICE_TOLERANCE)
        | (frame["Open"] > frame["High"] + PRICE_TOLERANCE)
        | (frame["Close"] < frame["Low"] - PRICE_TOLERANCE)
        | (frame["Close"] > frame["High"] + PRICE_TOLERANCE)
    )

    repaired = int(outside.sum())

    if not repaired:
        return frame, 0

    columns = ["Open", "High", "Low", "Close"]

    frame.loc[outside, "High"] = frame.loc[outside, columns].max(axis=1)
    frame.loc[outside, "Low"] = frame.loc[outside, columns].min(axis=1)

    tickers = ", ".join(sorted(frame.loc[outside, "Ticker"].unique()))
    LOGGER.warning(
        "Memperbaiki %s baris OHLC tidak konsisten (ticker: %s).",
        repaired,
        tickers,
    )

    return frame, repaired


def clean(data: pd.DataFrame) -> pd.DataFrame:
    """Rapikan data mentah: tipe, tanggal, rentang OHLC, duplikat, dan urutan."""
    if data is None or data.empty:
        return pd.DataFrame()

    frame = data.copy()

    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce").dt.strftime("%Y-%m-%d")

    for column in NUMERIC_COLUMNS:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.dropna(subset=[*KEY_COLUMNS, "Open", "High", "Low", "Close"])
    frame, repaired = _repair_price_range(frame)
    frame = frame.sort_values(list(KEY_COLUMNS))
    frame = frame.drop_duplicates(subset=list(KEY_COLUMNS), keep="last")
    frame = frame.reset_index(drop=True)

    # Disimpan untuk dilaporkan di summary.json.
    frame.attrs["repaired_rows"] = repaired

    return frame


def validate(data: pd.DataFrame, expected_tickers: dict[str, str] | None = None) -> None:
    """Pastikan data layak dipakai; lempar ``ValueError`` bila tidak."""
    if data is None or data.empty:
        raise ValueError("Data kosong: tidak ada baris untuk disimpan.")

    missing_columns = set(REQUIRED_COLUMNS) - set(data.columns)

    if missing_columns:
        raise ValueError(f"Kolom wajib tidak ada: {sorted(missing_columns)}")

    duplicates = int(data.duplicated(subset=list(KEY_COLUMNS)).sum())

    if duplicates:
        raise ValueError(f"Masih ada {duplicates} baris duplikat (Date, Ticker).")

    if data[["Open", "High", "Low", "Close"]].isna().any().any():
        raise ValueError("Harga Open/High/Low/Close masih mengandung nilai kosong.")

    invalid_range = data["High"] < data["Low"] - PRICE_TOLERANCE

    if invalid_range.any():
        raise ValueError(f"Ada {int(invalid_range.sum())} baris dengan High < Low.")

    close_outside = (data["Close"] < data["Low"] - PRICE_TOLERANCE) | (
        data["Close"] > data["High"] + PRICE_TOLERANCE
    )

    if close_outside.any():
        raise ValueError(f"Ada {int(close_outside.sum())} baris dengan Close di luar Low-High.")

    negative_volume = data["Volume"] < 0

    if negative_volume.any():
        raise ValueError(f"Ada {int(negative_volume.sum())} baris dengan Volume negatif.")

    if expected_tickers:
        missing_tickers = sorted(set(expected_tickers) - set(data["Ticker"]))

        if missing_tickers:
            raise ValueError(f"Ticker tidak lengkap: {missing_tickers}")
