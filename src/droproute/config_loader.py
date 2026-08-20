from __future__ import annotations

import json
import os
from pathlib import Path, PureWindowsPath
from typing import Any, cast

from droproute.models import Action, AppConfig, ConflictPolicy, Rule


class ConfigError(ValueError):
    pass


_REQUIRED_RULE_FIELDS = {
    "name",
    "enabled",
    "priority",
    "extensions",
    "name_contains",
    "destination",
    "action",
    "on_conflict",
}


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in config: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Unable to read config: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Config root must be a JSON object")

    base_dir = path.parent.resolve()
    watch_paths = _parse_watch_paths(raw.get("watch_paths"), base_dir)
    poll_interval_seconds = _parse_positive_float(
        raw.get("poll_interval_seconds"), "poll_interval_seconds"
    )
    stability_window_seconds = _parse_positive_float(
        raw.get("stability_window_seconds"), "stability_window_seconds"
    )
    max_wait_seconds = _parse_positive_float(raw.get("max_wait_seconds", 300), "max_wait_seconds")
    if max_wait_seconds < stability_window_seconds:
        raise ConfigError("max_wait_seconds must be >= stability_window_seconds")

    process_existing_on_startup = _require_bool(
        raw.get("process_existing_on_startup", True), "process_existing_on_startup"
    )
    worker_count = _parse_worker_count(raw.get("worker_count", 4))
    log_level = _parse_log_level(raw.get("log_level"))
    rules = _parse_rules(raw.get("rules"), base_dir)

    if len({_path_key(item) for item in watch_paths}) != len(watch_paths):
        raise ConfigError("watch_paths must not contain duplicates")
    watch_keys = {_path_key(item) for item in watch_paths}
    for rule in rules:
        if _path_key(rule.destination) in watch_keys:
            raise ConfigError(f"Rule '{rule.name}' destination cannot equal a watched folder")

    return AppConfig(
        watch_paths=watch_paths,
        poll_interval_seconds=poll_interval_seconds,
        stability_window_seconds=stability_window_seconds,
        max_wait_seconds=max_wait_seconds,
        process_existing_on_startup=process_existing_on_startup,
        worker_count=worker_count,
        log_level=log_level,
        rules=tuple(sorted(rules, key=lambda item: item.priority)),
    )


def _parse_watch_paths(value: Any, base_dir: Path) -> tuple[Path, ...]:
    if not isinstance(value, list) or not value:
        raise ConfigError("watch_paths must be a non-empty array")
    paths = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ConfigError("Each watch path must be a non-empty string")
        paths.append(_parse_path(item, base_dir))
    return tuple(paths)


def _parse_positive_float(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{field_name} must be a number")
    parsed = float(value)
    if parsed <= 0:
        raise ConfigError(f"{field_name} must be > 0")
    return parsed


def _parse_log_level(value: Any) -> str:
    if not isinstance(value, str):
        raise ConfigError("log_level must be a string")
    normalized = value.upper()
    allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if normalized not in allowed:
        raise ConfigError(f"log_level must be one of {sorted(allowed)}")
    return normalized


def _parse_rules(value: Any, base_dir: Path) -> tuple[Rule, ...]:
    if not isinstance(value, list) or not value:
        raise ConfigError("rules must be a non-empty array")

    rules = []
    for idx, raw_rule in enumerate(value, start=1):
        if not isinstance(raw_rule, dict):
            raise ConfigError(f"Rule #{idx} must be an object")
        missing = _REQUIRED_RULE_FIELDS - raw_rule.keys()
        if missing:
            raise ConfigError(f"Rule #{idx} missing fields: {sorted(missing)}")
        rules.append(_parse_rule(cast(dict[str, Any], raw_rule), idx, base_dir))

    normalized_names = [rule.name.casefold() for rule in rules]
    if len(set(normalized_names)) != len(normalized_names):
        raise ConfigError("Rule names must be unique (case-insensitive)")
    return tuple(rules)


def _parse_rule(raw_rule: dict[str, Any], idx: int, base_dir: Path) -> Rule:
    name = _require_str(raw_rule["name"], f"rules[{idx}].name")
    enabled = _require_bool(raw_rule["enabled"], f"rules[{idx}].enabled")
    priority = _require_int(raw_rule["priority"], f"rules[{idx}].priority")
    extensions = _parse_str_list(raw_rule["extensions"], f"rules[{idx}].extensions")
    name_contains = _parse_str_list(raw_rule["name_contains"], f"rules[{idx}].name_contains")
    destination = _parse_path(
        _require_str(raw_rule["destination"], f"rules[{idx}].destination"), base_dir
    )
    action = cast(
        Action,
        _require_enum(raw_rule["action"], f"rules[{idx}].action", {"move", "copy"}),
    )
    on_conflict = cast(
        ConflictPolicy,
        _require_enum(
            raw_rule["on_conflict"],
            f"rules[{idx}].on_conflict",
            {"rename", "skip", "overwrite"},
        ),
    )

    normalized_extensions = tuple(sorted({_normalize_extension(item) for item in extensions}))
    normalized_contains = tuple(item.casefold() for item in name_contains)

    return Rule(
        name=name,
        enabled=enabled,
        priority=priority,
        extensions=normalized_extensions,
        name_contains=normalized_contains,
        destination=destination,
        action=action,
        on_conflict=on_conflict,
    )


def _normalize_extension(value: str) -> str:
    normalized = value if value.startswith(".") else f".{value}"
    return normalized.casefold()


def _require_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"{field_name} must be a boolean")
    return value


def _require_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{field_name} must be an integer")
    return value


def _parse_str_list(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ConfigError(f"{field_name} must be an array")
    parsed = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ConfigError(f"{field_name} entries must be non-empty strings")
        parsed.append(item.strip())
    return tuple(parsed)


def _require_enum(value: Any, field_name: str, allowed: set[str]) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"{field_name} must be a string")
    normalized = value.strip().casefold()
    if normalized not in allowed:
        raise ConfigError(f"{field_name} must be one of {sorted(allowed)}")
    return normalized


def _parse_worker_count(value: Any) -> int:
    parsed = _require_int(value, "worker_count")
    if not 1 <= parsed <= 32:
        raise ConfigError("worker_count must be between 1 and 32")
    return parsed


def _parse_path(value: str, base_dir: Path) -> Path:
    expanded = os.path.expanduser(os.path.expandvars(value))
    parsed = Path(expanded)
    if parsed.is_absolute() or PureWindowsPath(expanded).is_absolute():
        return parsed
    return (base_dir / parsed).resolve()


def _path_key(path: Path) -> str:
    return os.path.normcase(os.path.abspath(path))
