from __future__ import annotations

from drift_detector.extract.registry import ExtractorRegistry
from drift_detector.model.resources import NormalizedResource, ResourceIdentity
from drift_detector.state.reader import StateResource


def state_to_normalized(
    resource: StateResource,
    registry: ExtractorRegistry,
) -> NormalizedResource | None:
    mapper = registry.state_mapper(resource.resource_type)
    if mapper is None:
        return None
    external_id = str(resource.attributes.get("id") or resource.attributes.get("arn") or "")
    identity = ResourceIdentity(
        provider=resource.provider,
        resource_type=resource.resource_type,
        name=resource.name,
        module=resource.module.strip("/") if resource.module else "",
        external_id=external_id,
    )
    return NormalizedResource(
        identity=identity,
        attributes=mapper.comparable_attributes(resource.attributes),
        tags=mapper.tags_from_state(resource.attributes),
        source="state",
    )
