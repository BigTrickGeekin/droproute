from __future__ import annotations

import time
from pathlib import Path


class FileStabilityChecker:
    def __init__(self, poll_interval_seconds: float, stability_window_seconds: float) -> None:
        self._poll_interval_seconds = poll_interval_seconds
        self._stability_window_seconds = stability_window_seconds

    def wait_until_stable(self, path: Path) -> bool:
        stable_elapsed = 0.0
        last_signature: tuple[int, int] | None = None

        while True:
            if not path.exists():
                return False

            current_signature = self._read_signature(path)
            if current_signature is None:
                time.sleep(self._poll_interval_seconds)
                continue

            if current_signature == last_signature:
                stable_elapsed += self._poll_interval_seconds
                if stable_elapsed >= self._stability_window_seconds:
                    return True
            else:
                stable_elapsed = 0.0
                last_signature = current_signature

            time.sleep(self._poll_interval_seconds)

    @staticmethod
    def _read_signature(path: Path) -> tuple[int, int] | None:
        try:
            stat = path.stat()
        except OSError:
            return None
        return stat.st_size, int(stat.st_mtime_ns)


def is_temporary_download(path: Path) -> bool:
    suffix = path.suffix.casefold()
    return suffix in {".crdownload", ".part", ".tmp"}
