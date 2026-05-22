"""Background pipeline jobs with log streaming."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from ..config import PROJECT_ROOT, load_config, paths_from_config
from ..safe_io import read_json, read_utf8


class JobMode(str, Enum):
    FULL = "full"
    QUANTIZE = "quantize"
    BENCHMARK = "benchmark"
    VALIDATE = "validate"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


MODE_SCRIPTS: dict[JobMode, str] = {
    JobMode.FULL: "run_optimization.ps1",
    JobMode.QUANTIZE: "quantize_only.ps1",
}


@dataclass
class Job:
    id: str
    profile: str
    mode: JobMode
    status: JobStatus = JobStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str | None = None
    exit_code: int | None = None
    log_path: Path | None = None
    error: str | None = None
    _lines: deque[str] = field(default_factory=lambda: deque(maxlen=5000))
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _process: subprocess.Popen[str] | None = field(default=None, repr=False)
    _thread: threading.Thread | None = field(default=None, repr=False)

    def append_line(self, line: str) -> None:
        with self._lock:
            self._lines.append(line)

    def get_lines(self, after: int = 0) -> tuple[list[str], int]:
        with self._lock:
            lines = list(self._lines)
        if after < len(lines):
            return lines[after:], len(lines)
        return [], len(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "profile": self.profile,
            "mode": self.mode.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
            "exit_code": self.exit_code,
            "error": self.error,
            "log_path": str(self.log_path) if self.log_path else None,
        }


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._current_id: str | None = None

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def current(self) -> Job | None:
        with self._lock:
            if self._current_id:
                return self._jobs.get(self._current_id)
        return None

    def list_jobs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [j.to_dict() for j in jobs[:limit]]

    def start(self, profile: str, mode: JobMode) -> Job:
        with self._lock:
            if self._current_id:
                cur = self._jobs.get(self._current_id)
                if cur and cur.status == JobStatus.RUNNING:
                    raise RuntimeError("Another job is already running")

        job_id = uuid.uuid4().hex[:12]
        cfg = load_config(profile)
        paths = paths_from_config(cfg)
        logs_dir = paths["logs"]
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / f"web-job-{job_id}.log"

        job = Job(id=job_id, profile=profile, mode=mode, log_path=log_path)
        with self._lock:
            self._jobs[job_id] = job
            self._current_id = job_id

        thread = threading.Thread(target=self._run_job, args=(job,), daemon=True)
        job._thread = thread
        thread.start()
        return job

    def _run_job(self, job: Job) -> None:
        job.status = JobStatus.RUNNING
        job.append_line(f"[{job.mode.value}] Starting profile={job.profile}")

        try:
            if job.mode == JobMode.VALIDATE:
                exit_code = self._run_python_cli(job, ["validate", "--smoke-test"])
            elif job.mode == JobMode.BENCHMARK:
                exit_code = self._run_python_cli(job, ["benchmark"])
            else:
                exit_code = self._run_powershell(job)
            job.exit_code = exit_code
            job.status = JobStatus.SUCCESS if exit_code == 0 else JobStatus.FAILED
            if exit_code != 0:
                job.error = f"Process exited with code {exit_code}"
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
            job.append_line(f"ERROR: {exc}")
            job.exit_code = 1
        finally:
            job.finished_at = datetime.now(timezone.utc).isoformat()
            with self._lock:
                if self._current_id == job.id:
                    self._current_id = None
            job.append_line(f"[done] status={job.status.value}")

    def _run_powershell(self, job: Job) -> int:
        script_name = MODE_SCRIPTS.get(job.mode)
        if not script_name:
            raise ValueError(f"Unknown mode: {job.mode}")
        script = PROJECT_ROOT / script_name
        if not script.exists():
            raise FileNotFoundError(f"Script not found: {script}")

        env = os.environ.copy()
        env["QUANTFORGE_PROFILE"] = job.profile

        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ]
        job.append_line(f"$ {' '.join(cmd)}")

        with open(job.log_path, "w", encoding="utf-8") as log_file:
            proc = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            job._process = proc
            assert proc.stdout is not None
            for line in proc.stdout:
                line = line.rstrip("\n\r")
                job.append_line(line)
                log_file.write(line + "\n")
                log_file.flush()
            return proc.wait()

    def _run_python_cli(self, job: Job, args: list[str]) -> int:
        venv_py = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
        python = str(venv_py) if venv_py.exists() else "python"
        cmd = [python, "-m", "quantforge", *args, "--profile", job.profile]
        job.append_line(f"$ {' '.join(cmd)}")
        env = os.environ.copy()
        env["QUANTFORGE_PROFILE"] = job.profile

        with open(job.log_path, "w", encoding="utf-8") as log_file:
            proc = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            job._process = proc
            assert proc.stdout is not None
            for line in proc.stdout:
                line = line.rstrip("\n\r")
                job.append_line(line)
                log_file.write(line + "\n")
                log_file.flush()
            return proc.wait()


def docker_available() -> bool:
    try:
        r = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=15,
            cwd=str(PROJECT_ROOT),
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def load_artifacts(profile: str) -> dict[str, Any]:
    cfg = load_config(profile)
    paths = paths_from_config(cfg)
    gguf = paths["gguf"]
    metrics_dir = paths["metrics"]
    result: dict[str, Any] = {
        "profile": profile,
        "gguf": None,
        "manifest": None,
        "benchmark": None,
        "report_url": None,
    }

    if gguf.exists():
        result["gguf"] = {
            "name": gguf.name,
            "size_bytes": gguf.stat().st_size,
            "download_url": f"/api/download/{gguf.name}",
        }

    manifest_path = paths["models"] / "manifest.json"
    manifest_data = read_json(manifest_path, root=paths["root"], default=None)
    if manifest_data:
        result["manifest"] = manifest_data

    bench_path = metrics_dir / "benchmark_results.json"
    bench_data = read_json(bench_path, root=paths["root"], default=None)
    if bench_data:
        result["benchmark"] = bench_data

    report_path = metrics_dir / "report.md"
    if report_path.exists():
        result["report_url"] = "/api/report"

    return result


def safe_gguf_path(filename: str) -> Path | None:
    if ".." in filename or "/" in filename or "\\" in filename:
        return None
    if not filename.endswith(".gguf"):
        return None
    models = (PROJECT_ROOT / "models").resolve()
    path = (models / filename).resolve()
    try:
        path.relative_to(models)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return path


# Global manager for the dashboard process
manager = JobManager()
