from pathlib import Path

from droproute.core.matcher import RuleMatcher
from droproute.models import Rule


def test_matcher_matches_extension_and_contains() -> None:
    rules = (
        Rule(
            name="Invoices",
            enabled=True,
            priority=10,
            extensions=(".pdf",),
            name_contains=("invoice",),
            destination=Path("C:/Out"),
            action="move",
            on_conflict="rename",
        ),
    )
    matcher = RuleMatcher(rules)

    decision = matcher.decide(Path("customer-invoice.pdf"))

    assert decision.matched_rule is not None
    assert decision.matched_rule.name == "Invoices"
