from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from droproute.core.router import Router
from droproute.core.stability import FileStabilityChecker, is_temporary_download

logger = logging.getLogger(__name__)


class _EventHandler(FileSystemEventHandler):
    def __init__(self, stability_checker: FileStabilityChecker, router: Router) -> None:
        self._stability_checker = stability_checker
        self._router = router
        self._inflight: set[Path] = set()
        self._lock = threading.Lock()

    def on_created(self, event: FileSystemEvent) -> None:
        self._handle_event(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        self._handle_event(event)

    def _handle_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return

        source_path = Path(getattr(event, "dest_path", event.src_path))
        if is_temporary_download(source_path):
            return

        with self._lock:
            if source_path in self._inflight:
                return
            self._inflight.add(source_path)

        thread = threading.Thread(target=self._process_file, args=(source_path,), daemon=True)
        thread.start()

    def _process_file(self, source_path: Path) -> None:
        try:
            if self._stability_checker.wait_until_stable(source_path):
                self._router.route(source_path)
        finally:
            with self._lock:
                self._inflight.discard(source_path)


class FolderWatcher:
    def __init__(self, watch_paths: tuple[Path, ...], stability_checker: FileStabilityChecker, router: Router) -> None:
        self._watch_paths = watch_paths
        self._stability_checker = stability_checker
        self._router = router
        self._observer = Observer()

    def run_forever(self) -> None:
        handler = _EventHandler(self._stability_checker, self._router)

        for path in self._watch_paths:
            path.mkdir(parents=True, exist_ok=True)
            logger.info("Watching folder: %s", path)
            self._observer.schedule(handler, str(path), recursive=False)

        self._observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            self._observer.stop()
            self._observer.join()
