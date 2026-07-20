from drift_detector.model.diff import deep_diff, tag_diff
from drift_detector.model.resources import (
    DriftKind,
    NormalizedResource,
    ResourceIdentity,
)
from drift_detector.config import ScanConfig
from drift_detector.drift.engine import compare_resources, run_drift_scan
from drift_detector.model.resources import DriftReport
from drift_detector.state.reader import StateReader


def test_state_reader_parses_managed_resources():
    doc = StateReader().read("tests/fixtures/sample.tfstate")
    assert doc.serial == 42
    assert len(doc.resources) == 3
    types = {r.resource_type for r in doc.resources}
    assert types == {"aws_instance", "aws_s3_bucket", "aws_security_group"}


def test_tag_diff_detects_changes():
    diffs = tag_diff({"env": "dev"}, {"env": "prod"})
    assert len(diffs) == 1
    assert diffs[0].path == "tags.env"


def test_compare_deleted_resource():
    identity = ResourceIdentity(
        provider="aws",
        resource_type="aws_instance",
        name="web",
        external_id="i-123",
    )
    expected = NormalizedResource(identity=identity, attributes={"ami": "ami-1"})
    findings = compare_resources(expected, None, ScanConfig())
    assert len(findings) == 1
    assert findings[0].kind == DriftKind.DELETED


def test_compare_modified_attributes():
    identity = ResourceIdentity(
        provider="aws",
        resource_type="aws_instance",
        name="web",
        external_id="i-123",
    )
    expected = NormalizedResource(
        identity=identity,
        attributes={"instance_type": "t3.micro"},
        tags={"env": "dev"},
    )
    actual = NormalizedResource(
        identity=identity,
        attributes={"instance_type": "t3.small"},
        tags={"env": "dev"},
        source="cloud",
    )
    findings = compare_resources(expected, actual, ScanConfig())
    kinds = {f.kind for f in findings}
    assert DriftKind.MODIFIED in kinds
    assert DriftKind.TAGS_CHANGED not in kinds


def test_run_drift_scan_summary():
    identity = ResourceIdentity(
        provider="aws",
        resource_type="aws_instance",
        name="web",
        external_id="i-123",
    )
    expected = NormalizedResource(identity=identity, attributes={"ami": "ami-1"})
    report = DriftReport.new_scan()
    report = run_drift_scan(report, [expected], {}, ScanConfig())
    assert report.summary.deleted == 1
    assert report.has_drift()
