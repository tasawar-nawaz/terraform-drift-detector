from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from drift_detector.api.app import create_app  # noqa: E402
from drift_detector.config import AppConfig  # noqa: E402


def test_api_lists_scans(tmp_path):
    cfg = AppConfig.from_dict(
        {
            "state": {"path": "tests/fixtures/sample.tfstate", "backend": "local"},
            "storage": {"database": str(tmp_path / "drift.db")},
            "server": {"api_key": "secret"},
        }
    )
    client = TestClient(create_app(cfg))
    unauthorized = client.get("/api/scans")
    assert unauthorized.status_code == 401

    headers = {"X-API-Key": "secret"}
    empty = client.get("/api/scans", headers=headers)
    assert empty.status_code == 200
    assert empty.json() == []

    run_resp = client.post("/api/scans/run", headers=headers)
    assert run_resp.status_code == 200
    assert "scan_id" in run_resp.json()

    listed = client.get("/api/scans", headers=headers).json()
    assert len(listed) == 1

    metrics = client.get("/metrics", headers=headers)
    assert metrics.status_code == 200
    assert "drift_scans_total" in metrics.text
