from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(level: str) -> None:
    runtime_dir = Path("runtime")
    runtime_dir.mkdir(parents=True, exist_ok=True)
    log_path = runtime_dir / "droproute.log"

    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
        force=True,
    )
