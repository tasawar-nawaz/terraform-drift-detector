# Extending Terraform Drift Detector

## Add a resource type

1. Implement a **state mapper** (`comparable_attributes`, `tags_from_state`).
2. Implement a **cloud mapper** (`map_from_cloud`).
3. Register both in the provider's `register_*_mappers()` function.
4. Add **fetch logic** in the provider's cloud fetcher (`_fetch_raw`).

Supported providers:

| Provider key | Config section | Fetcher |
|--------------|----------------|---------|
| `aws` | `aws` | `AwsCloudFetcher` |
| `azurerm` | `azure` | `AzureCloudFetcher` |
| `google` | `gcp` | `GcpCloudFetcher` |

Terraform state `provider` values are normalized to these keys (for example `hashicorp/aws` -> `aws`).

## Optional dependencies

```bash
pip install "terraform-drift-detector[azure]"
pip install "terraform-drift-detector[gcp]"
pip install "terraform-drift-detector[server]"
```

## Comparison profiles

Configure under `scan.comparison`:

- `default` — compare attributes and tags; honor `ignore_attribute_paths`
- `tags_only` — tag drift only
- Use `ignore_attribute_paths` to suppress noisy fields

## Remote state

```yaml
state:
  backend: s3
  bucket: my-tf-state
  key: env/prod/terraform.tfstate
  region: us-east-1
  profile: ops
```

## Operations

- `drift scan --persist --notify` — SQLite history + webhooks
- `drift serve` — dashboard, REST API, Prometheus `/metrics`, cron scheduler
