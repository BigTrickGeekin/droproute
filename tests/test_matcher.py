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
    assert decision.status == "matched"


def test_matcher_is_case_insensitive_and_requires_all_name_tokens() -> None:
    rule = Rule(
        name="Paid invoices",
        enabled=True,
        priority=10,
        extensions=(".pdf",),
        name_contains=("invoice", "paid"),
        destination=Path("out"),
        action="copy",
        on_conflict="rename",
    )
    matcher = RuleMatcher((rule,))

    assert matcher.decide(Path("PAID-INVOICE.PDF")).status == "matched"
    assert matcher.decide(Path("invoice.pdf")).status == "unmatched"


def test_matcher_skips_disabled_rule() -> None:
    rule = Rule(
        name="Disabled",
        enabled=False,
        priority=10,
        extensions=(),
        name_contains=(),
        destination=Path("out"),
        action="move",
        on_conflict="rename",
    )

    decision = RuleMatcher((rule,)).decide(Path("anything.txt"))

    assert decision.matched_rule is None
    assert decision.status == "unmatched"
