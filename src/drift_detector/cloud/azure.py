from __future__ import annotations

from typing import Any

import httpx

from drift_detector.config import AzureConfig
from drift_detector.extract.registry import ExtractorRegistry
from drift_detector.model.resources import NormalizedResource, ResourceIdentity


class AzureCloudFetcher:
    provider = "azurerm"

    def __init__(self, config: AzureConfig, registry: ExtractorRegistry) -> None:
        self._config = config
        self._registry = registry

    def fetch_one(self, expected: NormalizedResource) -> tuple[NormalizedResource | None, str | None]:
        try:
            from azure.identity import DefaultAzureCredential
        except ImportError:
            return None, "azure-identity is not installed (pip install terraform-drift-detector[azure])"

        if not self._config.subscription_id:
            return None, "azure.subscription_id is required"

        rtype = expected.identity.resource_type
        mapper = self._registry.cloud_mapper(rtype)
        if mapper is None:
            return None, f"No cloud mapper for {rtype}"

        try:
            raw = self._fetch_raw(rtype, expected, DefaultAzureCredential())
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None, None
            return None, str(exc)
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
        credential: Any,
    ) -> dict[str, Any] | None:
        token = credential.get_token("https://management.azure.com/.default").token
        headers = {"Authorization": f"Bearer {token}"}

        if resource_type == "azurerm_resource_group":
            name = expected.attributes.get("name") or expected.identity.name
            url = (
                f"https://management.azure.com/subscriptions/{self._config.subscription_id}"
                f"/resourcegroups/{name}?api-version=2021-04-01"
            )
            resp = httpx.get(url, headers=headers, timeout=30.0)
            resp.raise_for_status()
            return resp.json()

        if resource_type == "azurerm_storage_account":
            resource_id = expected.identity.external_id or expected.attributes.get("id")
            if not resource_id:
                return None
            url = f"https://management.azure.com{resource_id}?api-version=2023-01-01"
            resp = httpx.get(url, headers=headers, timeout=30.0)
            resp.raise_for_status()
            return resp.json()

        return None
