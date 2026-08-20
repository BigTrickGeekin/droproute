import json
from pathlib import Path

import pytest

from droproute.config_loader import ConfigError, load_config


def _config() -> dict[str, object]:
    return {
        "watch_paths": ["incoming"],
        "poll_interval_seconds": 0.01,
        "stability_window_seconds": 0.02,
        "max_wait_seconds": 0.1,
        "process_existing_on_startup": True,
        "worker_count": 2,
        "log_level": "INFO",
        "rules": [
            {
                "name": "Documents",
                "enabled": True,
                "priority": 10,
                "extensions": ["PDF"],
                "name_contains": [],
                "destination": "sorted/documents",
                "action": "move",
                "on_conflict": "rename",
            }
        ],
    }


def _write_config(tmp_path: Path, value: object) -> Path:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(value), encoding="utf-8")
    return config_path


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


def test_load_config_applies_defaults_and_resolves_relative_paths(tmp_path: Path) -> None:
    raw = _config()
    raw.pop("max_wait_seconds")
    raw.pop("process_existing_on_startup")
    raw.pop("worker_count")

    config = load_config(_write_config(tmp_path, raw))

    assert config.watch_paths == ((tmp_path / "incoming").resolve(),)
    assert config.rules[0].destination == (tmp_path / "sorted/documents").resolve()
    assert config.rules[0].extensions == (".pdf",)
    assert config.max_wait_seconds == 300
    assert config.process_existing_on_startup is True
    assert config.worker_count == 4


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("poll_interval_seconds", True, "must be a number"),
        ("stability_window_seconds", 0, "must be > 0"),
        ("max_wait_seconds", 0.001, "must be >= stability_window_seconds"),
        ("process_existing_on_startup", "yes", "must be a boolean"),
        ("worker_count", 0, "must be between 1 and 32"),
        ("worker_count", True, "must be an integer"),
        ("log_level", "TRACE", "must be one of"),
    ],
)
def test_load_config_rejects_invalid_app_fields(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    raw = _config()
    raw[field] = value

    with pytest.raises(ConfigError, match=message):
        load_config(_write_config(tmp_path, raw))


def test_load_config_rejects_duplicate_rule_names(tmp_path: Path) -> None:
    raw = _config()
    first_rule = raw["rules"][0]  # type: ignore[index]
    raw["rules"] = [first_rule, {**first_rule, "name": "documents", "priority": 20}]  # type: ignore[arg-type]

    with pytest.raises(ConfigError, match="Rule names must be unique"):
        load_config(_write_config(tmp_path, raw))


def test_load_config_rejects_watched_folder_as_destination(tmp_path: Path) -> None:
    raw = _config()
    raw["rules"][0]["destination"] = "incoming"  # type: ignore[index]

    with pytest.raises(ConfigError, match="destination cannot equal a watched folder"):
        load_config(_write_config(tmp_path, raw))


def test_load_config_reports_invalid_json(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text("{", encoding="utf-8")

    with pytest.raises(ConfigError, match="Invalid JSON"):
        load_config(config_path)


def test_load_config_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Config file not found"):
        load_config(tmp_path / "missing.json")
