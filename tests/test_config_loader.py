import json
from pathlib import Path

from droproute.config_loader import load_config


def test_load_config_sorts_rules_by_priority(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "watch_paths": ["C:/Users/User/Downloads"],
                "poll_interval_seconds": 1,
                "stability_window_seconds": 2,
                "log_level": "INFO",
                "rules": [
                    {
                        "name": "B",
                        "enabled": True,
                        "priority": 20,
                        "extensions": [".pdf"],
                        "name_contains": [],
                        "destination": "C:/B",
                        "action": "move",
                        "on_conflict": "rename",
                    },
                    {
                        "name": "A",
                        "enabled": True,
                        "priority": 10,
                        "extensions": [".tap"],
                        "name_contains": [],
                        "destination": "C:/A",
                        "action": "move",
                        "on_conflict": "rename",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.rules[0].name == "A"
    assert config.rules[1].name == "B"
