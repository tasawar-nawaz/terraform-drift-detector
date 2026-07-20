from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DriftKind(str, Enum):
    DELETED = "deleted"
    MODIFIED = "modified"
    TAGS_CHANGED = "tags_changed"
    UNMANAGED = "unmanaged"


@dataclass(frozen=True)
class ResourceIdentity:
    provider: str
    resource_type: str
    name: str
    module: str = ""
    external_id: str = ""

    def key(self) -> str:
        mod = self.module or "root"
        ext = self.external_id or ""
        return f"{self.provider}|{mod}|{self.resource_type}|{self.name}|{ext}"

    def display_address(self) -> str:
        if self.module:
            return f"{self.module}.{self.resource_type}.{self.name}"
        return f"{self.resource_type}.{self.name}"


@dataclass
class NormalizedResource:
    identity: ResourceIdentity
    attributes: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)
    source: str = "state"


@dataclass
class AttributeDiff:
    path: str
    expected: Any
    actual: Any


@dataclass
class DriftFinding:
    kind: DriftKind
    identity: ResourceIdentity
    message: str
    attribute_diffs: list[AttributeDiff] = field(default_factory=list)
    tag_diffs: list[AttributeDiff] = field(default_factory=list)


@dataclass
class ScanSummary:
    total_expected: int = 0
    total_actual: int = 0
    deleted: int = 0
    modified: int = 0
    tags_changed: int = 0
    unchanged: int = 0
    errors: int = 0


@dataclass
class DriftReport:
    scan_id: str
    workspace: str
    started_at: datetime
    finished_at: datetime | None = None
    state_serial: int | None = None
    summary: ScanSummary = field(default_factory=ScanSummary)
    findings: list[DriftFinding] = field(default_factory=list)
    fetch_errors: list[str] = field(default_factory=list)
    webhook_errors: list[str] = field(default_factory=list)

    def has_drift(self) -> bool:
        return any(
            f.kind in (DriftKind.DELETED, DriftKind.MODIFIED, DriftKind.TAGS_CHANGED)
            for f in self.findings
        )

    @staticmethod
    def new_scan(workspace: str = "default") -> DriftReport:
        import uuid

        return DriftReport(
            scan_id=str(uuid.uuid4()),
            workspace=workspace,
            started_at=datetime.now(timezone.utc),
        )

    def finish(self) -> None:
        self.finished_at = datetime.now(timezone.utc)
