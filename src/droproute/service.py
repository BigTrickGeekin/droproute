from __future__ import annotations

from pathlib import Path

from droproute.config_loader import load_config
from droproute.core.matcher import RuleMatcher
from droproute.core.mover import FileMover
from droproute.core.router import Router
from droproute.core.stability import FileStabilityChecker
from droproute.core.watcher import FolderWatcher
from droproute.logging_setup import configure_logging


class DropRouteApp:
    def __init__(self, config_path: Path) -> None:
        self._config = load_config(config_path)
        configure_logging(self._config.log_level)
        matcher = RuleMatcher(self._config.rules)
        mover = FileMover()
        self._router = Router(matcher=matcher, mover=mover)
        self._stability_checker = FileStabilityChecker(
            poll_interval_seconds=self._config.poll_interval_seconds,
            stability_window_seconds=self._config.stability_window_seconds,
        )

    def run(self) -> None:
        watcher = FolderWatcher(
            watch_paths=self._config.watch_paths,
            stability_checker=self._stability_checker,
            router=self._router,
        )
        watcher.run_forever()

    def route_once(self, source: Path) -> str:
        if not self._stability_checker.wait_until_stable(source):
            return f"File not stable or no longer present: {source}"
        decision = self._router.route(source)
        return decision.reason
