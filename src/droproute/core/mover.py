from __future__ import annotations

import errno
import os
import shutil
import threading
import uuid
from pathlib import Path

from droproute.models import Action, ConflictPolicy


class FileMoveError(RuntimeError):
    pass


class FileMover:
    def __init__(self) -> None:
        self._lock = threading.Lock()

    def execute(
        self,
        source: Path,
        destination_dir: Path,
        action: Action,
        on_conflict: ConflictPolicy,
    ) -> Path:
        if not source.is_file():
            raise FileMoveError(f"Source is not a readable file: {source}")

        destination_dir.mkdir(parents=True, exist_ok=True)
        requested_target = destination_dir / source.name
        if _same_path(source, requested_target):
            raise FileMoveError("Source and destination are the same file")

        with self._lock:
            final_target = self._resolve_target(requested_target, on_conflict)

            if final_target is None:
                raise FileMoveError(f"Conflict policy skip triggered for {source.name}")

            try:
                if on_conflict == "overwrite" and final_target.exists():
                    self._overwrite(source, final_target, action)
                elif action == "move":
                    shutil.move(str(source), str(final_target))
                elif action == "copy":
                    shutil.copy2(source, final_target)
                else:
                    raise FileMoveError(f"Unsupported action: {action}")
            except FileMoveError:
                raise
            except OSError as exc:
                raise FileMoveError(f"Unable to route {source.name}: {exc}") from exc
        return final_target

    def _resolve_target(self, target: Path, on_conflict: ConflictPolicy) -> Path | None:
        if not target.exists():
            return target
        if on_conflict == "overwrite":
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

    @staticmethod
    def _overwrite(source: Path, target: Path, action: Action) -> None:
        if target.is_dir():
            raise FileMoveError(f"Cannot overwrite directory: {target}")

        if action == "move":
            try:
                os.replace(source, target)
                return
            except OSError as exc:
                if exc.errno != errno.EXDEV:
                    raise

        temp_target = target.with_name(f".{target.name}.{uuid.uuid4().hex}.droproute.tmp")
        try:
            shutil.copy2(source, temp_target)
            os.replace(temp_target, target)
            if action == "move":
                source.unlink()
        finally:
            temp_target.unlink(missing_ok=True)


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(os.path.abspath(right))
