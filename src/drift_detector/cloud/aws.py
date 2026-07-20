from __future__ import annotations

from typing import Any

import boto3
from botocore.exceptions import ClientError

from drift_detector.config import AwsConfig
from drift_detector.extract.registry import ExtractorRegistry
from drift_detector.model.resources import NormalizedResource, ResourceIdentity


class AwsCloudFetcher:
    """Fetch live AWS resources referenced in Terraform state."""

    provider = "aws"

    def __init__(self, config: AwsConfig, registry: ExtractorRegistry) -> None:
        session_kwargs: dict[str, Any] = {}
        if config.profile:
            session_kwargs["profile_name"] = config.profile
        self._session = boto3.Session(**session_kwargs)
        self._region = config.region
        self._registry = registry

    def fetch_one(self, expected: NormalizedResource) -> tuple[NormalizedResource | None, str | None]:
        rtype = expected.identity.resource_type
        mapper = self._registry.cloud_mapper(rtype)
        if mapper is None:
            return None, f"No cloud mapper for {rtype}"
        try:
            raw = self._fetch_raw(rtype, expected)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in ("InvalidInstanceID.NotFound", "NoSuchBucket", "InvalidGroup.NotFound"):
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

    def _fetch_raw(self, resource_type: str, expected: NormalizedResource) -> dict[str, Any] | None:
        attrs = expected.identity
        ext_id = expected.identity.external_id
        if resource_type == "aws_instance":
            ec2 = self._session.client("ec2", region_name=self._region)
            resp = ec2.describe_instances(InstanceIds=[ext_id])
            for reservation in resp.get("Reservations") or []:
                for inst in reservation.get("Instances") or []:
                    if inst.get("InstanceId") == ext_id:
                        return inst
            return None
        if resource_type == "aws_s3_bucket":
            s3 = self._session.client("s3", region_name=self._region)
            bucket = expected.attributes.get("bucket") or expected.identity.name
            s3.head_bucket(Bucket=bucket)
            loc = s3.get_bucket_location(Bucket=bucket)
            region = loc.get("LocationConstraint") or "us-east-1"
            tags: list[dict[str, str]] = []
            try:
                tagging = s3.get_bucket_tagging(Bucket=bucket)
                tags = [{"Key": t["Key"], "Value": t["Value"]} for t in tagging.get("TagSet") or []]
            except ClientError as exc:
                code = exc.response.get("Error", {}).get("Code", "")
                if code not in ("NoSuchTagSet", "AccessDenied"):
                    raise
            return {"Name": bucket, "Region": region, "Tags": tags}
        if resource_type == "aws_security_group":
            ec2 = self._session.client("ec2", region_name=self._region)
            resp = ec2.describe_security_groups(GroupIds=[ext_id])
            groups = resp.get("SecurityGroups") or []
            return groups[0] if groups else None
        return None
