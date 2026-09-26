from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

PROVIDER_VERSION = "1.0.0"
CMDSTAN_VERSION = os.environ.get("SC_STAN_CMDSTAN_VERSION", "2.36.0")
RUNTIME_ID = "sc-runtime-stan"
ADAPTER_ID = "adapter:sc-runtime-stan"
ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
RUNTIME_CONTRACT = "sc.core.stan-runtime.v1"
HOST = os.environ.get("SC_STAN_RUNTIME_HOST", "127.0.0.1")
PORT = int(os.environ.get("SC_STAN_RUNTIME_PORT", "18095"))

CMDSTAN_HOME = Path(
    os.environ.get(
        "SC_STAN_CMDSTAN_HOME",
        f"/opt/sustainable-catalyst/stan-runtime/.cmdstan/cmdstan-{CMDSTAN_VERSION}",
    )
)
ARTIFACT_ROOT = Path(
    os.environ.get(
        "SC_STAN_ARTIFACT_ROOT",
        "/var/lib/sc-stan-runtime/artifacts",
    )
)
MODEL_ROOT = Path(
    os.environ.get(
        "SC_STAN_MODEL_ROOT",
        "/var/lib/sc-stan-runtime/models",
    )
)

MAX_SOURCE_BYTES = int(os.environ.get("SC_STAN_MAX_SOURCE_BYTES", "200000"))
MAX_DATA_BYTES = int(os.environ.get("SC_STAN_MAX_DATA_BYTES", "5000000"))
MAX_EXECUTION_SECONDS = int(os.environ.get("SC_STAN_MAX_EXECUTION_SECONDS", "3600"))
MAX_COMPILE_SECONDS = int(os.environ.get("SC_STAN_MAX_COMPILE_SECONDS", "900"))

OPERATIONS = [
    "compile_model",
    "sample",
    "optimize",
    "variational",
    "diagnose",
]
SAFE_OPERATION = set(OPERATIONS)
SAFE_MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
FORBIDDEN_SOURCE_PATTERNS = [
    re.compile(r"(?im)^\s*#\s*include\b"),
]
SAFE_EXTRA_OPTIONS = {
    "adapt_delta",
    "max_treedepth",
    "stepsize",
    "iter",
    "output_samples",
    "algorithm",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def cmdstan_ready() -> bool:
    return (
        CMDSTAN_HOME.exists()
        and (CMDSTAN_HOME / "bin" / "stanc").exists()
        and (CMDSTAN_HOME / "makefile").exists()
    )


def validate_model_source(source: str) -> str:
    if not isinstance(source, str) or not source.strip():
        raise ValueError("model_source must be a non-empty string")
    encoded = source.encode("utf-8")
    if len(encoded) > MAX_SOURCE_BYTES:
        raise ValueError("model_source exceeds maximum size")
    for pattern in FORBIDDEN_SOURCE_PATTERNS:
        if pattern.search(source):
            raise ValueError("Stan #include directives are not allowed")
    return source


def validate_data(data: Any) -> dict[str, Any]:
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("data must be an object")
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_DATA_BYTES:
        raise ValueError("data exceeds maximum serialized size")
    return data


def validate_options(options: Any) -> dict[str, Any]:
    if options is None:
        return {}
    if not isinstance(options, dict):
        raise ValueError("options must be an object")
    unknown = set(options) - SAFE_EXTRA_OPTIONS
    if unknown:
        raise ValueError("unsupported Stan option(s): " + ", ".join(sorted(unknown)))
    out: dict[str, Any] = {}
    for key, value in options.items():
        if key in {"adapt_delta", "stepsize"}:
            number = float(value)
            if not math.isfinite(number) or number <= 0:
                raise ValueError(f"{key} must be a positive finite number")
            if key == "adapt_delta" and number > 1:
                raise ValueError("adapt_delta must be <= 1")
            out[key] = number
        elif key in {"max_treedepth", "iter", "output_samples"}:
            number = int(value)
            if number < 1 or number > 100000:
                raise ValueError(f"{key} out of range")
            out[key] = number
        elif key == "algorithm":
            value = str(value)
            if value not in {"meanfield", "fullrank", "lbfgs", "bfgs", "newton"}:
                raise ValueError("unsupported algorithm")
            out[key] = value
    return out


def source_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def model_paths(source: str) -> tuple[Path, Path]:
    digest = source_hash(source)
    model_dir = MODEL_ROOT / digest
    return model_dir / "model.stan", model_dir / "model"


def compile_model(source: str) -> dict[str, Any]:
    if not cmdstan_ready():
        raise RuntimeError(f"CmdStan is not ready at {CMDSTAN_HOME}")
    source = validate_model_source(source)
    stan_path, exe_path = model_paths(source)
    stan_path.parent.mkdir(parents=True, exist_ok=True)
    if not stan_path.exists() or stan_path.read_text() != source:
        stan_path.write_text(source)
    if not exe_path.exists():
        proc = subprocess.run(
            ["make", str(exe_path)],
            cwd=str(CMDSTAN_HOME),
            capture_output=True,
            text=True,
            timeout=MAX_COMPILE_SECONDS,
        )
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout or "Stan compilation failed").strip())
    return {
        "model_source_sha256": source_hash(source),
        "stan_path": str(stan_path),
        "executable_path": str(exe_path),
        "executable_sha256": file_sha256(exe_path),
    }


