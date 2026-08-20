# DropRoute

DropRoute is a focused Windows-friendly utility that watches folders and routes completed files
using deterministic JSON rules. It is intended for downloads, CNC output, CAD exports, invoices,
and other local workflows where predictable behavior matters more than AI classification.

## MVP status

The `0.1.x` MVP supports:

- one or more non-recursive watch folders
- startup processing for files that already exist
- bounded background workers instead of one thread per event
- download-completion checks with a configurable timeout
- extension and filename-token matching in priority order
- move or copy actions
- `rename`, `skip`, and safe-replacement conflict policies
- relative paths resolved from the config file location
- environment variables and `~` in configured paths
- console and file logging
- a one-file Windows executable build

The MVP deliberately has no GUI, cloud service, browser extension, or AI classifier. Those are not
required to prove the routing engine.

## Requirements

- Windows 10 or 11 for the primary deployment target
- Python 3.11 or newer when running from source

## Install from source

```powershell
git clone https://github.com/BigTrickGeekin/droproute.git
Set-Location .\droproute
.\scripts\bootstrap.ps1
```

The bootstrap script creates `.venv`, installs DropRoute and its development checks, and creates
`config.json` from the example when needed.

## Configure

Edit `config.json`:

```json
{
  "watch_paths": ["%USERPROFILE%/Downloads"],
  "poll_interval_seconds": 1.0,
  "stability_window_seconds": 3.0,
  "max_wait_seconds": 300.0,
  "process_existing_on_startup": true,
  "worker_count": 4,
  "log_level": "INFO",
  "rules": [
    {
      "name": "CNC posts",
      "enabled": true,
      "priority": 10,
      "extensions": ["tap", "nc"],
      "name_contains": [],
      "destination": "C:/TEN10/CNC/Posts",
      "action": "move",
      "on_conflict": "rename"
    },
    {
      "name": "Invoices",
      "enabled": true,
      "priority": 20,
      "extensions": ["pdf"],
      "name_contains": ["invoice"],
      "destination": "sorted/invoices",
      "action": "copy",
      "on_conflict": "rename"
    }
  ]
}
```

Relative watch and destination paths are resolved from the folder containing `config.json`, not
from the current terminal directory. Rule names must be unique. A rule destination cannot be the
same folder it watches.

All entries in `name_contains` must occur in the filename. Leave both `extensions` and
`name_contains` empty only when an intentional catch-all rule is needed.

## Run

Validate before starting the watcher:

```powershell
droproute validate --config .\config.json
droproute run --config .\config.json
```

Route one file for setup verification:

```powershell
droproute route-once --config .\config.json --file "$env:USERPROFILE\Downloads\example.tap"
```

Runtime logs are written to `runtime/droproute.log` beside the selected config file. Stop the
watcher with `Ctrl+C`.

Exit codes are `0` for a successful command or unmatched file, `1` when a requested file cannot
be routed, and `2` for configuration or command errors.

## Build the Windows executable

```powershell
.\scripts\build_windows.ps1
```

The executable is written to `dist\DropRoute.exe`. GitHub Actions can build the same artifact using
the **Windows executable** workflow.

## Quality gate

```powershell
ruff format --check src tests
ruff check .
mypy
pytest --cov=droproute --cov-report=term-missing
```

CI enforces formatting, linting, strict type checks, the full test suite, and at least 85% combined
branch/line coverage.

## Known MVP limits

- watch folders are intentionally non-recursive
- configuration changes require a restart
- the executable is console-based
- network shares and locked files depend on Windows/filesystem behavior

## License

MIT. See `LICENSE`.
