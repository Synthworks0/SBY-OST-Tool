from __future__ import annotations

import logging
import os
from pathlib import Path
from threading import Event
from typing import Optional

import requests

try:
    import boto3
    from botocore.client import Config as BotoConfig
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:  # pragma: no cover
    boto3 = None
    BotoConfig = None
    BotoCoreError = ClientError = Exception

from .config import AppConfig

logger = logging.getLogger(__name__)


class R2Client:
    def __init__(self, config: AppConfig, cancel_event: Optional[Event] = None) -> None:
        self._config = config
        self._cancel_event = cancel_event
        access_key = config.r2.access_key or os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = config.r2.secret_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        bucket = config.r2.bucket or os.getenv("AWS_S3_BUCKET")
        endpoint = config.r2.endpoint_url or os.getenv("AWS_ENDPOINT_URL")

        if not boto3:
            raise RuntimeError("boto3 is required for Cloudflare R2 access. Install boto3 and retry.")
        if not all([bucket, endpoint, access_key, secret_key]):
            raise RuntimeError(
                "Cloudflare R2 credentials are incomplete. Set SBY_R2_BUCKET, SBY_R2_ENDPOINT, "
                "SBY_R2_ACCESS_KEY, and SBY_R2_SECRET_KEY (or the standard AWS_* equivalents)."
            )

        region = (config.r2.region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "").strip()
        if not region or region.lower() == "auto":
            region = None
        region = (config.r2.region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "auto").strip()

        try:
            session = boto3.session.Session()
            self._s3 = session.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
                config=BotoConfig(signature_version="s3v4"),
            )
        except (BotoCoreError, ClientError, ValueError) as exc:
            raise RuntimeError(f"Failed to initialise Cloudflare R2 client: {exc}") from exc

        self._bucket = bucket
        self._prefix = (config.r2.prefix or "").strip().strip("/")

    def _object_key(self, relative_path: str) -> str:
        rel = relative_path.replace("\\", "/").lstrip("/")
        if self._prefix:
            return f"{self._prefix}/{rel}"
        return rel

    def build_url(self, relative_path: str) -> str:
        params = {"Bucket": self._bucket, "Key": self._object_key(relative_path)}
        try:
            return self._s3.generate_presigned_url(
                ClientMethod="get_object",
                Params=params,
                ExpiresIn=self._config.r2.presign_ttl,
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"Failed to generate presigned URL for {relative_path}: {exc}") from exc

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
