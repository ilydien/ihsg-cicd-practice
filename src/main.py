"""Orkestrator pipeline: unduh, bersihkan, validasi, lalu simpan."""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import UTC, datetime

from src.config import TICKERS, default_start_date
from src.ingestion import fetch_prices
from src.storage import save_csv, save_summary
from src.validation import clean, validate

LOGGER = logging.getLogger("ihsg")


def run(start: str | None = None) -> dict:
    """Jalankan seluruh pipeline dan kembalikan ringkasan eksekusi."""
    started_at = datetime.now(UTC)
    timer = time.perf_counter()
    start = start or default_start_date()

    LOGGER.info("Mulai ingestion IHSG (start=%s)", start)

    raw = fetch_prices(start=start)
    LOGGER.info("Data mentah: %s baris", len(raw))

    cleaned = clean(raw)
    validate(cleaned, expected_tickers=TICKERS)

    repaired_rows = int(cleaned.attrs.get("repaired_rows", 0))

    if repaired_rows:
        LOGGER.info("Baris OHLC yang diperbaiki: %s", repaired_rows)

    csv_path = save_csv(cleaned)

    summary = {
        "generated_at": started_at.isoformat(),
        "start_date": start,
        "raw_rows": len(raw),
        "rows": len(cleaned),
        "repaired_rows": repaired_rows,
        "tickers": sorted(cleaned["Ticker"].unique().tolist()),
        "first_date": str(cleaned["Date"].min()),
        "last_date": str(cleaned["Date"].max()),
        "output": str(csv_path),
        "duration_seconds": round(time.perf_counter() - timer, 2),
    }

    save_summary(summary)

    LOGGER.info("Selesai: %s baris -> %s", len(cleaned), csv_path)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pipeline ingestion data IHSG")
    parser.add_argument(
        "--start",
        default=None,
        help="Tanggal mulai (YYYY-MM-DD); default dua tahun ke belakang.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Level logging (default: INFO).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(message)s",
    )

    try:
        run(start=args.start)
    except Exception:  # noqa: BLE001 - exit code dipakai oleh CI/CD
        LOGGER.exception("Pipeline gagal")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
