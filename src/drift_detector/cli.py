from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

import typer
import uvicorn
from rich.console import Console

from drift_detector.config import AppConfig
from drift_detector.report.formatters import format_table, report_to_json
from drift_detector.scan.runner import ScanRunner
from drift_detector.scan.service import ScanService

app = typer.Typer(
    name="drift",
    help="Detect Terraform configuration drift by comparing state to live cloud APIs.",
    no_args_is_help=True,
)
console = Console()


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


@app.command("scan")
def scan(
    config: Path = typer.Option(
        Path("drift.yaml"),
        "--config",
        "-c",
        help="Path to drift configuration YAML",
        exists=True,
        readable=True,
    ),
    state: Optional[Path] = typer.Option(
        None,
        "--state",
        help="Override Terraform state file path from config",
    ),
    output: OutputFormat = typer.Option(
        OutputFormat.table,
        "--output",
        "-o",
        help="Report output format",
    ),
    out_file: Optional[Path] = typer.Option(
        None,
        "--out",
        help="Write report to file instead of stdout",
    ),
    persist: bool = typer.Option(
        False,
        "--persist/--no-persist",
        help="Store scan report in the configured SQLite database",
    ),
    notify: bool = typer.Option(
        False,
        "--notify/--no-notify",
        help="Send configured webhook notifications",
    ),
    fail_on_drift: bool = typer.Option(
        True,
        "--fail-on-drift/--no-fail-on-drift",
        help="Exit with code 2 when drift is detected",
    ),
) -> None:
    """Run a drift scan for resources defined in Terraform state."""
    cfg = AppConfig.load(config)
    if state is not None:
        cfg.state.path = str(state)

    if cfg.state.backend == "local" and not cfg.state.path:
        console.print("[red]State path is required (config state.path or --state)[/red]")
        raise typer.Exit(code=1)

    if persist or notify:
        report = ScanRunner(cfg, config_path=config).run(persist=persist, notify=notify)
    else:
        report = ScanService(cfg).run()

    if output == OutputFormat.json:
        text = report_to_json(report)
    else:
        text = format_table(report)

    if out_file:
        out_file.write_text(text, encoding="utf-8")
        console.print(f"Report written to {out_file}")
    else:
        console.print(text)

    if fail_on_drift and report.has_drift():
        raise typer.Exit(code=2)
    if report.summary.errors > 0 or report.fetch_errors:
        raise typer.Exit(code=1)


@app.command("serve")
def serve(
    config: Path = typer.Option(
        Path("drift.yaml"),
        "--config",
        "-c",
        help="Path to drift configuration YAML",
        exists=True,
        readable=True,
    ),
) -> None:
    """Start API, dashboard, metrics endpoint, and optional scheduled scans."""
    from drift_detector.api.app import create_app
    from drift_detector.scheduler.service import ScanScheduler

    cfg = AppConfig.load(config)
    scheduler = ScanScheduler(cfg, config_path=config)
    scheduler.start()
    api = create_app(cfg, config_path=config)
    console.print(f"Serving dashboard on http://{cfg.server.host}:{cfg.server.port}")
    try:
        uvicorn.run(api, host=cfg.server.host, port=cfg.server.port, log_level="info")
    finally:
        scheduler.shutdown()


@app.command("types")
def list_types() -> None:
    """List resource types supported for drift comparison."""
    from drift_detector.extract.registry import get_default_registry

    registry = get_default_registry()
    for rtype in registry.supported_types():
        console.print(rtype)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
