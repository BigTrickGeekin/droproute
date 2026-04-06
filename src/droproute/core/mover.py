from __future__ import annotations

import shutil
from pathlib import Path

from droproute.models import ConflictPolicy


class FileMoveError(RuntimeError):
    pass


class FileMover:
    def execute(self, source: Path, destination_dir: Path, action: str, on_conflict: ConflictPolicy) -> Path:
        destination_dir.mkdir(parents=True, exist_ok=True)
        final_target = self._resolve_target(destination_dir / source.name, on_conflict)

        if final_target is None:
            raise FileMoveError(f"Conflict policy skip triggered for {source.name}")

        if action == "move":
            shutil.move(str(source), str(final_target))
        elif action == "copy":
            shutil.copy2(source, final_target)
        else:
            raise FileMoveError(f"Unsupported action: {action}")
        return final_target

    def _resolve_target(self, target: Path, on_conflict: ConflictPolicy) -> Path | None:
        if not target.exists():
            return target
        if on_conflict == "overwrite":
            if target.is_file():
                target.unlink()
            return target
        if on_conflict == "skip":
            return None
        if on_conflict == "rename":
            stem = target.stem
            suffix = target.suffix
            parent = target.parent
            counter = 1
            while True:
                candidate = parent / f"{stem} ({counter}){suffix}"
                if not candidate.exists():
                    return candidate
                counter += 1
        raise FileMoveError(f"Unsupported conflict policy: {on_conflict}")
