from __future__ import annotations

import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from droproute.core.router import Router
from droproute.core.stability import FileStabilityChecker, is_temporary_download

logger = logging.getLogger(__name__)


class _EventHandler(FileSystemEventHandler):
    def __init__(
        self,
        stability_checker: FileStabilityChecker,
        router: Router,
        worker_count: int,
    ) -> None:
        self._stability_checker = stability_checker
        self._router = router
        self._inflight: set[Path] = set()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._executor = ThreadPoolExecutor(
            max_workers=worker_count, thread_name_prefix="droproute"
        )

    def on_created(self, event: FileSystemEvent) -> None:
        self._handle_event(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        self._handle_event(event)

    def _handle_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return

        event_path = getattr(event, "dest_path", event.src_path)
        source_path = Path(os.fsdecode(event_path))
        self.submit(source_path)

    def submit(self, source_path: Path) -> bool:
        source_path = _normalized_path(source_path)
        if is_temporary_download(source_path):
            return False

        with self._lock:
            if source_path in self._inflight:
                return False
            self._inflight.add(source_path)

        self._executor.submit(self._process_file, source_path)
        return True

    def _process_file(self, source_path: Path) -> None:
        try:
            if self._stability_checker.wait_until_stable(source_path, self._stop_event):
                self._router.route(source_path)
        finally:
            with self._lock:
                self._inflight.discard(source_path)

    def close(self) -> None:
        self._stop_event.set()
        self._executor.shutdown(wait=True, cancel_futures=True)


class FolderWatcher:
    def __init__(
        self,
        watch_paths: tuple[Path, ...],
        stability_checker: FileStabilityChecker,
        router: Router,
        process_existing_on_startup: bool,
        worker_count: int,
    ) -> None:
        self._watch_paths = watch_paths
        self._stability_checker = stability_checker
        self._router = router
        self._process_existing_on_startup = process_existing_on_startup
        self._worker_count = worker_count
        self._observer = Observer()

    def run_forever(self) -> None:
        handler = _EventHandler(
            self._stability_checker,
            self._router,
            worker_count=self._worker_count,
        )

        for path in self._watch_paths:
            path.mkdir(parents=True, exist_ok=True)
            logger.info("Watching folder: %s", path)
            self._observer.schedule(handler, str(path), recursive=False)

        self._observer.start()
        if self._process_existing_on_startup:
            queued = self._queue_existing(handler)
            logger.info("Queued %d existing file(s) at startup", queued)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            self._observer.stop()
            self._observer.join()
            handler.close()

    def _queue_existing(self, handler: _EventHandler) -> int:
        queued = 0
        for watch_path in self._watch_paths:
            for candidate in watch_path.iterdir():
                if candidate.is_file() and handler.submit(candidate):
                    queued += 1
        return queued


def _normalized_path(path: Path) -> Path:
    return Path(os.path.normcase(os.path.abspath(path)))
