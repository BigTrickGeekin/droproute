# DropRoute

DropRoute is a focused desktop utility that watches a folder, waits for files to finish downloading, and routes them to target folders based on deterministic rules.

## Scope

This project intentionally stays narrow:
- watch one or more folders
- detect when a file is stable and complete
- match rules by file extension and filename content
- move or copy files into destination folders
- avoid accidental overwrites
- log every decision

No AI classification. No browser extension. No cloud dependency.

## Core design goals

- reliable with partially written download files
- simple rule model
- future-ready package layout
- low-friction local deployment
- safe defaults

## Features in this scaffold

- JSON config
- CLI entrypoint
- folder watching via `watchdog`
- stability detection before routing
- priority-ordered rules
- extension and substring matching
- conflict policies: `rename`, `skip`, `overwrite`
- move or copy per rule
- structured logging
- unit tests for matcher, stability, and routing behavior

## Install

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## Quick start

1. Copy the sample config:

```powershell
Copy-Item .\config.example.json .\config.json
```

2. Edit `config.json`.

3. Run validation:

```powershell
droproute validate --config .\config.json
```

4. Start the watcher:

```powershell
droproute run --config .\config.json
```

## Example config

```json
{
  "watch_paths": [
    "C:/Users/User/Downloads"
  ],
  "poll_interval_seconds": 1.0,
  "stability_window_seconds": 3.0,
  "log_level": "INFO",
  "rules": [
    {
      "name": "CNC posts",
      "enabled": true,
      "priority": 10,
      "extensions": [".tap", ".nc"],
      "name_contains": [],
      "destination": "C:/TEN10/CNC/Posts",
      "action": "move",
      "on_conflict": "rename"
    },
    {
      "name": "Invoices",
      "enabled": true,
      "priority": 20,
      "extensions": [".pdf"],
      "name_contains": ["invoice", "receipt"],
      "destination": "C:/TEN10/Docs/Invoices",
      "action": "move",
      "on_conflict": "rename"
    }
  ]
}
```

## CLI

```powershell
droproute validate --config .\config.json
droproute run --config .\config.json
droproute route-once --config .\config.json --file C:\Users\User\Downloads\example.tap
```

## Windows packaging later

When you are ready to ship an `.exe`, package the CLI or a thin GUI shell around it with PyInstaller or Briefcase. The core routing engine should remain unchanged.

## Repo bootstrap

This connector cannot create a new GitHub repo directly, but the scaffold is ready to push.

```powershell
gh repo create BigTrickGeekin/droproute --public --source . --remote origin --push
```

Or if you already created the repo manually:

```powershell
git init
git branch -M main
git add .
git commit -m "Initial DropRoute scaffold"
git remote add origin https://github.com/BigTrickGeekin/droproute.git
git push -u origin main
```
