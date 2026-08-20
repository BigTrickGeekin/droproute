from __future__ import annotations

from pathlib import Path

from droproute.config_loader import load_config
from droproute.core.matcher import RuleMatcher
from droproute.core.mover import FileMover
from droproute.core.router import Router
from droproute.core.stability import FileStabilityChecker
from droproute.core.watcher import FolderWatcher
from droproute.logging_setup import configure_logging
from droproute.models import RouteDecision


class DropRouteApp:
    def __init__(self, config_path: Path) -> None:
        self._config = load_config(config_path)
        configure_logging(self._config.log_level, config_path.parent / "runtime")
        matcher = RuleMatcher(self._config.rules)
        mover = FileMover()
        self._router = Router(matcher=matcher, mover=mover)
        self._stability_checker = FileStabilityChecker(
            poll_interval_seconds=self._config.poll_interval_seconds,
            stability_window_seconds=self._config.stability_window_seconds,
            max_wait_seconds=self._config.max_wait_seconds,
        )

    def run(self) -> None:
        watcher = FolderWatcher(
            watch_paths=self._config.watch_paths,
            stability_checker=self._stability_checker,
            router=self._router,
            process_existing_on_startup=self._config.process_existing_on_startup,
            worker_count=self._config.worker_count,
        )
        watcher.run_forever()

    def route_once(self, source: Path) -> RouteDecision:
        if not self._stability_checker.wait_until_stable(source):
            return RouteDecision(
                source=source,
                matched_rule=None,
                reason=f"File not stable, not readable, or no longer present: {source}",
                status="failed",
            )
        return self._router.route(source)
