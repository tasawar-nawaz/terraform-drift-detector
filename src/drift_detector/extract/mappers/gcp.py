from __future__ import annotations

from typing import Any

from drift_detector.extract.mappers.aws import _pick, _tags_from_map
from drift_detector.extract.registry import ExtractorRegistry, StateMapper, CloudMapper
from drift_detector.model.resources import NormalizedResource, ResourceIdentity


class GoogleStorageBucketStateMapper:
    resource_type = "google_storage_bucket"

    def comparable_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        return _pick(attributes, ["name", "location", "storage_class"])

    def tags_from_state(self, attributes: dict[str, Any]) -> dict[str, str]:
        return _tags_from_map(attributes.get("labels"))


class GoogleStorageBucketCloudMapper:
    resource_type = "google_storage_bucket"

    def map_from_cloud(self, raw: dict[str, Any], identity: ResourceIdentity) -> NormalizedResource:
        return NormalizedResource(
            identity=identity,
            attributes={
                "name": raw.get("name"),
                "location": raw.get("location"),
                "storage_class": raw.get("storage_class"),
            },
            tags=_tags_from_map(raw.get("labels")),
            source="cloud",
        )


def register_gcp_mappers(registry: ExtractorRegistry) -> None:
    registry.register_state(GoogleStorageBucketStateMapper())
    registry.register_cloud(GoogleStorageBucketCloudMapper())
