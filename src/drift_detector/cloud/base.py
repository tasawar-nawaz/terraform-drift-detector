from __future__ import annotations

from typing import Protocol

from drift_detector.extract.registry import ExtractorRegistry
from drift_detector.model.resources import NormalizedResource


class CloudFetcher(Protocol):
    provider: str

    def fetch_one(self, expected: NormalizedResource) -> tuple[NormalizedResource | None, str | None]: ...


def fetch_actual_resources(
    expected_list: list[NormalizedResource],
    fetchers: dict[str, CloudFetcher],
    registry: ExtractorRegistry,
) -> tuple[dict[str, NormalizedResource], list[str], int]:
    actual_map: dict[str, NormalizedResource] = {}
    errors: list[str] = []
    error_count = 0

    for expected in expected_list:
        provider = expected.identity.provider
        fetcher = fetchers.get(provider)
        if fetcher is None:
            errors.append(
                f"{expected.identity.display_address()}: no cloud fetcher for provider '{provider}'"
            )
            error_count += 1
            continue
        actual, err = fetcher.fetch_one(expected)
        if err:
            errors.append(f"{expected.identity.display_address()}: {err}")
            error_count += 1
            continue
        if actual is not None:
            actual_map[expected.identity.key()] = actual

    return actual_map, errors, error_count
