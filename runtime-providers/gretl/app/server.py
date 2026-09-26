from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

PROVIDER_VERSION = "1.0.0"
GRETL_VERSION = os.environ.get("SC_GRETL_VERSION", "2023c")
GRETL_PACKAGE_VERSION = os.environ.get("SC_GRETL_PACKAGE_VERSION", "2023c-2.1build3")
RUNTIME_ID = "sc-runtime-gretl"
ADAPTER_ID = "adapter:sc-runtime-gretl"
ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
RUNTIME_CONTRACT = "sc.core.gretl-hansl-runtime.v1"
HOST = os.environ.get("SC_GRETL_RUNTIME_HOST", "127.0.0.1")
PORT = int(os.environ.get("SC_GRETL_RUNTIME_PORT", "18097"))
GRETL_BIN = os.environ.get("SC_GRETL_BIN", "/usr/bin/gretlcli")
ARTIFACT_ROOT = Path(os.environ.get("SC_GRETL_ARTIFACT_ROOT", "/var/lib/sc-gretl-runtime/artifacts"))
WORK_ROOT = Path(os.environ.get("SC_GRETL_WORK_ROOT", "/var/lib/sc-gretl-runtime/work"))

MAX_ROWS = int(os.environ.get("SC_GRETL_MAX_ROWS", "200000"))
MAX_COLUMNS = int(os.environ.get("SC_GRETL_MAX_COLUMNS", "256"))
MAX_DATA_BYTES = int(os.environ.get("SC_GRETL_MAX_DATA_BYTES", "25000000"))
MAX_EXECUTION_SECONDS = int(os.environ.get("SC_GRETL_MAX_EXECUTION_SECONDS", "1800"))

