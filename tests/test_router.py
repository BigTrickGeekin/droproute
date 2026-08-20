from pathlib import Path

from droproute.core.matcher import RuleMatcher
from droproute.core.mover import FileMover
from droproute.core.router import Router
from droproute.models import ConflictPolicy, Rule


def _rule(destination: Path, conflict: ConflictPolicy = "rename") -> Rule:
    return Rule(
        name="Text",
        enabled=True,
        priority=10,
        extensions=(".txt",),
        name_contains=(),
        destination=destination,
        action="move",
        on_conflict=conflict,
    )


def test_router_routes_matching_file(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("data", encoding="utf-8")
    router = Router(RuleMatcher((_rule(tmp_path / "out"),)), FileMover())

    decision = router.route(source)

    assert decision.status == "routed"
    assert decision.target == tmp_path / "out/source.txt"
    assert decision.target.read_text(encoding="utf-8") == "data"


def test_router_leaves_unmatched_file_in_place(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    source.write_text("data", encoding="utf-8")
    router = Router(RuleMatcher((_rule(tmp_path / "out"),)), FileMover())

    decision = router.route(source)

    assert decision.status == "unmatched"
    assert source.exists()


def test_router_reports_conflict_failure(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("new", encoding="utf-8")
    destination = tmp_path / "out"
    destination.mkdir()
    (destination / source.name).write_text("old", encoding="utf-8")
    router = Router(RuleMatcher((_rule(destination, "skip"),)), FileMover())

    decision = router.route(source)

    assert decision.status == "failed"
    assert "skip" in decision.reason
    assert source.exists()
