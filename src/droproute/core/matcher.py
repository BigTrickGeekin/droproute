from __future__ import annotations

from pathlib import Path

from droproute.models import RouteDecision, Rule


class RuleMatcher:
    def __init__(self, rules: tuple[Rule, ...]) -> None:
        self._rules = rules

    def decide(self, source: Path) -> RouteDecision:
        filename_casefold = source.name.casefold()
        extension = source.suffix.casefold()

        for rule in self._rules:
            if not rule.enabled:
                continue
            if rule.extensions and extension not in rule.extensions:
                continue
            if rule.name_contains and not all(token in filename_casefold for token in rule.name_contains):
                continue
            return RouteDecision(source=source, matched_rule=rule, reason=f"Matched rule: {rule.name}")

        return RouteDecision(source=source, matched_rule=None, reason="No matching rule")