OPERATIONS = [
    "ols",
    "robust_ols",
    "logit",
    "probit",
    "descriptive_summary",
    "correlation_matrix",
]
SAFE_OPERATION = set(OPERATIONS)
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def gretl_ready() -> bool:
    try:
        proc = subprocess.run(
            [GRETL_BIN, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        text = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0 and GRETL_VERSION.lower() in text.lower()
    except Exception:
        return False


def validate_identifier(name: str) -> str:
    if not IDENT.fullmatch(name):
        raise ValueError(f"invalid gretl variable identifier: {name}")
    return name


def validate_columns(columns: Any) -> dict[str, list[float]]:
    if not isinstance(columns, dict) or not columns:
        raise ValueError("columns must be a non-empty object")
    if len(columns) > MAX_COLUMNS:
        raise ValueError("dataset exceeds maximum column count")

    out: dict[str, list[float]] = {}
    lengths: set[int] = set()
    for key, values in columns.items():
        validate_identifier(str(key))
        if not isinstance(values, list):
            raise ValueError("each dataset column must be an array")
        numeric: list[float] = []
        for value in values:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("dataset values must be finite numbers")
            value = float(value)
            if not math.isfinite(value):
                raise ValueError("dataset values must be finite numbers")
            numeric.append(value)
        out[str(key)] = numeric
        lengths.add(len(numeric))

    if len(lengths) != 1:
        raise ValueError("dataset columns must have equal lengths")
    rows = next(iter(lengths))
    if rows < 2:
        raise ValueError("dataset requires at least two observations")
    if rows > MAX_ROWS:
        raise ValueError("dataset exceeds maximum row count")

    encoded = json.dumps(out, separators=(",", ":"), sort_keys=True).encode("utf-8")
    if len(encoded) > MAX_DATA_BYTES:
        raise ValueError("dataset exceeds maximum serialized size")
    return out


def validate_specification(
    operation: str,
    columns: dict[str, list[float]],
    dependent_variable: str | None,
    predictors: list[str],
    variables: list[str],
) -> None:
    names = set(columns)
    if operation in {"ols", "robust_ols", "logit", "probit"}:
        if dependent_variable is None:
            raise ValueError("model operation requires dependent_variable")
        validate_identifier(dependent_variable)
        if dependent_variable not in names:
            raise ValueError("dependent variable is missing from dataset")
        if not predictors:
            raise ValueError("model operation requires predictors")
        if len(predictors) != len(set(predictors)):
            raise ValueError("predictors must be unique")
        for item in predictors:
            validate_identifier(item)
            if item not in names:
                raise ValueError(f"predictor missing from dataset: {item}")
            if item == dependent_variable:
                raise ValueError("dependent variable cannot also be a predictor")
    elif operation in {"descriptive_summary", "correlation_matrix"}:
        if not variables:
            raise ValueError("summary/correlation operation requires variables")
        if len(variables) != len(set(variables)):
            raise ValueError("variables must be unique")
        for item in variables:
            validate_identifier(item)
            if item not in names:
                raise ValueError(f"variable missing from dataset: {item}")
    else:
        raise ValueError("unsupported gretl operation")


def dataset_hash(columns: dict[str, list[float]]) -> str:
    encoded = json.dumps(columns, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, columns: dict[str, list[float]]) -> None:
    names = list(columns)
    rows = len(columns[names[0]])
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(names)
        for i in range(rows):
            writer.writerow([columns[name][i] for name in names])


def build_hansl_script(
    *,
    operation: str,
    csv_path: Path,
    dependent_variable: str | None,
    predictors: list[str],
    include_constant: bool,
    variables: list[str],
) -> str:
    # No caller-supplied hansl is accepted. This function emits a fixed,
    # bounded script using only validated variable identifiers and provider
    # controlled filesystem paths.
    lines = [
        "set echo off",
        "set messages off",
        f'open "{csv_path}" --csv',
    ]

    if operation in {"ols", "robust_ols", "logit", "probit"}:
        regressors = (["const"] if include_constant else []) + predictors
        cmd = "ols" if operation in {"ols", "robust_ols"} else operation
        suffix = " --robust" if operation == "robust_ols" else ""
        lines.append(f"{cmd} {dependent_variable} {' '.join(regressors)}{suffix}")
    elif operation == "descriptive_summary":
        lines.append("summary " + " ".join(variables))
    elif operation == "correlation_matrix":
        lines.append("corr " + " ".join(variables))
    else:
        raise ValueError("unsupported gretl operation")

    lines.append("quit")
    return "\n".join(lines) + "\n"


def parse_regression_coefficients(
    transcript: str,
    *,
    include_constant: bool,
    predictors: list[str],
) -> dict[str, float]:
    wanted = (["const"] if include_constant else []) + predictors
    result: dict[str, float] = {}
    for name in wanted:
        pattern = re.compile(
            rf"(?m)^\s*{re.escape(name)}\s+"
            r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)"
        )
        match = pattern.search(transcript)
        if match:
            result[name] = float(match.group(1))
    return result


def execute_gretl(
    *,
    operation: str,
    columns: dict[str, list[float]],
    dependent_variable: str | None,
    predictors: list[str],
    include_constant: bool,
    variables: list[str],
    timeout_seconds: int,
    run_id: str,
) -> dict[str, Any]:
    if not gretl_ready():
        raise RuntimeError(f"gretl is not ready at {GRETL_BIN}")
    columns = validate_columns(columns)
    validate_specification(operation, columns, dependent_variable, predictors, variables)

    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    safe_run = run_id.replace(":", "_")
    run_dir = WORK_ROOT / safe_run
    artifact_dir = ARTIFACT_ROOT / safe_run
    run_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    csv_path = run_dir / "dataset.csv"
    script_path = run_dir / "analysis.inp"
    transcript_path = artifact_dir / "transcript.txt"
    stderr_path = artifact_dir / "stderr.txt"
    result_path = artifact_dir / "result.json"

    write_csv(csv_path, columns)
    script = build_hansl_script(
        operation=operation,
        csv_path=csv_path,
        dependent_variable=dependent_variable,
        predictors=predictors,
        include_constant=include_constant,
        variables=variables,
    )
    script_path.write_text(script)

    command = [GRETL_BIN, "-b", str(script_path)]
    started = time.monotonic()
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=min(timeout_seconds, MAX_EXECUTION_SECONDS),
        cwd=str(run_dir),
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(run_dir),
            "LC_ALL": "C.UTF-8",
        },
    )
    elapsed_ms = int((time.monotonic() - started) * 1000)

    transcript = proc.stdout or ""
    stderr = proc.stderr or ""
    transcript_path.write_text(transcript)
    stderr_path.write_text(stderr)

    if proc.returncode != 0:
        raise RuntimeError((stderr or transcript or "gretl execution failed").strip())

    coefficients: dict[str, float] = {}
    if operation in {"ols", "robust_ols", "logit", "probit"}:
        coefficients = parse_regression_coefficients(
            transcript,
            include_constant=include_constant,
            predictors=predictors,
        )

    result = {
        "operation": operation,
        "observation_count": len(next(iter(columns.values()))),
        "dataset_sha256": dataset_hash(columns),
        "elapsed_ms": elapsed_ms,
        "coefficients": coefficients,
        "transcript_sha256": file_sha256(transcript_path),
        "stderr_sha256": file_sha256(stderr_path),
    }
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True))

    return {
        **result,
        "artifacts": [
            {
                "artifact_kind": "gretl-transcript",
                "path": str(transcript_path),
                "content_sha256": file_sha256(transcript_path),
            },
            {
                "artifact_kind": "econometric-result-json",
                "path": str(result_path),
                "content_sha256": file_sha256(result_path),
            },
            {
                "artifact_kind": "gretl-stderr",
                "path": str(stderr_path),
                "content_sha256": file_sha256(stderr_path),
            },
        ],
    }


