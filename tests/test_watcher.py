from pathlib import Path
from threading import Event
from typing import Any

from droproute.core import watcher as watcher_module
from droproute.core.watcher import FolderWatcher, _EventHandler


class _RecordingHandler:
    def __init__(self) -> None:
        self.paths: list[Path] = []

    def submit(self, path: Path) -> bool:
        self.paths.append(path)
        return not path.name.endswith(".tmp")


def test_queue_existing_only_submits_files(tmp_path: Path) -> None:
    (tmp_path / "one.txt").write_text("1", encoding="utf-8")
    (tmp_path / "ignored.tmp").write_text("2", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    handler = _RecordingHandler()
    watcher = FolderWatcher(
        watch_paths=(tmp_path,),
        stability_checker=object(),  # type: ignore[arg-type]
        router=object(),  # type: ignore[arg-type]
        process_existing_on_startup=True,
        worker_count=1,
    )

    queued = watcher._queue_existing(handler)  # type: ignore[arg-type]

    assert queued == 1
    assert {path.name for path in handler.paths} == {"one.txt", "ignored.tmp"}


class _BlockingChecker:
    def __init__(self) -> None:
        self.release = Event()

    def wait_until_stable(self, path: Path, stop_event: Event | None = None) -> bool:
        self.release.wait(timeout=0.2)
        return not (stop_event and stop_event.is_set())


class _RecordingRouter:
    def __init__(self) -> None:
        self.paths: list[Path] = []
        self.called = Event()

    def route(self, path: Path) -> None:
        self.paths.append(path)
        self.called.set()


def test_event_handler_deduplicates_inflight_and_ignores_temporary_files(
    tmp_path: Path,
) -> None:
    checker = _BlockingChecker()
    router = _RecordingRouter()
    handler = _EventHandler(checker, router, worker_count=1)  # type: ignore[arg-type]
    source = tmp_path / "file.txt"
    source.write_text("data", encoding="utf-8")

    assert handler.submit(source) is True
    assert handler.submit(source) is False
    assert handler.submit(tmp_path / "partial.crdownload") is False
    checker.release.set()
    assert router.called.wait(timeout=0.2)
    handler.close()

    assert router.paths == [source]


class _FakeObserver:
    def __init__(self) -> None:
        self.scheduled: list[tuple[str, bool]] = []
        self.started = False
        self.stopped = False
        self.joined = False

    def schedule(self, handler: Any, path: str, recursive: bool) -> None:
        self.scheduled.append((path, recursive))

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def join(self) -> None:
        self.joined = True


class _ImmediateChecker:
    def wait_until_stable(self, path: Path, stop_event: Event | None = None) -> bool:
        return path.exists() and not (stop_event and stop_event.is_set())


def test_run_forever_starts_scans_and_stops_cleanly(tmp_path: Path, monkeypatch: Any) -> None:
    watch_path = tmp_path / "incoming"
    watch_path.mkdir()
    source = watch_path / "existing.txt"
    source.write_text("data", encoding="utf-8")
    router = _RecordingRouter()
    fake_observer = _FakeObserver()
    watcher = FolderWatcher(
        watch_paths=(watch_path,),
        stability_checker=_ImmediateChecker(),  # type: ignore[arg-type]
        router=router,  # type: ignore[arg-type]
        process_existing_on_startup=True,
        worker_count=1,
    )
    watcher._observer = fake_observer  # type: ignore[assignment]

    def interrupt(_: float) -> None:
        assert router.called.wait(timeout=0.2)
        raise KeyboardInterrupt

    monkeypatch.setattr(watcher_module.time, "sleep", interrupt)

    watcher.run_forever()

    assert fake_observer.scheduled == [(str(watch_path), False)]
    assert fake_observer.started is True
    assert fake_observer.stopped is True
    assert fake_observer.joined is True
    assert router.paths == [source]