def _option_tokens(operation: str, options: dict[str, Any]) -> list[str]:
    tokens: list[str] = []
    if operation == "sample":
        if "adapt_delta" in options:
            tokens += ["adapt", f"delta={options['adapt_delta']}"]
        if "max_treedepth" in options:
            tokens += ["algorithm=hmc", "engine=nuts", f"max_depth={options['max_treedepth']}"]
        if "stepsize" in options:
            tokens += [f"stepsize={options['stepsize']}"]
    elif operation == "optimize" and "algorithm" in options:
        tokens += [f"algorithm={options['algorithm']}"]
    elif operation == "variational":
        if "algorithm" in options:
            tokens += [f"algorithm={options['algorithm']}"]
        if "iter" in options:
            tokens += [f"iter={options['iter']}"]
        if "output_samples" in options:
            tokens += [f"output_samples={options['output_samples']}"]
    return tokens


def build_command(
    executable: Path,
    operation: str,
    data_path: Path,
    output_path: Path,
    *,
    seed: int,
    num_warmup: int,
    num_samples: int,
    thin: int,
    refresh: int,
    options: dict[str, Any],
) -> list[str]:
    if operation not in SAFE_OPERATION:
        raise ValueError(f"unsupported Stan operation: {operation}")
    if operation == "compile_model":
        return [str(executable)]

    command = [str(executable), operation]
    if operation == "sample":
        command += [
            f"num_warmup={num_warmup}",
            f"num_samples={num_samples}",
            f"thin={thin}",
        ]
    command += _option_tokens(operation, options)
    command += [
        "data", f"file={data_path}",
        "random", f"seed={seed}",
        "output", f"file={output_path}", f"refresh={refresh}",
    ]
    return command


def csv_summary(path: Path) -> dict[str, Any]:
    columns: list[str] = []
    rows = 0
    with path.open(newline="") as handle:
        filtered = (line for line in handle if not line.startswith("#"))
        reader = csv.reader(filtered)
        try:
            columns = next(reader)
        except StopIteration:
            columns = []
        for _ in reader:
            rows += 1
    return {
        "columns": columns,
        "row_count": rows,
        "content_sha256": file_sha256(path),
        "size_bytes": path.stat().st_size,
    }