class PrepareRequest(BaseModel):
    operation: str
    columns: dict[str, list[float | int]]
    dependent_variable: str | None = None
    predictors: list[str] = Field(default_factory=list)
    include_constant: bool = True
    variables: list[str] = Field(default_factory=list)
    timeout_seconds: int = Field(default=120, ge=1, le=1800)
    job_ref: str | None = Field(default=None, max_length=500)
    environment_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        if self.operation not in SAFE_OPERATION:
            raise ValueError("unsupported gretl operation")
        columns = validate_columns(self.columns)
        validate_specification(
            self.operation,
            columns,
            self.dependent_variable,
            self.predictors,
            self.variables,
        )
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
        "native_runtime": "gretl",
        "native_runtime_version": GRETL_VERSION,
        "native_package_version": GRETL_PACKAGE_VERSION,
        "runtime_kind": "domain",
        "language": "hansl",
        "status": "registered",
        "execution_state": "active" if gretl_ready() else "degraded",
        "transport": "HTTP",
        "endpoint": f"http://{HOST}:{PORT}",
        "capabilities": OPERATIONS,
        "lifecycle_methods": [
            "health", "version", "capabilities", "prepare", "execute",
            "cancel", "inspect", "collect_results", "collect_artifacts", "diagnose",
        ],
        "boundaries": {
            "arbitrary_hansl_source": False,
            "shell_execution": False,
            "runtime_package_install": False,
            "caller_filesystem_paths": False,
        },
    }


app = FastAPI(title="Sustainable Catalyst gretl/hansl Runtime", version=PROVIDER_VERSION)


@app.get("/health")
def health():
    return {
        "ok": gretl_ready(),
        "runtime_id": RUNTIME_ID,
        "version": PROVIDER_VERSION,
        "gretl_version": GRETL_VERSION,
        "gretl_package_version": GRETL_PACKAGE_VERSION,
        "gretl_bin": GRETL_BIN,
        "capabilities": len(OPERATIONS),
    }


@app.get("/version")
def version():
    return {
        "runtime_id": RUNTIME_ID,
        "version": PROVIDER_VERSION,
        "gretl_version": GRETL_VERSION,
        "gretl_package_version": GRETL_PACKAGE_VERSION,
    }


@app.get("/capabilities")
def capabilities():
    return {"runtime_id": RUNTIME_ID, "version": PROVIDER_VERSION, "operations": OPERATIONS}


@app.get("/v1/core-adapter")
def core_adapter():
    return adapter_descriptor()


@app.post("/v1/core-adapter/prepare")
def prepare(body: PrepareRequest):
    run_id = f"gretl-run:{uuid.uuid4()}"
    RUNS[run_id] = RunRecord(run_id=run_id, request=body)
    columns = validate_columns(body.columns)
    return {
        "ok": True,
        "run_id": run_id,
        "status": "prepared",
        "operation": body.operation,
        "runtime_id": RUNTIME_ID,
        "runtime_version": PROVIDER_VERSION,
        "dataset_sha256": dataset_hash(columns),
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
        record.result = execute_gretl(
            operation=req.operation,
            columns=validate_columns(req.columns),
            dependent_variable=req.dependent_variable,
            predictors=req.predictors,
            include_constant=req.include_constant,
            variables=req.variables,
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
        record.error = "gretl execution timed out"
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
        "runtime_ready": gretl_ready(), "error": record.error,
        "coefficients": (record.result or {}).get("coefficients"),
    }
