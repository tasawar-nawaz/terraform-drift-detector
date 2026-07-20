from drift_detector.model.resources import DriftReport, DriftKind, ResourceIdentity, DriftFinding
from drift_detector.storage.repository import ScanRepository


def test_repository_roundtrip(tmp_path):
    db = tmp_path / "drift.db"
    repo = ScanRepository(str(db))
    report = DriftReport.new_scan(workspace="demo")
    report.finish()
    report.findings.append(
        DriftFinding(
            kind=DriftKind.MODIFIED,
            identity=ResourceIdentity("aws", "aws_instance", "web", external_id="i-1"),
            message="changed",
        )
    )
    repo.save(report)

    listed = repo.list_scans()
    assert len(listed) == 1
    assert listed[0]["scan_id"] == report.scan_id
    assert listed[0]["has_drift"] is True

    loaded = repo.get_scan(report.scan_id)
    assert loaded is not None
    assert loaded["workspace"] == "demo"
