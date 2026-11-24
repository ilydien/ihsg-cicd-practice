"""Tes pembersihan dan validasi data (tanpa jaringan)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.validation import clean, validate


def make_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": ["2026-01-02", "2026-01-02", "2026-01-05"],
            "Open": [100.0, 100.0, 101.0],
            "High": [105.0, 105.0, 106.0],
            "Low": [99.0, 99.0, 100.0],
            "Close": [104.0, 104.0, 105.0],
            "Adj Close": [104.0, 104.0, 105.0],
            "Volume": [1000, 1000, 1200],
            "Ticker": ["^JKSE", "^JKSE", "^JKSE"],
            "Instrument": ["IHSG", "IHSG", "IHSG"],
        }
    )


def test_clean_menghapus_duplikat() -> None:
    result = clean(make_frame())

    assert len(result) == 2
    assert result["Date"].tolist() == ["2026-01-02", "2026-01-05"]


def test_clean_mengembalikan_frame_kosong_untuk_input_kosong() -> None:
    assert clean(pd.DataFrame()).empty


def test_validate_menolak_data_kosong() -> None:
    with pytest.raises(ValueError, match="Data kosong"):
        validate(pd.DataFrame())


def test_validate_menolak_high_lebih_kecil_dari_low() -> None:
    frame = make_frame().drop_duplicates(subset=["Date", "Ticker"])
    frame.loc[frame.index[0], "High"] = 50.0

    with pytest.raises(ValueError, match="High < Low"):
        validate(frame)


def test_validate_menolak_ticker_yang_tidak_lengkap() -> None:
    frame = clean(make_frame())

    with pytest.raises(ValueError, match="Ticker tidak lengkap"):
        validate(frame, expected_tickers={"^JKSE": "IHSG", "GC=F": "Gold"})


def test_validate_menerima_data_yang_bersih() -> None:
    validate(clean(make_frame()), expected_tickers={"^JKSE": "IHSG"})


def test_clean_memperbaiki_close_di_atas_high() -> None:
    frame = clean(make_frame()).head(1).copy()
    frame.loc[0, "High"] = 103.0
    frame.loc[0, "Close"] = 104.0

    result = clean(frame)

    assert result.loc[0, "High"] == 104.0
    assert result.attrs["repaired_rows"] == 1


def test_clean_memperbaiki_open_di_bawah_low() -> None:
    frame = clean(make_frame()).head(1).copy()
    frame.loc[0, "Open"] = 90.0

    result = clean(frame)

    assert result.loc[0, "Low"] == 90.0
    assert result.attrs["repaired_rows"] == 1


def test_clean_tanpa_anomali_tidak_melaporkan_perbaikan() -> None:
    result = clean(make_frame())

    assert result.attrs["repaired_rows"] == 0
