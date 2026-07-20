from __future__ import annotations

from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from drift_detector.config import AppConfig
from drift_detector.scan.runner import ScanRunner


class ScanScheduler:
    def __init__(self, config: AppConfig, config_path: Path | None = None) -> None:
        self._config = config
        self._config_path = config_path
        self._scheduler = BackgroundScheduler()
        self._runner = ScanRunner(config, config_path=config_path)

    def start(self) -> None:
        if not self._config.schedule.enabled:
            return
        trigger = CronTrigger.from_crontab(self._config.schedule.cron)

        def job() -> None:
            self._runner.run(persist=True, notify=True)

        self._scheduler.add_job(job, trigger=trigger, id="drift-scan", replace_existing=True)
        self._scheduler.start()

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
