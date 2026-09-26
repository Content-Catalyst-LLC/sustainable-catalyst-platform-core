from __future__ import annotations

import hashlib
import json
import math
import os
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
OCTAVE_VERSION = os.environ.get("SC_OCTAVE_VERSION", "8.4.0")
RUNTIME_ID = "sc-runtime-octave"
ADAPTER_ID = "adapter:sc-runtime-octave"
ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
RUNTIME_CONTRACT = "sc.core.octave-runtime.v1"
HOST = os.environ.get("SC_OCTAVE_RUNTIME_HOST", "127.0.0.1")
PORT = int(os.environ.get("SC_OCTAVE_RUNTIME_PORT", "18096"))
OCTAVE_BIN = os.environ.get("SC_OCTAVE_BIN", "/usr/bin/octave-cli")
ARTIFACT_ROOT = Path(os.environ.get("SC_OCTAVE_ARTIFACT_ROOT", "/var/lib/sc-octave-runtime/artifacts"))
WORK_ROOT = Path(os.environ.get("SC_OCTAVE_WORK_ROOT", "/var/lib/sc-octave-runtime/work"))

MAX_DATA_BYTES = int(os.environ.get("SC_OCTAVE_MAX_DATA_BYTES", "5000000"))
MAX_ELEMENTS = int(os.environ.get("SC_OCTAVE_MAX_ELEMENTS", "250000"))
MAX_EXECUTION_SECONDS = int(os.environ.get("SC_OCTAVE_MAX_EXECUTION_SECONDS", "1800"))

OPERATIONS = [
    "matrix_multiply",
    "linear_solve",
    "eigenvalues",
    "svd",
    "fft",
    "polynomial_roots",
]
SAFE_OPERATION = set(OPERATIONS)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def octave_ready() -> bool:
    try:
        p = subprocess.run(
            [OCTAVE_BIN, "--version"],
            capture_output=True, text=True, timeout=10,
        )
        return p.returncode == 0 and "GNU Octave" in (p.stdout + p.stderr)
    except Exception:
        return False


