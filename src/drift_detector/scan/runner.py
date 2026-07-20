from __future__ import annotations

from pathlib import Path

from drift_detector.alerts.webhook import WebhookNotifier
from drift_detector.config import AppConfig
from drift_detector.model.resources import DriftReport
from drift_detector.observability.metrics import metrics_registry
from drift_detector.scan.service import ScanService
from drift_detector.storage.repository import ScanRepository


class ScanRunner:
    def __init__(self, config: AppConfig, config_path: Path | None = None) -> None:
        self._config = config
        self._config_path = config_path
        self._repository = ScanRepository(config.storage.database)
        self._notifier = WebhookNotifier(config.webhooks)

    @property
    def repository(self) -> ScanRepository:
        return self._repository

    def run(self, *, persist: bool = True, notify: bool = True) -> DriftReport:
        report = ScanService(self._config).run()
        if persist:
            self._repository.save(report)
        if notify:
            report.webhook_errors = self._notifier.send(report)
        metrics_registry.record_scan(report)
        return report
