from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from droproute import __version__
from droproute.config_loader import ConfigError, load_config
from droproute.service import DropRouteApp


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="droproute", description="Route completed downloads by deterministic rule"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.add_argument("--config", required=True, type=Path)

    run_parser = subparsers.add_parser("run", help="Run folder watcher")
    run_parser.add_argument("--config", required=True, type=Path)

    once_parser = subparsers.add_parser("route-once", help="Route a single file using the config")
    once_parser.add_argument("--config", required=True, type=Path)
    once_parser.add_argument("--file", required=True, type=Path)

    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            _validate(args.config)
            return 0

        app = DropRouteApp(config_path=args.config)
        if args.command == "run":
            app.run()
            return 0
        if args.command == "route-once":
            decision = app.route_once(args.file)
            print(decision.reason)
            return 1 if decision.status == "failed" else 0
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 2

    parser.error("Unsupported command")


def _validate(config_path: Path) -> None:
    config = load_config(config_path)

    print("Config valid")
    print(f"Watch paths: {len(config.watch_paths)}")
    print(f"Rules: {len(config.rules)}")
    print(f"Workers: {config.worker_count}")
    print(f"Maximum stability wait: {config.max_wait_seconds:g}s")


if __name__ == "__main__":
    raise SystemExit(main())
