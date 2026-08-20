from pathlib import Path

import pytest

from droproute.core.mover import FileMoveError, FileMover


def test_mover_renames_on_conflict(tmp_path: Path) -> None:
    source = tmp_path / "example.tap"
    source.write_text("data", encoding="utf-8")
    destination = tmp_path / "dest"
    destination.mkdir()
    (destination / "example.tap").write_text("existing", encoding="utf-8")

    moved = FileMover().execute(source, destination, action="move", on_conflict="rename")

    assert moved.name == "example (1).tap"
    assert moved.exists()


def test_mover_skip_raises(tmp_path: Path) -> None:
    source = tmp_path / "example.tap"
    source.write_text("data", encoding="utf-8")
    destination = tmp_path / "dest"
    destination.mkdir()
    (destination / "example.tap").write_text("existing", encoding="utf-8")

    try:
        FileMover().execute(source, destination, action="move", on_conflict="skip")
    except FileMoveError as exc:
        assert "skip" in str(exc)
    else:
        raise AssertionError("Expected FileMoveError")


def test_mover_copies_and_preserves_source(tmp_path: Path) -> None:
    source = tmp_path / "example.txt"
    source.write_text("new", encoding="utf-8")

    target = FileMover().execute(source, tmp_path / "dest", "copy", "rename")

    assert source.read_text(encoding="utf-8") == "new"
    assert target.read_text(encoding="utf-8") == "new"


def test_mover_overwrites_existing_file_without_predeleting_source(tmp_path: Path) -> None:
    source = tmp_path / "example.txt"
    source.write_text("new", encoding="utf-8")
    destination = tmp_path / "dest"
    destination.mkdir()
    (destination / source.name).write_text("old", encoding="utf-8")

    target = FileMover().execute(source, destination, "move", "overwrite")

    assert not source.exists()
    assert target.read_text(encoding="utf-8") == "new"


def test_mover_overwrite_copy_preserves_source(tmp_path: Path) -> None:
    source = tmp_path / "example.txt"
    source.write_text("new", encoding="utf-8")
    destination = tmp_path / "dest"
    destination.mkdir()
    (destination / source.name).write_text("old", encoding="utf-8")

    target = FileMover().execute(source, destination, "copy", "overwrite")

    assert source.read_text(encoding="utf-8") == "new"
    assert target.read_text(encoding="utf-8") == "new"


def test_mover_rejects_missing_source(tmp_path: Path) -> None:
    with pytest.raises(FileMoveError, match="not a readable file"):
        FileMover().execute(tmp_path / "missing", tmp_path / "dest", "move", "rename")


def test_mover_rejects_same_source_and_destination(tmp_path: Path) -> None:
    source = tmp_path / "example.txt"
    source.write_text("data", encoding="utf-8")

    with pytest.raises(FileMoveError, match="same file"):
        FileMover().execute(source, tmp_path, "move", "overwrite")
