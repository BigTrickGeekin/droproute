from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Action = Literal["move", "copy"]
ConflictPolicy = Literal["rename", "skip", "overwrite"]


@dataclass(frozen=True, slots=True)
class Rule:
    name: str
    enabled: bool
    priority: int
    extensions: tuple[str, ...]
    name_contains: tuple[str, ...]
    destination: Path
    action: Action
    on_conflict: ConflictPolicy


@dataclass(frozen=True, slots=True)
class AppConfig:
    watch_paths: tuple[Path, ...]
    poll_interval_seconds: float
    stability_window_seconds: float
    log_level: str
    rules: tuple[Rule, ...]


@dataclass(frozen=True, slots=True)
class RouteDecision:
    source: Path
    matched_rule: Rule | None
    reason: str
