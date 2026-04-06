from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from droproute.models import AppConfig, Rule


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

    if not isinstance(raw, dict):
        raise ConfigError("Config root must be a JSON object")

    watch_paths = _parse_watch_paths(raw.get("watch_paths"))
    poll_interval_seconds = _parse_positive_float(raw.get("poll_interval_seconds"), "poll_interval_seconds")
    stability_window_seconds = _parse_positive_float(
        raw.get("stability_window_seconds"), "stability_window_seconds"
    )
    log_level = _parse_log_level(raw.get("log_level"))
    rules = _parse_rules(raw.get("rules"))

    return AppConfig(
        watch_paths=watch_paths,
        poll_interval_seconds=poll_interval_seconds,
        stability_window_seconds=stability_window_seconds,
        log_level=log_level,
        rules=tuple(sorted(rules, key=lambda item: item.priority)),
    )


def _parse_watch_paths(value: Any) -> tuple[Path, ...]:
    if not isinstance(value, list) or not value:
        raise ConfigError("watch_paths must be a non-empty array")
    paths = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ConfigError("Each watch path must be a non-empty string")
        paths.append(Path(item))
    return tuple(paths)


def _parse_positive_float(value: Any, field_name: str) -> float:
    if not isinstance(value, (int, float)):
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


def _parse_rules(value: Any) -> tuple[Rule, ...]:
    if not isinstance(value, list) or not value:
        raise ConfigError("rules must be a non-empty array")

    rules = []
    for idx, raw_rule in enumerate(value, start=1):
        if not isinstance(raw_rule, dict):
            raise ConfigError(f"Rule #{idx} must be an object")
        missing = _REQUIRED_RULE_FIELDS - raw_rule.keys()
        if missing:
            raise ConfigError(f"Rule #{idx} missing fields: {sorted(missing)}")
        rules.append(_parse_rule(cast(dict[str, Any], raw_rule), idx))
    return tuple(rules)


def _parse_rule(raw_rule: dict[str, Any], idx: int) -> Rule:
    name = _require_str(raw_rule["name"], f"rules[{idx}].name")
    enabled = _require_bool(raw_rule["enabled"], f"rules[{idx}].enabled")
    priority = _require_int(raw_rule["priority"], f"rules[{idx}].priority")
    extensions = _parse_str_list(raw_rule["extensions"], f"rules[{idx}].extensions")
    name_contains = _parse_str_list(raw_rule["name_contains"], f"rules[{idx}].name_contains")
    destination = Path(_require_str(raw_rule["destination"], f"rules[{idx}].destination"))
    action = _require_enum(raw_rule["action"], f"rules[{idx}].action", {"move", "copy"})
    on_conflict = _require_enum(
        raw_rule["on_conflict"], f"rules[{idx}].on_conflict", {"rename", "skip", "overwrite"}
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
    return value if value.startswith(".") else f".{value}".casefold()


def _require_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"{field_name} must be a boolean")
    return value


def _require_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int):
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
