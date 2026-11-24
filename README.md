# IHSG Data Ingestion Pipeline

Pipeline ingestion data harian IHSG dan variabel eksternal dari Yahoo Finance,
disiapkan untuk dijalankan otomatis oleh GitHub Actions dan disimpan ke Azure
Blob Storage.

## Instrumen

| Ticker | Instrumen |
|---|---|
| `^JKSE` | IHSG (target) |
| `GC=F` | Gold Futures |
| `CL=F` | Crude Oil WTI Futures |
| `IDR=X` | USD/IDR |
| `^HSI` | Hang Seng Index |
| `^N225` | Nikkei 225 |
| `^DJI` | Dow Jones Industrial Average |
| `EEM` | iShares MSCI Emerging Markets ETF |

## Struktur proyek

```text
.
├── src/
│   ├── config.py       konfigurasi: ticker, tanggal mulai, lokasi output
│   ├── ingestion.py    unduh data mentah dari Yahoo Finance
│   ├── validation.py   bersihkan dan periksa kualitas data
│   ├── storage.py      tulis CSV dan summary.json secara atomik
│   └── main.py         orkestrator + CLI + exit code
├── tests/
│   ├── test_validation.py
│   └── test_storage.py
├── data/               output lokal (tidak di-commit)
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

## Menjalankan pipeline

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# default: dua tahun terakhir
python -m src.main

# rentang tertentu
python -m src.main --start 2024-01-01
```

Output:

```text
data/
├── ihsg.csv
└── summary.json
```

`ihsg.csv` berisi kolom `Date`, `Open`, `High`, `Low`, `Close`, `Adj Close`,
`Volume`, `Ticker`, dan `Instrument`. `summary.json` mencatat waktu eksekusi,
jumlah baris, daftar ticker, rentang tanggal, dan durasi.

## Menjalankan tes

```bash
pytest -v
ruff check .
```

## Catatan

- Pipeline tidak memakai jaringan saat tes; `yfinance` hanya dipanggil saat
  `python -m src.main` dijalankan.
- Exit code `0` berarti sukses dan `1` berarti gagal, sehingga bisa dipakai
  langsung oleh workflow CI/CD.
- Upload ke Azure Blob Storage dilakukan oleh workflow, bukan oleh kode Python.
- Ticker FX (`IDR=X`) dari Yahoo kadang punya `Open`/`Close` di luar rentang
  `High`/`Low` harian. Baris seperti itu diperbaiki dengan melebarkan
  `High`/`Low` agar mencakup `Open` dan `Close`, lalu jumlahnya dicatat di
  `repaired_rows` pada `summary.json`.

