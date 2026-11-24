"""Tes penyimpanan CSV dan ringkasan JSON."""

from __future__ import annotations

import json

import pandas as pd

from src.storage import save_csv, save_summary


def make_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": ["2026-01-02"],
            "Open": [100.0],
            "High": [105.0],
            "Low": [99.0],
            "Close": [104.0],
            "Adj Close": [104.0],
            "Volume": [1000],
            "Ticker": ["^JKSE"],
            "Instrument": ["IHSG"],
        }
    )


def test_save_csv_menulis_file_yang_bisa_dibaca_ulang(tmp_path) -> None:
    path = save_csv(make_frame(), tmp_path / "ihsg.csv")

    assert path.is_file()

    result = pd.read_csv(path)

    assert len(result) == 1
    assert result.loc[0, "Ticker"] == "^JKSE"


def test_save_summary_menulis_json(tmp_path) -> None:
    path = save_summary({"rows": 1, "tickers": ["^JKSE"]}, tmp_path / "summary.json")

    assert path.is_file()

    result = json.loads(path.read_text(encoding="utf-8"))

    assert result["rows"] == 1
    assert result["tickers"] == ["^JKSE"]
