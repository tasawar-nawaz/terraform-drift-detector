from __future__ import annotations

from drift_detector.cloud.aws import AwsCloudFetcher
from drift_detector.cloud.azure import AzureCloudFetcher
from drift_detector.cloud.base import CloudFetcher
from drift_detector.cloud.gcp import GcpCloudFetcher
from drift_detector.config import AppConfig
from drift_detector.extract.registry import ExtractorRegistry


def build_cloud_fetchers(config: AppConfig, registry: ExtractorRegistry) -> dict[str, CloudFetcher]:
    fetchers: dict[str, CloudFetcher] = {}
    if config.aws.enabled:
        fetchers["aws"] = AwsCloudFetcher(config.aws, registry)
    if config.azure.enabled:
        fetchers["azurerm"] = AzureCloudFetcher(config.azure, registry)
    if config.gcp.enabled:
        fetchers["google"] = GcpCloudFetcher(config.gcp, registry)
    return fetchers
