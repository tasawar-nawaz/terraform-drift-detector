from __future__ import annotations

import httpx

from drift_detector.config import WebhookConfig
from drift_detector.model.resources import DriftReport
from drift_detector.report.formatters import report_to_dict


class WebhookNotifier:
    def __init__(self, webhooks: list[WebhookConfig]) -> None:
        self._webhooks = webhooks

    def send(self, report: DriftReport) -> list[str]:
        errors: list[str] = []
        if not self._webhooks:
            return errors

        payload = report_to_dict(report)
        for hook in self._webhooks:
            if hook.on_drift_only and not report.has_drift():
                continue
            try:
                resp = httpx.post(hook.url, json=payload, timeout=15.0)
                resp.raise_for_status()
            except Exception as exc:
                errors.append(f"{hook.url}: {exc}")
        return errors
