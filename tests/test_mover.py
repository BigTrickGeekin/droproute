from pathlib import Path

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
