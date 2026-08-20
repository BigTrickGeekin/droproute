from pathlib import Path
from threading import Event

from droproute.core.stability import FileStabilityChecker, is_temporary_download


def test_temporary_download_detection() -> None:
    assert is_temporary_download(Path("file.crdownload")) is True
    assert is_temporary_download(Path("file.part")) is True
    assert is_temporary_download(Path("file.OPDOWNLOAD")) is True
    assert is_temporary_download(Path("file.partial")) is True
    assert is_temporary_download(Path("file.pdf")) is False


def test_stability_checker_accepts_stable_file(tmp_path: Path) -> None:
    source = tmp_path / "complete.txt"
    source.write_text("done", encoding="utf-8")
    checker = FileStabilityChecker(0.005, 0.01, 0.1)

    assert checker.wait_until_stable(source) is True


def test_stability_checker_rejects_missing_file(tmp_path: Path) -> None:
    checker = FileStabilityChecker(0.005, 0.01, 0.05)

    assert checker.wait_until_stable(tmp_path / "missing.txt") is False


def test_stability_checker_rejects_directory(tmp_path: Path) -> None:
    checker = FileStabilityChecker(0.005, 0.01, 0.02)

    assert checker.wait_until_stable(tmp_path) is False


def test_stability_checker_stops_when_cancelled(tmp_path: Path) -> None:
    source = tmp_path / "complete.txt"
    source.write_text("done", encoding="utf-8")
    stop_event = Event()
    stop_event.set()

    assert FileStabilityChecker(0.01, 0.02, 0.1).wait_until_stable(source, stop_event) is False
