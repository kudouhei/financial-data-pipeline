from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"


@dataclass(frozen=True)
class PipelineConfig:
    """Runtime configuration for local files and optional PostgreSQL loading."""

    raw_data_dir: Path = RAW_DATA_DIR
    processed_data_dir: Path = PROCESSED_DATA_DIR
    reports_dir: Path = REPORTS_DIR
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://pipeline:pipeline@localhost:5432/financial_data",
    )
    as_of_date: str = os.getenv("AS_OF_DATE", "2024-02-29")


def ensure_output_dirs(config: PipelineConfig) -> None:
    config.processed_data_dir.mkdir(parents=True, exist_ok=True)
    config.reports_dir.mkdir(parents=True, exist_ok=True)
