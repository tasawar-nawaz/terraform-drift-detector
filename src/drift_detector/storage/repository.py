from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from drift_detector.model.resources import DriftReport
from drift_detector.report.formatters import report_to_dict


class ScanRepository:
    def __init__(self, database_path: str) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scans (
                    scan_id TEXT PRIMARY KEY,
                    workspace TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    has_drift INTEGER NOT NULL,
                    summary_json TEXT NOT NULL,
                    report_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save(self, report: DriftReport) -> None:
        payload = report_to_dict(report)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO scans
                (scan_id, workspace, started_at, finished_at, has_drift, summary_json, report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.scan_id,
                    report.workspace,
                    report.started_at.isoformat(),
                    report.finished_at.isoformat() if report.finished_at else None,
                    1 if report.has_drift() else 0,
                    json.dumps(payload["summary"]),
                    json.dumps(payload),
                ),
            )
            conn.commit()

    def list_scans(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT scan_id, workspace, started_at, finished_at, has_drift, summary_json
                FROM scans ORDER BY started_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        results = []
        for row in rows:
            results.append(
                {
                    "scan_id": row["scan_id"],
                    "workspace": row["workspace"],
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                    "has_drift": bool(row["has_drift"]),
                    "summary": json.loads(row["summary_json"]),
                }
            )
        return results

    def get_scan(self, scan_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT report_json FROM scans WHERE scan_id = ?",
                (scan_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["report_json"])
