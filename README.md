# Terraform Drift Detector

Compare **Terraform state** against **live cloud APIs** to find configuration drift without running `terraform plan` or `terraform apply`.

## Architecture

```
Terraform State -> State Reader -> Extractor -> Expected Model --+
                                                                 +-> Drift Engine -> Report
Cloud APIs      -> Cloud Fetcher -> Extractor -> Actual Model  --+
```

## Features

- Local or **S3** Terraform state backends
- AWS (default), optional **Azure** and **GCP** fetchers
- Normalized attribute and tag comparison with **comparison profiles**
- CLI (table + JSON), **SQLite scan history**, **webhooks**
- **Dashboard + REST API**, **Prometheus metrics**, **cron scheduling**

## Install

```bash
pip install -e ".[dev]"
pip install -e ".[azure]"   # optional
pip install -e ".[gcp]"     # optional
```

## CLI

```bash
drift types
drift scan -c configs/example-drift.yaml
drift scan -c configs/example-drift.yaml -o json --out report.json
drift scan -c configs/example-drift.yaml --persist --notify
drift serve -c configs/example-drift.yaml
```

## Dashboard and API

`drift serve` exposes:

| Endpoint | Description |
|----------|-------------|
| `/` | Web dashboard |
| `/api/scans` | List stored scans |
| `/api/scans/{id}` | Scan report JSON |
| `/api/scans/run` | Trigger scan (POST) |
| `/metrics` | Prometheus metrics |
| `/health` | Health check |

Set `server.api_key` in config to require `X-API-Key` on API and metrics routes.

## Configuration

See `configs/example-drift.yaml` and `docs/EXTENDING.md`.

## Tests

```bash
pytest
```

## Exit codes

- `0` — no drift
- `1` — fetch/config errors
- `2` — drift detected (`--fail-on-drift`, default)
.............................................................