from __future__ import annotations

import logging
import os
from pathlib import Path
from threading import Event
from typing import Optional

import requests

from .config import AppConfig

logger = logging.getLogger(__name__)


class R2Client:
     def __init__(self, config: AppConfig, cancel_event: Optional[Event] = None) -> None:
        self._config = config
        self._cancel_event = cancel_event
        self._base_url = (config.r2.base_url or "").strip().rstrip("/")
        self._prefix = (config.r2.prefix or "").strip().strip("/")
        
        if not self._base_url:
            raise RuntimeError(
                "Missing R2 base URL"
            )

    def _object_key(self, relative_path: str) -> str:
        rel = relative_path.replace("\\", "/").lstrip("/")
        if self._prefix:
            return f"{self._prefix}/{rel}"
        return rel

    def build_url(self, relative_path: str) -> str:
        object_key = self._object_key(relative_path)
        return f"{self._base_url}/{object_key}"

    def download_file(self, relative_path: str, destination: Path) -> None:
        url = self.build_url(relative_path)
        logger.debug("Downloading %s to %s", url, destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with destination.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        if self._cancel_event is not None and self._cancel_event.is_set():
                            # Abort download and remove partial file
                            try:
                                response.close()
                            finally:
                                try:
                                    destination.unlink(missing_ok=True)
                                except Exception:
                                    pass
                            raise RuntimeError("Download cancelled")
                        fh.write(chunk)


__all__ = ["R2Client"]
