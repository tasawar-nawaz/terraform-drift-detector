from __future__ import annotations

from typing import Any

from drift_detector.config import GcpConfig
from drift_detector.extract.registry import ExtractorRegistry
from drift_detector.model.resources import NormalizedResource, ResourceIdentity


class GcpCloudFetcher:
    provider = "google"

    def __init__(self, config: GcpConfig, registry: ExtractorRegistry) -> None:
        self._config = config
        self._registry = registry

    def fetch_one(self, expected: NormalizedResource) -> tuple[NormalizedResource | None, str | None]:
        try:
            from google.api_core.exceptions import NotFound
            from google.cloud import storage
        except ImportError:
            return None, "google-cloud-storage is not installed (pip install terraform-drift-detector[gcp])"

        rtype = expected.identity.resource_type
        mapper = self._registry.cloud_mapper(rtype)
        if mapper is None:
            return None, f"No cloud mapper for {rtype}"

        try:
            raw = self._fetch_raw(rtype, expected, storage)
        except NotFound:
            return None, None
        except Exception as exc:
            return None, str(exc)

        if raw is None:
            return None, None

        identity = ResourceIdentity(
            provider=expected.identity.provider,
            resource_type=expected.identity.resource_type,
            name=expected.identity.name,
            module=expected.identity.module,
            external_id=expected.identity.external_id,
        )
        return mapper.map_from_cloud(raw, identity), None

    def _fetch_raw(
        self,
        resource_type: str,
        expected: NormalizedResource,
        storage_mod: Any,
    ) -> dict[str, Any] | None:
        if resource_type == "google_storage_bucket":
            client = storage_mod.Client(project=self._config.project_id or None)
            bucket_name = expected.attributes.get("name") or expected.identity.name
            bucket = client.get_bucket(bucket_name)
            labels = dict(bucket.labels or {})
            tags = {k: str(v) for k, v in labels.items()}
            return {
                "name": bucket.name,
                "location": bucket.location,
                "storage_class": bucket.storage_class,
                "labels": tags,
            }
        return None
