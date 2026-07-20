import pytest

from drift_detector.config import AppConfig, ScanConfig, ComparisonConfig
from drift_detector.drift.engine import compare_resources
from drift_detector.model.resources import (
    DriftKind,
    NormalizedResource,
    ResourceIdentity,
)
from drift_detector.state.reader import StateReader


def test_provider_normalization():
    doc = StateReader().read("tests/fixtures/sample.tfstate")
    assert all(r.provider == "aws" for r in doc.resources)


def test_tags_only_profile_skips_attribute_drift():
    identity = ResourceIdentity(
        provider="aws",
        resource_type="aws_instance",
        name="web",
        external_id="i-123",
    )
    expected = NormalizedResource(identity=identity, attributes={"instance_type": "t3.micro"})
    actual = NormalizedResource(
        identity=identity,
        attributes={"instance_type": "t3.small"},
        source="cloud",
    )
    cfg = ScanConfig(comparison=ComparisonConfig(profile="tags_only"))
    findings = compare_resources(expected, actual, cfg)
    assert findings == []
