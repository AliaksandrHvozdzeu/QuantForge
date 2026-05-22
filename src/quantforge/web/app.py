"""FastAPI web dashboard."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..config import PROJECT_ROOT, list_profiles, load_config, paths_from_config
from .jobs import (
    JobMode,
    JobStatus,
    docker_available,
    load_artifacts,
    manager,
    safe_gguf_path,
)

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="QuantForge Dashboard", version="0.5.0")


class StartJobRequest(BaseModel):
    profile: str = Field(..., min_length=1)
    mode: str = Field(default="full", pattern="^(full|quantize|benchmark|validate)$")


def _profile_info(name: str) -> dict[str, Any]:
    cfg = load_config(name)
    model = cfg.get("model", {})
    paths = paths_from_config(cfg)
    gguf = paths["gguf"]
    return {
        "id": name,
        "display_name": model.get("display_name", name),
        "repo": model.get("repo", ""),
        "quantize_type": cfg.get("quantize_type", ""),
        "gguf_output": model.get("gguf_output", ""),
        "gguf_exists": gguf.exists(),
        "gguf_size_bytes": gguf.stat().st_size if gguf.exists() else None,
    }


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    html_path = STATIC_DIR / "index.html"
    if not html_path.exists():
        raise HTTPException(404, "Dashboard UI not found")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "docker": docker_available(),
        "project_root": str(PROJECT_ROOT),
    }


@app.get("/api/profiles")
async def profiles() -> list[dict[str, Any]]:
    return [_profile_info(p) for p in list_profiles()]


@app.get("/api/status")
async def status() -> dict[str, Any]:
    current = manager.current()
    return {
        "docker": docker_available(),
        "current_job": current.to_dict() if current else None,
        "jobs": manager.list_jobs(10),
    }


@app.post("/api/jobs")
async def start_job(body: StartJobRequest) -> dict[str, Any]:
    if body.mode in ("full", "quantize") and not docker_available():
        raise HTTPException(503, "Docker is not running. Start Docker Desktop first.")

    try:
        mode = JobMode(body.mode)
        job = manager.start(body.profile, mode)
        return job.to_dict()
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str) -> dict[str, Any]:
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    data = job.to_dict()
    if job.status in (JobStatus.SUCCESS, JobStatus.FAILED):
        data["artifacts"] = load_artifacts(job.profile)
    return data


@app.get("/api/jobs/{job_id}/stream")
async def stream_job(job_id: str) -> StreamingResponse:
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    async def event_generator():
        offset = 0
        while True:
            lines, offset = job.get_lines(offset)
            for line in lines:
                payload = json.dumps({"line": line}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
            if job.status not in (JobStatus.PENDING, JobStatus.RUNNING):
                done = json.dumps(
                    {
                        "done": True,
                        "status": job.status.value,
                        "exit_code": job.exit_code,
                        "error": job.error,
                    },
                    ensure_ascii=False,
                )
                yield f"data: {done}\n\n"
                break
            await asyncio.sleep(0.4)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/artifacts")
async def artifacts(profile: str) -> dict[str, Any]:
    try:
        return load_artifacts(profile)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/download/{filename}")
async def download_gguf(filename: str) -> FileResponse:
    path = safe_gguf_path(filename)
    if not path:
        raise HTTPException(404, "File not found or not allowed")
    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=path.name,
    )


@app.get("/api/report")
async def download_report(profile: str = "qwen2.5-coder-7b") -> FileResponse:
    cfg = load_config(profile)
    report = paths_from_config(cfg)["metrics"] / "report.md"
    if not report.exists():
        raise HTTPException(404, "Report not found")
    return FileResponse(report, media_type="text/markdown", filename="report.md")


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
