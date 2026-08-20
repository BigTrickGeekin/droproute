from __future__ import annotations

import stat
import threading
import time
from pathlib import Path


class FileStabilityChecker:
    def __init__(
        self,
        poll_interval_seconds: float,
        stability_window_seconds: float,
        max_wait_seconds: float,
    ) -> None:
        self._poll_interval_seconds = poll_interval_seconds
        self._stability_window_seconds = stability_window_seconds
        self._max_wait_seconds = max_wait_seconds

    def wait_until_stable(self, path: Path, stop_event: threading.Event | None = None) -> bool:
        stable_elapsed = 0.0
        last_signature: tuple[int, int] | None = None
        deadline = time.monotonic() + self._max_wait_seconds

        while time.monotonic() < deadline:
            if stop_event is not None and stop_event.is_set():
                return False
            if not path.exists():
                return False

            current_signature = self._read_signature(path)
            if current_signature is None:
                if _wait(self._poll_interval_seconds, stop_event):
                    return False
                continue

            if current_signature == last_signature:
                stable_elapsed += self._poll_interval_seconds
                if stable_elapsed >= self._stability_window_seconds:
                    return True
            else:
                stable_elapsed = 0.0
                last_signature = current_signature

            if _wait(self._poll_interval_seconds, stop_event):
                return False

        return False

    @staticmethod
    def _read_signature(path: Path) -> tuple[int, int] | None:
        try:
            file_stat = path.stat()
        except OSError:
            return None
        if not stat.S_ISREG(file_stat.st_mode):
            return None
        return file_stat.st_size, int(file_stat.st_mtime_ns)


def is_temporary_download(path: Path) -> bool:
    suffix = path.suffix.casefold()
    return suffix in {".crdownload", ".download", ".opdownload", ".part", ".partial", ".tmp"}


def _wait(seconds: float, stop_event: threading.Event | None) -> bool:
    if stop_event is None:
        time.sleep(seconds)
        return False
    return stop_event.wait(seconds)
