from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StateResource:
    module: str
    mode: str
    provider: str
    resource_type: str
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class StateDocument:
    version: int
    serial: int | None
    lineage: str | None
    resources: list[StateResource] = field(default_factory=list)


class StateReader:
    """Load Terraform state JSON from a local file."""

    def read(self, path: Path | str) -> StateDocument:
        path = Path(path)
        with path.open(encoding="utf-8") as f:
            raw = json.load(f)
        return self.parse(raw)

    def parse(self, raw: dict[str, Any]) -> StateDocument:
        version = int(raw.get("version", 0))
        serial = raw.get("serial")
        if serial is not None:
            serial = int(serial)
        lineage = raw.get("lineage")
        resources: list[StateResource] = []

        for entry in raw.get("resources") or []:
            module = entry.get("module") or ""
            mode = entry.get("mode") or "managed"
            if mode != "managed":
                continue
            provider = _normalize_provider(entry.get("provider") or "")
            resource_type = entry.get("type") or ""
            name = entry.get("name") or ""
            for inst in entry.get("instances") or []:
                attrs = dict((inst.get("attributes") or {}))
                resources.append(
                    StateResource(
                        module=module,
                        mode=mode,
                        provider=provider,
                        resource_type=resource_type,
                        name=name,
                        attributes=attrs,
                    )
                )
        return StateDocument(
            version=version,
            serial=serial,
            lineage=lineage,
            resources=resources,
        )


def _normalize_provider(provider: str) -> str:
    if provider.startswith("provider["):
        inner = provider[len("provider[") : -1].strip('"')
        if "/" in inner:
            return inner.split("/")[-1]
        return inner
    if "/" in provider:
        return provider.split("/")[-1]
    return provider or "unknown"
