from __future__ import annotations

import json
from typing import Any

from drift_detector.model.resources import DriftFinding, DriftKind, DriftReport


def report_to_dict(report: DriftReport) -> dict[str, Any]:
    def finding_dict(f: DriftFinding) -> dict[str, Any]:
        return {
            "kind": f.kind.value,
            "resource": f.identity.display_address(),
            "provider": f.identity.provider,
            "type": f.identity.resource_type,
            "name": f.identity.name,
            "external_id": f.identity.external_id,
            "message": f.message,
            "attribute_diffs": [
                {"path": d.path, "expected": d.expected, "actual": d.actual}
                for d in f.attribute_diffs
            ],
            "tag_diffs": [
                {"path": d.path, "expected": d.expected, "actual": d.actual}
                for d in f.tag_diffs
            ],
        }

    return {
        "scan_id": report.scan_id,
        "workspace": report.workspace,
        "started_at": report.started_at.isoformat(),
        "finished_at": report.finished_at.isoformat() if report.finished_at else None,
        "state_serial": report.state_serial,
        "summary": {
            "total_expected": report.summary.total_expected,
            "total_actual": report.summary.total_actual,
            "deleted": report.summary.deleted,
            "modified": report.summary.modified,
            "tags_changed": report.summary.tags_changed,
            "unchanged": report.summary.unchanged,
            "errors": report.summary.errors,
        },
        "findings": [finding_dict(f) for f in report.findings],
        "fetch_errors": report.fetch_errors,
        "webhook_errors": report.webhook_errors,
        "has_drift": report.has_drift(),
    }


def report_to_json(report: DriftReport, indent: int | None = 2) -> str:
    return json.dumps(report_to_dict(report), indent=indent, default=str)


def format_table(report: DriftReport) -> str:
    lines: list[str] = []
    lines.append(f"Scan {report.scan_id}  workspace={report.workspace}")
    if report.state_serial is not None:
        lines.append(f"State serial: {report.state_serial}")
    s = report.summary
    lines.append(
        f"Summary: expected={s.total_expected} actual={s.total_actual} "
        f"unchanged={s.unchanged} deleted={s.deleted} modified={s.modified} "
        f"tags_changed={s.tags_changed} errors={s.errors}"
    )
    if not report.findings and not report.fetch_errors:
        lines.append("No drift detected.")
        return "\n".join(lines)
    for finding in report.findings:
        lines.append("")
        lines.append(f"[{finding.kind.value.upper()}] {finding.identity.display_address()}")
        lines.append(f"  {finding.message}")
        for d in finding.attribute_diffs:
            lines.append(f"  attr {d.path}: expected={d.expected!r} actual={d.actual!r}")
        for d in finding.tag_diffs:
            lines.append(f"  tag {d.path}: expected={d.expected!r} actual={d.actual!r}")
    if report.fetch_errors:
        lines.append("")
        lines.append("Fetch errors:")
        for err in report.fetch_errors:
            lines.append(f"  - {err}")
    return "\n".join(lines)
