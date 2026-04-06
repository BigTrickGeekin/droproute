from pathlib import Path

from droproute.core.stability import is_temporary_download


def test_temporary_download_detection() -> None:
    assert is_temporary_download(Path("file.crdownload")) is True
    assert is_temporary_download(Path("file.part")) is True
    assert is_temporary_download(Path("file.pdf")) is False
