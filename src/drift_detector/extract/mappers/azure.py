from __future__ import annotations

from typing import Any

from drift_detector.extract.mappers.aws import _pick, _tags_from_map
from drift_detector.extract.registry import CloudMapper, ExtractorRegistry, StateMapper
from drift_detector.model.resources import NormalizedResource, ResourceIdentity


class AzurermResourceGroupStateMapper:
    resource_type = "azurerm_resource_group"

    def comparable_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        return _pick(attributes, ["name", "location"])

    def tags_from_state(self, attributes: dict[str, Any]) -> dict[str, str]:
        return _tags_from_map(attributes.get("tags"))


class AzurermResourceGroupCloudMapper:
    resource_type = "azurerm_resource_group"

    def map_from_cloud(self, raw: dict[str, Any], identity: ResourceIdentity) -> NormalizedResource:
        props = raw.get("properties") or {}
        return NormalizedResource(
            identity=identity,
            attributes={
                "name": raw.get("name"),
                "location": raw.get("location") or props.get("location"),
            },
            tags=_tags_from_map(raw.get("tags")),
            source="cloud",
        )


class AzurermStorageAccountStateMapper:
    resource_type = "azurerm_storage_account"

    def comparable_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        return _pick(
            attributes,
            ["name", "account_tier", "account_replication_type", "account_kind"],
        )

    def tags_from_state(self, attributes: dict[str, Any]) -> dict[str, str]:
        return _tags_from_map(attributes.get("tags"))


class AzurermStorageAccountCloudMapper:
    resource_type = "azurerm_storage_account"

    def map_from_cloud(self, raw: dict[str, Any], identity: ResourceIdentity) -> NormalizedResource:
        sku = (raw.get("sku") or {}).get("name", "")
        tier = sku.split("_")[0] if "_" in sku else sku
        replication = sku.split("_")[1] if "_" in sku else ""
        return NormalizedResource(
            identity=identity,
            attributes={
                "name": raw.get("name"),
                "account_tier": tier,
                "account_replication_type": replication,
                "account_kind": raw.get("kind"),
            },
            tags=_tags_from_map(raw.get("tags")),
            source="cloud",
        )


def register_azure_mappers(registry: ExtractorRegistry) -> None:
    for mapper in (
        AzurermResourceGroupStateMapper(),
        AzurermStorageAccountStateMapper(),
    ):
        registry.register_state(mapper)
    for mapper in (
        AzurermResourceGroupCloudMapper(),
        AzurermStorageAccountCloudMapper(),
    ):
        registry.register_cloud(mapper)