def execute_stan(
    *,
    operation: str,
    model_source: str,
    data: dict[str, Any],
    seed: int,
    num_warmup: int,
    num_samples: int,
    thin: int,
    refresh: int,
    options: dict[str, Any],
    timeout_seconds: int,
    run_id: str,
) -> dict[str, Any]:
    compiled = compile_model(model_source)
    exe = Path(compiled["executable_path"])
    if operation == "compile_model":
        return {
            "operation": operation,
            "compiled_model": compiled,
            "artifacts": [],
        }

    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    run_dir = ARTIFACT_ROOT / run_id.replace(":", "_")
    run_dir.mkdir(parents=True, exist_ok=True)

    data_path = run_dir / "data.json"
    output_path = run_dir / "output.csv"
    log_path = run_dir / "run.log"
    data_path.write_text(json.dumps(validate_data(data), sort_keys=True))

    command = build_command(
        exe,
        operation,
        data_path,
        output_path,
        seed=seed,
        num_warmup=num_warmup,
        num_samples=num_samples,
        thin=thin,
        refresh=refresh,
        options=validate_options(options),
    )

    started = time.monotonic()
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=min(timeout_seconds, MAX_EXECUTION_SECONDS),
    )
    elapsed_ms = int((time.monotonic() - started) * 1000)
    log_path.write_text(
        "COMMAND=" + json.dumps(command) + "\n\nSTDOUT\n" + (proc.stdout or "")
        + "\n\nSTDERR\n" + (proc.stderr or "")
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "Stan execution failed").strip())

    summary = csv_summary(output_path) if output_path.exists() else {
        "columns": [],
        "row_count": 0,
        "content_sha256": None,
        "size_bytes": 0,
    }
    artifacts = [
        {
            "artifact_kind": "stan-run-log",
            "path": str(log_path),
            "content_sha256": file_sha256(log_path),
        }
    ]
    if output_path.exists():
        artifacts.append(
            {
                "artifact_kind": "stan-sample-csv",
                "path": str(output_path),
                "content_sha256": file_sha256(output_path),
            }
        )

    return {
        "operation": operation,
        "elapsed_ms": elapsed_ms,
        "compiled_model": compiled,
        "output_summary": summary,
        "artifacts": artifacts,
    }


class PrepareRequest(BaseModel):
    operation: str
    model_id: str = Field(min_length=2, max_length=200)
    model_source: str = Field(min_length=8, max_length=200_000)
    data: dict[str, Any] = Field(default_factory=dict)
    seed: int = Field(default=12345, ge=1, le=2_147_483_647)
    chains: int = Field(default=1, ge=1, le=1)
    num_warmup: int = Field(default=500, ge=0, le=10_000)
    num_samples: int = Field(default=1000, ge=1, le=50_000)
    thin: int = Field(default=1, ge=1, le=100)
    refresh: int = Field(default=0, ge=0, le=10_000)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    options: dict[str, Any] = Field(default_factory=dict)
    job_ref: str | None = Field(default=None, max_length=500)
    environment_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        if self.operation not in SAFE_OPERATION:
            raise ValueError("unsupported Stan operation")
        if not SAFE_MODEL_ID.fullmatch(self.model_id):
            raise ValueError("invalid model_id")
        validate_model_source(self.model_source)
        validate_data(self.data)
        validate_options(self.options)
        if self.operation != "compile_model" and not self.data:
            raise ValueError("Stan execution requires data")
        return self


class RunRequest(BaseModel):
    run_id: str = Field(min_length=2, max_length=500)


@dataclass
class RunRecord:
    run_id: str
    request: PrepareRequest
    status: str = "prepared"
    created_at: str = field(default_factory=now_iso)
    started_at: str | None = None
    completed_at: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


RUNS: dict[str, RunRecord] = {}


def adapter_descriptor() -> dict[str, Any]:
    return {
        "adapter_id": ADAPTER_ID,
        "adapter_contract": ADAPTER_CONTRACT,
        "provider_id": RUNTIME_ID,
        "provider_version": PROVIDER_VERSION,
        "native_runtime": "CmdStan",
        "native_runtime_version": CMDSTAN_VERSION,
        "runtime_kind": "domain",
        "language": "stan",
        "status": "registered",
        "execution_state": "active" if cmdstan_ready() else "degraded",
        "transport": "HTTP",
        "endpoint": f"http://{HOST}:{PORT}",
        "capabilities": OPERATIONS,
        "lifecycle_methods": [
            "health",
            "version",
            "capabilities",
            "prepare",
            "execute",
            "cancel",
            "inspect",
            "collect_results",
            "collect_artifacts",
            "diagnose",
        ],
        "boundaries": {
            "arbitrary_shell": False,
            "runtime_package_install": False,
            "stan_include_directives": False,
            "external_cpp_extensions": False,
            "multi_chain_parallel_v1": False,
        },
    }


app = FastAPI(title="Sustainable Catalyst Stan Runtime", version=PROVIDER_VERSION)


@app.get("/health")
def health():
    return {
        "ok": cmdstan_ready(),
        "runtime_id": RUNTIME_ID,
        "version": PROVIDER_VERSION,
        "cmdstan_version": CMDSTAN_VERSION,
        "cmdstan_home": str(CMDSTAN_HOME),
        "stanc": str(CMDSTAN_HOME / "bin" / "stanc"),
        "capabilities": len(OPERATIONS),
    }


