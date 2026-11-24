"""Penyimpanan hasil pipeline ke disk secara atomik."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

from src.config import CSV_PATH, SUMMARY_PATH


def save_csv(data: pd.DataFrame, path: str | Path = CSV_PATH) -> Path:
    """Tulis hasil ke CSV lewat file sementara, lalu ganti secara atomik."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    temporary = destination.with_name(f"{destination.name}.tmp")
    data.to_csv(temporary, index=False)
    os.replace(temporary, destination)

    return destination


def save_summary(summary: dict, path: str | Path = SUMMARY_PATH) -> Path:
    """Tulis ringkasan eksekusi ke JSON secara atomik."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    temporary = destination.with_name(f"{destination.name}.tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())

    os.replace(temporary, destination)

    return destination
