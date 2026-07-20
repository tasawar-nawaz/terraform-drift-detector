from __future__ import annotations

from drift_detector.config import ScanConfig
from drift_detector.model.diff import deep_diff, tag_diff
from drift_detector.model.resources import (
    DriftFinding,
    DriftKind,
    DriftReport,
    NormalizedResource,
    ScanSummary,
    AttributeDiff,
)


def _filter_tags(tags: dict[str, str], ignore_keys: list[str]) -> dict[str, str]:
    if not ignore_keys:
        return tags
    ignore = set(ignore_keys)
    return {k: v for k, v in tags.items() if k not in ignore}


def _should_ignore_path(path: str, config: ScanConfig) -> bool:
    for ignored in config.comparison.ignore_attribute_paths:
        if path == ignored or path.startswith(f"{ignored}."):
            return True
    return False


def _filter_attribute_diffs(diffs: list[AttributeDiff], config: ScanConfig) -> list[AttributeDiff]:
    if config.comparison.profile == "tags_only":
        return []
    return [d for d in diffs if not _should_ignore_path(d.path, config)]


def compare_resources(
    expected: NormalizedResource,
    actual: NormalizedResource | None,
    config: ScanConfig,
) -> list[DriftFinding]:
    if actual is None:
        return [
            DriftFinding(
                kind=DriftKind.DELETED,
                identity=expected.identity,
                message=f"Resource exists in state but was not found in cloud: {expected.identity.display_address()}",
            )
        ]

    findings: list[DriftFinding] = []
    exp_tags = _filter_tags(expected.tags, config.ignore_tag_keys)
    act_tags = _filter_tags(actual.tags, config.ignore_tag_keys)
    tdiffs = tag_diff(exp_tags, act_tags)
    if tdiffs:
        findings.append(
            DriftFinding(
                kind=DriftKind.TAGS_CHANGED,
                identity=expected.identity,
                message="Tag differences detected",
                tag_diffs=tdiffs,
            )
        )

    compare_attrs = config.compare_attributes and config.comparison.profile != "tags_only"
    if compare_attrs:
        adiffs = _filter_attribute_diffs(
            deep_diff(expected.attributes, actual.attributes),
            config,
        )
        if adiffs:
            findings.append(
                DriftFinding(
                    kind=DriftKind.MODIFIED,
                    identity=expected.identity,
                    message="Attribute differences detected",
                    attribute_diffs=adiffs,
                )
            )

    return findings


def run_drift_scan(
    report: DriftReport,
    expected_list: list[NormalizedResource],
    actual_map: dict[str, NormalizedResource],
    config: ScanConfig,
) -> DriftReport:
    summary = ScanSummary(total_expected=len(expected_list), total_actual=len(actual_map))
    findings: list[DriftFinding] = []

    for expected in expected_list:
        actual = actual_map.get(expected.identity.key())
        resource_findings = compare_resources(expected, actual, config)
        if not resource_findings:
            summary.unchanged += 1
        for finding in resource_findings:
            findings.append(finding)
            if finding.kind == DriftKind.DELETED:
                summary.deleted += 1
            elif finding.kind == DriftKind.MODIFIED:
                summary.modified += 1
            elif finding.kind == DriftKind.TAGS_CHANGED:
                summary.tags_changed += 1

    report.summary = summary
    report.findings = findings
    report.finish()
    return report