@app.get("/version")
def version():
    return {
        "runtime_id": RUNTIME_ID,
        "version": PROVIDER_VERSION,
        "cmdstan_version": CMDSTAN_VERSION,
    }


@app.get("/capabilities")
def capabilities():
    return {
        "runtime_id": RUNTIME_ID,
        "version": PROVIDER_VERSION,
        "operations": OPERATIONS,
    }


@app.get("/v1/core-adapter")
def core_adapter():
    return adapter_descriptor()


@app.post("/v1/core-adapter/prepare")
def prepare(body: PrepareRequest):
    run_id = f"stan-run:{uuid.uuid4()}"
    RUNS[run_id] = RunRecord(run_id=run_id, request=body)
    return {
        "ok": True,
        "run_id": run_id,
        "status": "prepared",
        "operation": body.operation,
        "runtime_id": RUNTIME_ID,
        "runtime_version": PROVIDER_VERSION,
        "model_source_sha256": source_hash(body.model_source),
    }


@app.post("/v1/core-adapter/execute")
def execute(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    if record.status == "cancelled":
        raise HTTPException(status_code=409, detail="run is cancelled")
    if record.status == "completed":
        return {
            "ok": True,
            "run_id": record.run_id,
            "status": record.status,
            "result": record.result,
        }

    record.status = "running"
    record.started_at = now_iso()
    req = record.request
    try:
        record.result = execute_stan(
            operation=req.operation,
            model_source=req.model_source,
            data=req.data,
            seed=req.seed,
            num_warmup=req.num_warmup,
            num_samples=req.num_samples,
            thin=req.thin,
            refresh=req.refresh,
            options=req.options,
            timeout_seconds=req.timeout_seconds,
            run_id=record.run_id,
        )
        record.status = "completed"
        record.completed_at = now_iso()
        return {
            "ok": True,
            "run_id": record.run_id,
            "status": record.status,
            "runtime_id": RUNTIME_ID,
            "runtime_version": PROVIDER_VERSION,
            "result": record.result,
        }
    except subprocess.TimeoutExpired:
        record.status = "failed"
        record.error = "Stan execution timed out"
        record.completed_at = now_iso()
        raise HTTPException(status_code=504, detail=record.error)
    except Exception as exc:
        record.status = "failed"
        record.error = str(exc)
        record.completed_at = now_iso()
        raise HTTPException(status_code=500, detail=record.error)


@app.post("/v1/core-adapter/cancel")
def cancel(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    if record.status == "running":
        raise HTTPException(
            status_code=409,
            detail="v1 synchronous provider cannot interrupt an already-running process",
        )
    if record.status in {"completed", "failed"}:
        return {"ok": True, "run_id": record.run_id, "status": record.status}
    record.status = "cancelled"
    record.completed_at = now_iso()
    return {"ok": True, "run_id": record.run_id, "status": record.status}


@app.post("/v1/core-adapter/inspect")
def inspect(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "ok": True,
        "run_id": record.run_id,
        "status": record.status,
        "operation": record.request.operation,
        "job_ref": record.request.job_ref,
        "environment_ref": record.request.environment_ref,
        "created_at": record.created_at,
        "started_at": record.started_at,
        "completed_at": record.completed_at,
        "error": record.error,
    }


@app.post("/v1/core-adapter/collect-results")
def collect_results(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "ok": True,
        "run_id": record.run_id,
        "status": record.status,
        "result": record.result,
    }


@app.post("/v1/core-adapter/collect-artifacts")
def collect_artifacts(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    artifacts = []
    if record.result:
        artifacts = list(record.result.get("artifacts") or [])
    return {
        "ok": True,
        "run_id": record.run_id,
        "status": record.status,
        "artifacts": artifacts,
    }


@app.post("/v1/core-adapter/diagnose")
def diagnose(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "ok": True,
        "run_id": record.run_id,
        "status": record.status,
        "runtime_ready": cmdstan_ready(),
        "error": record.error,
        "result_summary": (
            record.result.get("output_summary")
            if record.result and isinstance(record.result, dict)
            else None
        ),
    }
