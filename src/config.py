"""Konfigurasi pipeline: instrumen, rentang data, dan lokasi output."""

from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

# IHSG sebagai target + variabel eksternal yang dipakai di final project.
TICKERS: dict[str, str] = {
    "^JKSE": "IHSG",
    "GC=F": "Gold Futures",
    "CL=F": "Crude Oil WTI Futures",
    "IDR=X": "USD/IDR",
    "^HSI": "Hang Seng Index",
    "^N225": "Nikkei 225",
    "^DJI": "Dow Jones Industrial Average",
    "EEM": "iShares MSCI Emerging Markets ETF",
}

DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "ihsg.csv"
SUMMARY_PATH = DATA_DIR / "summary.json"


def default_start_date() -> str:
    """Tanggal mulai default: dua tahun ke belakang.

    Bisa dioverride lewat environment ``START_DATE`` (format ``YYYY-MM-DD``)
    atau argumen ``--start`` saat menjalankan pipeline.
    """
    raw = os.getenv("START_DATE", "").strip()

    if raw:
        return raw

    return (date.today() - timedelta(days=730)).isoformat()
