from __future__ import annotations

from drift_detector.cloud.factory import build_cloud_fetchers
from drift_detector.config import AppConfig
from drift_detector.drift.engine import run_drift_scan
from drift_detector.extract.registry import get_default_registry
from drift_detector.extract.state import state_to_normalized
from drift_detector.model.resources import DriftReport, NormalizedResource
from drift_detector.state.backends import StateBackendError, load_state_document


class ScanService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._registry = get_default_registry()

    def run(self) -> DriftReport:
        report = DriftReport.new_scan(workspace=self._config.scan.workspace)
        try:
            doc = load_state_document(self._config.state)
        except StateBackendError as exc:
            report.fetch_errors.append(str(exc))
            report.summary.errors = 1
            report.finish()
            return report

        report.state_serial = doc.serial

        allowed_types = set(self._config.scan.resource_types or self._registry.supported_types())
        expected_list: list[NormalizedResource] = []

        for resource in doc.resources:
            if resource.resource_type not in allowed_types:
                continue
            normalized = state_to_normalized(resource, self._registry)
            if normalized is None:
                report.fetch_errors.append(
                    f"Unsupported resource type in state: {resource.resource_type}.{resource.name}"
                )
                continue
            if not normalized.identity.external_id and resource.resource_type not in (
                "aws_s3_bucket",
                "azurerm_resource_group",
                "google_storage_bucket",
            ):
                report.fetch_errors.append(
                    f"Missing external id for {resource.resource_type}.{resource.name}"
                )
                continue
            expected_list.append(normalized)

        fetchers = build_cloud_fetchers(self._config, self._registry)
        actual_map: dict[str, NormalizedResource] = {}
        fetch_error_count = 0
        comparable_expected: list[NormalizedResource] = []

        for expected in expected_list:
            fetcher = fetchers.get(expected.identity.provider)
            if fetcher is None:
                report.fetch_errors.append(
                    f"{expected.identity.display_address()}: no fetcher for provider "
                    f"'{expected.identity.provider}' (enable in config)"
                )
                fetch_error_count += 1
                continue

            actual, err = fetcher.fetch_one(expected)
            if err:
                report.fetch_errors.append(
                    f"{expected.identity.display_address()}: {err}"
                )
                fetch_error_count += 1
                continue

            comparable_expected.append(expected)
            if actual is not None:
                actual_map[expected.identity.key()] = actual

        result = run_drift_scan(report, comparable_expected, actual_map, self._config.scan)
        result.summary.total_expected = len(expected_list)
        result.summary.errors = fetch_error_count
        return result
