from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Iterable, List


class FileSystemService:
    def list_drives(self) -> list[str]:
        if os.name == "nt":
            return self._list_windows_drives()
        return self._list_unix_mounts()

    def list_directory(self, path: str | Path) -> list[dict[str, object]]:
        directory = Path(path)
        if not directory.exists():
            return []
        entries: list[dict[str, object]] = []
        for child in sorted(directory.iterdir(), key=lambda c: (not c.is_dir(), c.name.lower())):
            if child.is_dir():
                entries.append({
                    "name": child.name,
                    "path": str(child),
                    "isDir": True,
                })
        return entries

    def create_folder(self, parent_path: str | Path, folder_name: str) -> Path | None:
        parent = Path(parent_path)
        if not parent.exists():
            return None
        new_path = parent / folder_name
        try:
            new_path.mkdir(parents=False, exist_ok=False)
        except FileExistsError:
            return new_path if new_path.is_dir() else None
        except OSError:
            return None
        return new_path

    @staticmethod
    def join(path1: str | Path, path2: str | Path) -> str:
        return str(Path(path1) / Path(path2))

    @staticmethod
    def parent(path: str | Path) -> str:
        current = Path(path)
        parent = current.parent
        if parent == current:
            return ""
        return str(parent)

    def _list_windows_drives(self) -> list[str]:
        import string
        try:
            from ctypes import windll
        except Exception:
            return ["C:\\"] if Path("C:/").exists() else []
        drives: list[str] = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for idx, letter in enumerate(string.ascii_uppercase):
            if bitmask & (1 << idx):
                drive = f"{letter}:\\"
                if Path(drive).exists():
                    drives.append(drive)
        return drives

    def _list_unix_mounts(self) -> list[str]:
        roots: list[str] = ["/"]
        potential_mounts = [
            Path("/Volumes"),
            Path("/media"),
            Path("/mnt"),
            Path.home(),
        ]
        seen: set[str] = set()
        for root in roots:
            seen.add(root)
        for mount_point in potential_mounts:
            if not mount_point.exists():
                continue
            for child in mount_point.iterdir():
                if child.is_dir():
                    seen.add(str(child))
        return sorted(seen)


__all__ = ["FileSystemService"]
