from __future__ import annotations

from dataclasses import dataclass, field

from drift_detector.model.resources import DriftReport


@dataclass
class MetricsRegistry:
    scans_total: int = 0
    findings_total: dict[str, int] = field(default_factory=dict)
    last_scan_duration_seconds: float = 0.0

    def record_scan(self, report: DriftReport) -> None:
        self.scans_total += 1
        if report.started_at and report.finished_at:
            self.last_scan_duration_seconds = (
                report.finished_at - report.started_at
            ).total_seconds()
        for finding in report.findings:
            kind = finding.kind.value
            self.findings_total[kind] = self.findings_total.get(kind, 0) + 1

    def render_prometheus(self) -> str:
        lines = [
            "# HELP drift_scans_total Total drift scans executed",
            "# TYPE drift_scans_total counter",
            f"drift_scans_total {self.scans_total}",
            "# HELP drift_scan_duration_seconds Duration of the last scan",
            "# TYPE drift_scan_duration_seconds gauge",
            f"drift_scan_duration_seconds {self.last_scan_duration_seconds:.3f}",
        ]
        lines.append("# HELP drift_findings_total Drift findings by kind")
        lines.append("# TYPE drift_findings_total counter")
        for kind, count in sorted(self.findings_total.items()):
            lines.append(f'drift_findings_total{{kind="{kind}"}} {count}')
        return "\n".join(lines) + "\n"


metrics_registry = MetricsRegistry()
