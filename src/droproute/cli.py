from __future__ import annotations

import argparse
from pathlib import Path

from droproute.config_loader import ConfigError, load_config
from droproute.service import DropRouteApp


def main() -> None:
    parser = argparse.ArgumentParser(prog="droproute", description="Route completed downloads by rule")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.add_argument("--config", required=True, type=Path)

    run_parser = subparsers.add_parser("run", help="Run folder watcher")
    run_parser.add_argument("--config", required=True, type=Path)

    once_parser = subparsers.add_parser("route-once", help="Route a single file using the config")
    once_parser.add_argument("--config", required=True, type=Path)
    once_parser.add_argument("--file", required=True, type=Path)

    args = parser.parse_args()

    if args.command == "validate":
        _validate(args.config)
        return

    app = DropRouteApp(config_path=args.config)
    if args.command == "run":
        app.run()
        return
    if args.command == "route-once":
        print(app.route_once(args.file))
        return

    raise SystemExit("Unsupported command")


def _validate(config_path: Path) -> None:
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        raise SystemExit(f"Config validation failed: {exc}") from exc

    print("Config valid")
    print(f"Watch paths: {len(config.watch_paths)}")
    print(f"Rules: {len(config.rules)}")


if __name__ == "__main__":
    main()
