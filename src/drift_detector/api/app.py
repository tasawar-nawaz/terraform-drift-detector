from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from drift_detector.config import AppConfig
from drift_detector.observability.metrics import metrics_registry
from drift_detector.report.formatters import report_to_dict
from drift_detector.scan.runner import ScanRunner


def _verify_api_key(request: Request, config: AppConfig) -> None:
    if not config.server.api_key:
        return
    provided = request.headers.get("x-api-key") or request.query_params.get("api_key")
    if provided != config.server.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def create_app(config: AppConfig, config_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Terraform Drift Detector", version="1.0.0")
    runner = ScanRunner(config, config_path=config_path)

    static_dir = Path(__file__).resolve().parent.parent / "web" / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> HTMLResponse:
        index = static_dir / "index.html"
        if not index.exists():
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return HTMLResponse(index.read_text(encoding="utf-8"))

    @app.get("/metrics")
    def metrics(request: Request) -> PlainTextResponse:
        _verify_api_key(request, config)
        return PlainTextResponse(metrics_registry.render_prometheus())

    @app.get("/api/scans")
    def list_scans(request: Request, limit: int = 50) -> list[dict]:
        _verify_api_key(request, config)
        return runner.repository.list_scans(limit=limit)

    @app.get("/api/scans/{scan_id}")
    def get_scan(scan_id: str, request: Request) -> dict:
        _verify_api_key(request, config)
        report = runner.repository.get_scan(scan_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Scan not found")
        return report

    @app.post("/api/scans/run")
    def run_scan(request: Request) -> dict:
        _verify_api_key(request, config)
        report = runner.run(persist=True, notify=True)
        return report_to_dict(report)

    return app
