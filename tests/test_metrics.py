from drift_detector.observability.metrics import MetricsRegistry
from drift_detector.model.resources import DriftReport, DriftFinding, DriftKind, ResourceIdentity


def test_prometheus_render():
    metrics = MetricsRegistry()
    report = DriftReport.new_scan()
    report.finish()
    report.findings.append(
        DriftFinding(
            kind=DriftKind.DELETED,
            identity=ResourceIdentity("aws", "aws_instance", "x", external_id="i-1"),
            message="gone",
        )
    )
    metrics.record_scan(report)
    body = metrics.render_prometheus()
    assert "drift_scans_total 1" in body
    assert 'drift_findings_total{kind="deleted"} 1' in body
