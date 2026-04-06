from __future__ import annotations

import logging
from pathlib import Path

from droproute.core.matcher import RuleMatcher
from droproute.core.mover import FileMoveError, FileMover
from droproute.models import RouteDecision

logger = logging.getLogger(__name__)


class Router:
    def __init__(self, matcher: RuleMatcher, mover: FileMover) -> None:
        self._matcher = matcher
        self._mover = mover

    def route(self, source: Path) -> RouteDecision:
        decision = self._matcher.decide(source)
        if decision.matched_rule is None:
            logger.info("No rule matched for %s", source)
            return decision

        rule = decision.matched_rule
        try:
            target = self._mover.execute(
                source=source,
                destination_dir=rule.destination,
                action=rule.action,
                on_conflict=rule.on_conflict,
            )
        except FileMoveError as exc:
            logger.warning("Routing skipped for %s: %s", source, exc)
            return RouteDecision(source=source, matched_rule=rule, reason=str(exc))

        logger.info("Routed %s -> %s using rule '%s'", source, target, rule.name)
        return RouteDecision(source=target, matched_rule=rule, reason=f"Routed to {target}")
