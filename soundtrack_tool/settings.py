from __future__ import annotations
import json
from pathlib import Path
from typing import Any


class AppSettings:
    """Simple JSON-backed settings store."""

    def __init__(self, settings_path: Path) -> None:
        self._path = settings_path
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def load_last_output_folder(self) -> str:
        if not self._path.exists():
            return ""
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return ""
        return data.get("last_output_folder", "") if isinstance(data, dict) else ""

    def save_last_output_folder(self, folder: str) -> None:
        payload = {"last_output_folder": folder}
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass


__all__ = ["AppSettings"]
