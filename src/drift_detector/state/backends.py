from __future__ import annotations

import json
import tempfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from drift_detector.config import StateConfig
from drift_detector.state.reader import StateDocument, StateReader


class StateBackendError(Exception):
    pass


def load_state_document(config: StateConfig) -> StateDocument:
    backend = (config.backend or "local").lower()
    reader = StateReader()
    if backend == "local":
        if not config.path:
            raise StateBackendError("state.path is required for local backend")
        return reader.read(config.path)
    if backend == "s3":
        raw = _read_s3_state(config)
        return reader.parse(raw)
    raise StateBackendError(f"Unsupported state backend: {backend}")


def _read_s3_state(config: StateConfig) -> dict:
    if not config.bucket or not config.key:
        raise StateBackendError("state.bucket and state.key are required for s3 backend")
    session_kwargs: dict = {}
    if config.profile:
        session_kwargs["profile_name"] = config.profile
    session = boto3.Session(**session_kwargs)
    client = session.client("s3", region_name=config.region or None)
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
        client.download_file(config.bucket, config.key, str(tmp_path))
        with tmp_path.open(encoding="utf-8") as f:
            return json.load(f)
    except ClientError as exc:
        raise StateBackendError(f"S3 state read failed: {exc}") from exc
    finally:
        if "tmp_path" in locals() and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
