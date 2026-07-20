from __future__ import annotations

from typing import Any

from drift_detector.extract.registry import CloudMapper, ExtractorRegistry, StateMapper
from drift_detector.model.resources import NormalizedResource, ResourceIdentity


def _pick(attributes: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in keys:
        if key in attributes and attributes[key] is not None:
            out[key] = attributes[key]
    return out


def _tags_from_map(tags: Any) -> dict[str, str]:
    if not tags:
        return {}
    if isinstance(tags, dict):
        return {str(k): str(v) for k, v in tags.items()}
    if isinstance(tags, list):
        result: dict[str, str] = {}
        for item in tags:
            if isinstance(item, dict):
                k = item.get("key") or item.get("Key")
                v = item.get("value") or item.get("Value")
                if k is not None and v is not None:
                    result[str(k)] = str(v)
        return result
    return {}


class AwsS3BucketStateMapper:
    resource_type = "aws_s3_bucket"

    def comparable_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        return _pick(
            attributes,
            [
                "bucket",
                "force_destroy",
                "object_lock_enabled",
            ],
        )

    def tags_from_state(self, attributes: dict[str, Any]) -> dict[str, str]:
        return _tags_from_map(attributes.get("tags") or attributes.get("tags_all"))


class AwsS3BucketCloudMapper:
    resource_type = "aws_s3_bucket"

    def map_from_cloud(self, raw: dict[str, Any], identity: ResourceIdentity) -> NormalizedResource:
        return NormalizedResource(
            identity=identity,
            attributes={
                "bucket": raw.get("Name") or identity.name,
                "force_destroy": False,
            },
            tags=_tags_from_map(raw.get("Tags")),
            source="cloud",
        )


class AwsInstanceStateMapper:
    resource_type = "aws_instance"

    def comparable_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        return _pick(
            attributes,
            [
                "ami",
                "instance_type",
                "availability_zone",
                "tenancy",
                "ebs_optimized",
                "monitoring",
            ],
        )

    def tags_from_state(self, attributes: dict[str, Any]) -> dict[str, str]:
        return _tags_from_map(attributes.get("tags") or attributes.get("tags_all"))


class AwsInstanceCloudMapper:
    resource_type = "aws_instance"

    def map_from_cloud(self, raw: dict[str, Any], identity: ResourceIdentity) -> NormalizedResource:
        placement = raw.get("Placement") or {}
        monitoring = raw.get("Monitoring") or {}
        return NormalizedResource(
            identity=identity,
            attributes={
                "ami": raw.get("ImageId"),
                "instance_type": raw.get("InstanceType"),
                "availability_zone": placement.get("AvailabilityZone"),
                "tenancy": placement.get("Tenancy"),
                "ebs_optimized": raw.get("EbsOptimized"),
                "monitoring": monitoring.get("State") == "enabled",
            },
            tags=_tags_from_map(raw.get("Tags")),
            source="cloud",
        )


class AwsSecurityGroupStateMapper:
    resource_type = "aws_security_group"

    def comparable_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        return _pick(
            attributes,
            [
                "name",
                "description",
                "vpc_id",
            ],
        )

    def tags_from_state(self, attributes: dict[str, Any]) -> dict[str, str]:
        return _tags_from_map(attributes.get("tags") or attributes.get("tags_all"))


class AwsSecurityGroupCloudMapper:
    resource_type = "aws_security_group"

    def map_from_cloud(self, raw: dict[str, Any], identity: ResourceIdentity) -> NormalizedResource:
        return NormalizedResource(
            identity=identity,
            attributes={
                "name": raw.get("GroupName"),
                "description": raw.get("Description"),
                "vpc_id": raw.get("VpcId"),
            },
            tags=_tags_from_map(raw.get("Tags")),
            source="cloud",
        )


def register_aws_mappers(registry: ExtractorRegistry) -> None:
    state_mappers: list[StateMapper] = [
        AwsS3BucketStateMapper(),
        AwsInstanceStateMapper(),
        AwsSecurityGroupStateMapper(),
    ]
    cloud_mappers: list[CloudMapper] = [
        AwsS3BucketCloudMapper(),
        AwsInstanceCloudMapper(),
        AwsSecurityGroupCloudMapper(),
    ]
    for mapper in state_mappers:
        registry.register_state(mapper)
    for mapper in cloud_mappers:
        registry.register_cloud(mapper)
