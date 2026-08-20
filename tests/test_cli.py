import json
from pathlib import Path
from typing import Any

from droproute.cli import main


def _write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "watch_paths": ["incoming"],
                "poll_interval_seconds": 0.005,
                "stability_window_seconds": 0.01,
                "max_wait_seconds": 0.1,
                "worker_count": 1,
                "process_existing_on_startup": True,
                "log_level": "INFO",
                "rules": [
                    {
                        "name": "Text",
                        "enabled": True,
                        "priority": 10,
                        "extensions": ["txt"],
                        "name_contains": [],
                        "destination": "out",
                        "action": "move",
                        "on_conflict": "rename",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return config_path


def test_validate_command_reports_resolved_config(tmp_path: Path, capsys: Any) -> None:
    result = main(["validate", "--config", str(_write_config(tmp_path))])

    assert result == 0
    assert "Config valid" in capsys.readouterr().out


def test_validate_command_returns_nonzero_for_bad_config(tmp_path: Path, capsys: Any) -> None:
    config_path = tmp_path / "bad.json"
    config_path.write_text("{}", encoding="utf-8")

    result = main(["validate", "--config", str(config_path)])

    assert result == 2
    assert "Configuration error" in capsys.readouterr().out


def test_route_once_moves_file(tmp_path: Path, capsys: Any) -> None:
    source = tmp_path / "example.TXT"
    source.write_text("data", encoding="utf-8")

    result = main(
        [
            "route-once",
            "--config",
            str(_write_config(tmp_path)),
            "--file",
            str(source),
        ]
    )

    assert result == 0
    assert not source.exists()
    assert (tmp_path / "out/example.TXT").exists()
    assert "Routed to" in capsys.readouterr().out


def test_route_once_returns_nonzero_for_missing_file(tmp_path: Path) -> None:
    result = main(
        [
            "route-once",
            "--config",
            str(_write_config(tmp_path)),
            "--file",
            str(tmp_path / "missing.txt"),
        ]
    )

    assert result == 1
