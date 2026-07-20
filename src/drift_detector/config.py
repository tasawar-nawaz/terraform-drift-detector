from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class StateConfig:
    path: str = ""
    backend: str = "local"
    bucket: str = ""
    key: str = ""
    region: str = ""
    profile: str | None = None


@dataclass
class AwsConfig:
    enabled: bool = True
    region: str = "us-east-1"
    profile: str | None = None


@dataclass
class AzureConfig:
    enabled: bool = False
    subscription_id: str = ""
    tenant_id: str | None = None


@dataclass
class GcpConfig:
    enabled: bool = False
    project_id: str = ""


@dataclass
class ComparisonConfig:
    profile: str = "default"
    ignore_attribute_paths: list[str] = field(default_factory=list)


@dataclass
class ScanConfig:
    workspace: str = "default"
    resource_types: list[str] = field(default_factory=list)
    ignore_tag_keys: list[str] = field(default_factory=list)
    compare_attributes: bool = True
    report_unmanaged: bool = False
    comparison: ComparisonConfig = field(default_factory=ComparisonConfig)


@dataclass
class StorageConfig:
    database: str = "drift.db"


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8080
    api_key: str = ""


@dataclass
class ScheduleConfig:
    enabled: bool = False
    cron: str = "0 * * * *"


@dataclass
class WebhookConfig:
    url: str
    on_drift_only: bool = True


@dataclass
class AppConfig:
    state: StateConfig
    aws: AwsConfig = field(default_factory=AwsConfig)
    azure: AzureConfig = field(default_factory=AzureConfig)
    gcp: GcpConfig = field(default_factory=GcpConfig)
    scan: ScanConfig = field(default_factory=ScanConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    webhooks: list[WebhookConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppConfig:
        state_raw = data.get("state") or {}
        aws_raw = data.get("aws") or {}
        azure_raw = data.get("azure") or {}
        gcp_raw = data.get("gcp") or {}
        scan_raw = data.get("scan") or {}
        storage_raw = data.get("storage") or {}
        server_raw = data.get("server") or {}
        schedule_raw = data.get("schedule") or {}
        comparison_raw = scan_raw.get("comparison") or data.get("comparison") or {}
        webhook_raw = data.get("webhooks") or []

        webhooks = [
            WebhookConfig(
                url=str(item.get("url", "")),
                on_drift_only=bool(item.get("on_drift_only", True)),
            )
            for item in webhook_raw
            if isinstance(item, dict) and item.get("url")
        ]

        return cls(
            state=StateConfig(
                path=str(state_raw.get("path", "")),
                backend=str(state_raw.get("backend", "local")),
                bucket=str(state_raw.get("bucket", "")),
                key=str(state_raw.get("key", "")),
                region=str(state_raw.get("region", "")),
                profile=state_raw.get("profile"),
            ),
            aws=AwsConfig(
                enabled=bool(aws_raw.get("enabled", True)),
                region=str(aws_raw.get("region", "us-east-1")),
                profile=aws_raw.get("profile"),
            ),
            azure=AzureConfig(
                enabled=bool(azure_raw.get("enabled", False)),
                subscription_id=str(azure_raw.get("subscription_id", "")),
                tenant_id=azure_raw.get("tenant_id"),
            ),
            gcp=GcpConfig(
                enabled=bool(gcp_raw.get("enabled", False)),
                project_id=str(gcp_raw.get("project_id", "")),
            ),
            scan=ScanConfig(
                workspace=str(scan_raw.get("workspace", "default")),
                resource_types=list(scan_raw.get("resource_types") or []),
                ignore_tag_keys=list(scan_raw.get("ignore_tag_keys") or []),
                compare_attributes=bool(scan_raw.get("compare_attributes", True)),
                report_unmanaged=bool(scan_raw.get("report_unmanaged", False)),
                comparison=ComparisonConfig(
                    profile=str(comparison_raw.get("profile", "default")),
                    ignore_attribute_paths=list(
                        comparison_raw.get("ignore_attribute_paths") or []
                    ),
                ),
            ),
            storage=StorageConfig(database=str(storage_raw.get("database", "drift.db"))),
            server=ServerConfig(
                host=str(server_raw.get("host", "127.0.0.1")),
                port=int(server_raw.get("port", 8080)),
                api_key=str(server_raw.get("api_key", "")),
            ),
            schedule=ScheduleConfig(
                enabled=bool(schedule_raw.get("enabled", False)),
                cron=str(schedule_raw.get("cron", "0 * * * *")),
            ),
            webhooks=webhooks,
        )

    @classmethod
    def load(cls, path: Path | str) -> AppConfig:
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(yaml.safe_load(f) or {})