def _numeric_leaf(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    return False


def _count_and_validate(value: Any) -> int:
    if _numeric_leaf(value):
        return 1
    if isinstance(value, list):
        total = 0
        for item in value:
            total += _count_and_validate(item)
        return total
    raise ValueError("Octave payload values must contain only finite numbers and arrays")


def validate_payload(values: Any) -> dict[str, Any]:
    if not isinstance(values, dict) or not values:
        raise ValueError("values must be a non-empty object")
    total = 0
    for key, value in values.items():
        if not isinstance(key, str) or not key:
            raise ValueError("payload keys must be non-empty strings")
        total += _count_and_validate(value)
    if total > MAX_ELEMENTS:
        raise ValueError("payload exceeds maximum numeric element count")
    encoded = json.dumps(values, separators=(",", ":"), sort_keys=True).encode("utf-8")
    if len(encoded) > MAX_DATA_BYTES:
        raise ValueError("payload exceeds maximum serialized size")
    return values


def validate_operation_payload(operation: str, values: dict[str, Any]) -> None:
    if operation == "matrix_multiply":
        required = {"A", "B"}
    elif operation == "linear_solve":
        required = {"A", "b"}
    elif operation in {"eigenvalues", "svd"}:
        required = {"A"}
    elif operation == "fft":
        required = {"x"}
    elif operation == "polynomial_roots":
        required = {"coefficients"}
    else:
        raise ValueError("unsupported Octave operation")

    missing = required - set(values)
    if missing:
        raise ValueError("missing payload field(s): " + ", ".join(sorted(missing)))


def payload_hash(values: dict[str, Any]) -> str:
    encoded = json.dumps(values, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def operation_script(operation: str) -> str:
    common = r"""
args = argv();
input_path = args{1};
output_path = args{2};
raw = fileread(input_path);
d = jsondecode(raw);
"""
    if operation == "matrix_multiply":
        body = r"""
A = d.A;
B = d.B;
value = A * B;
result = struct("operation", "matrix_multiply", "value", value);
"""
    elif operation == "linear_solve":
        body = r"""
A = d.A;
b = d.b;
if isrow(b)
  b = b';
endif
value = A \ b;
residual = norm(A * value - b);
result = struct("operation", "linear_solve", "value", value, "residual_norm", residual);
"""
    elif operation == "eigenvalues":
        body = r"""
A = d.A;
value = eig(A);
result = struct("operation", "eigenvalues", "value", value);
"""
    elif operation == "svd":
        body = r"""
A = d.A;
[U, S, V] = svd(A);
singular_values = diag(S);
result = struct("operation", "svd", "U", U, "singular_values", singular_values, "V", V);
"""
    elif operation == "fft":
        body = r"""
x = d.x;
value = fft(x);
result = struct("operation", "fft", "value", value);
"""
    elif operation == "polynomial_roots":
        body = r"""
coefficients = d.coefficients;
value = roots(coefficients);
result = struct("operation", "polynomial_roots", "value", value);
"""
    else:
        raise ValueError("unsupported Octave operation")

    finish = r"""
fid = fopen(output_path, "w");
if fid < 0
  error("unable to open output file");
endif
fprintf(fid, "%s", jsonencode(result));
fclose(fid);
"""
    return common + body + finish


def execute_octave(
    *,
    operation: str,
    values: dict[str, Any],
    precision_digits: int,
    timeout_seconds: int,
    run_id: str,
) -> dict[str, Any]:
    if not octave_ready():
        raise RuntimeError(f"Octave is not ready at {OCTAVE_BIN}")
    if operation not in SAFE_OPERATION:
        raise ValueError("unsupported Octave operation")

    values = validate_payload(values)
    validate_operation_payload(operation, values)

    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    run_dir = WORK_ROOT / run_id.replace(":", "_")
    run_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir = ARTIFACT_ROOT / run_id.replace(":", "_")
    artifact_dir.mkdir(parents=True, exist_ok=True)

    input_path = run_dir / "input.json"
    script_path = run_dir / "operation.m"
    output_path = artifact_dir / "result.json"
    log_path = artifact_dir / "run.log"

    input_path.write_text(json.dumps(values, sort_keys=True))
    script_path.write_text(operation_script(operation))

    command = [
        OCTAVE_BIN,
        "--quiet",
        "--no-gui",
        "--norc",
        str(script_path),
        str(input_path),
        str(output_path),
    ]

    started = time.monotonic()
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=min(timeout_seconds, MAX_EXECUTION_SECONDS),
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(run_dir),
            "LC_ALL": "C.UTF-8",
        },
    )
    elapsed_ms = int((time.monotonic() - started) * 1000)

    log_path.write_text(
        "COMMAND=" + json.dumps(command) + "\n\nSTDOUT\n" + (proc.stdout or "")
        + "\n\nSTDERR\n" + (proc.stderr or "")
    )

    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "Octave execution failed").strip())
    if not output_path.exists():
        raise RuntimeError("Octave execution produced no result artifact")

    result = json.loads(output_path.read_text())

    return {
        "operation": operation,
        "elapsed_ms": elapsed_ms,
        "precision_digits": precision_digits,
        "input_sha256": payload_hash(values),
        "result": result,
        "artifacts": [
            {
                "artifact_kind": "octave-result-json",
                "path": str(output_path),
                "content_sha256": file_sha256(output_path),
            },
            {
                "artifact_kind": "octave-run-log",
                "path": str(log_path),
                "content_sha256": file_sha256(log_path),
            },
        ],
    }


class PrepareRequest(BaseModel):
    operation: str
    values: dict[str, Any]
    precision_digits: int = Field(default=15, ge=6, le=17)
    timeout_seconds: int = Field(default=120, ge=1, le=1800)
    job_ref: str | None = Field(default=None, max_length=500)
    environment_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        if self.operation not in SAFE_OPERATION:
            raise ValueError("unsupported Octave operation")
        validate_payload(self.values)
        validate_operation_payload(self.operation, self.values)
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
        "native_runtime": "GNU Octave",
        "native_runtime_version": OCTAVE_VERSION,
        "runtime_kind": "language",
        "language": "octave",
        "status": "registered",
        "execution_state": "active" if octave_ready() else "degraded",
        "transport": "HTTP",
        "endpoint": f"http://{HOST}:{PORT}",
        "capabilities": OPERATIONS,
        "lifecycle_methods": [
            "health", "version", "capabilities", "prepare", "execute",
            "cancel", "inspect", "collect_results", "collect_artifacts", "diagnose",
        ],
        "boundaries": {
            "arbitrary_octave_source": False,
            "shell_execution": False,
            "runtime_package_install": False,
            "caller_filesystem_paths": False,
        },
    }


app = FastAPI(title="Sustainable Catalyst Octave Runtime", version=PROVIDER_VERSION)


@app.get("/health")
def health():
    return {
        "ok": octave_ready(),
        "runtime_id": RUNTIME_ID,
        "version": PROVIDER_VERSION,
        "octave_version": OCTAVE_VERSION,
        "octave_bin": OCTAVE_BIN,
        "capabilities": len(OPERATIONS),
    }


@app.get("/version")
def version():
    return {"runtime_id": RUNTIME_ID, "version": PROVIDER_VERSION, "octave_version": OCTAVE_VERSION}


@app.get("/capabilities")
def capabilities():
    return {"runtime_id": RUNTIME_ID, "version": PROVIDER_VERSION, "operations": OPERATIONS}


@app.get("/v1/core-adapter")
def core_adapter():
    return adapter_descriptor()


@app.post("/v1/core-adapter/prepare")
def prepare(body: PrepareRequest):
    run_id = f"octave-run:{uuid.uuid4()}"
    RUNS[run_id] = RunRecord(run_id=run_id, request=body)
    return {
        "ok": True,
        "run_id": run_id,
        "status": "prepared",
        "operation": body.operation,
        "runtime_id": RUNTIME_ID,
        "runtime_version": PROVIDER_VERSION,
        "input_sha256": payload_hash(body.values),
    }


@app.post("/v1/core-adapter/execute")
def execute(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    if record.status == "cancelled":
        raise HTTPException(status_code=409, detail="run is cancelled")
    if record.status == "completed":
        return {"ok": True, "run_id": record.run_id, "status": record.status, "result": record.result}

    record.status = "running"
    record.started_at = now_iso()
    req = record.request
    try:
        record.result = execute_octave(
            operation=req.operation,
            values=req.values,
            precision_digits=req.precision_digits,
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
        record.error = "Octave execution timed out"
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
        raise HTTPException(status_code=409, detail="v1 synchronous provider cannot interrupt an already-running process")
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
        "ok": True, "run_id": record.run_id, "status": record.status,
        "operation": record.request.operation, "job_ref": record.request.job_ref,
        "environment_ref": record.request.environment_ref,
        "created_at": record.created_at, "started_at": record.started_at,
        "completed_at": record.completed_at, "error": record.error,
    }


@app.post("/v1/core-adapter/collect-results")
def collect_results(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    return {"ok": True, "run_id": record.run_id, "status": record.status, "result": record.result}


@app.post("/v1/core-adapter/collect-artifacts")
def collect_artifacts(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    artifacts = list((record.result or {}).get("artifacts") or [])
    return {"ok": True, "run_id": record.run_id, "status": record.status, "artifacts": artifacts}


@app.post("/v1/core-adapter/diagnose")
def diagnose(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "ok": True, "run_id": record.run_id, "status": record.status,
        "runtime_ready": octave_ready(), "error": record.error,
        "result": (record.result or {}).get("result"),
    }
