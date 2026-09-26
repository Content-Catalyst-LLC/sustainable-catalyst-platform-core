from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
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
RUSTC_VERSION = os.environ.get("SC_RUSTC_VERSION", "1.75.0")
RUST_PACKAGE_VERSION = os.environ.get("SC_RUST_PACKAGE_VERSION", "1.75.0+dfsg0ubuntu1-0ubuntu7.4")
CARGO_VERSION = os.environ.get("SC_CARGO_VERSION", "1.75.0")
CARGO_PACKAGE_VERSION = os.environ.get("SC_CARGO_PACKAGE_VERSION", "1.75.0+dfsg0ubuntu1-0ubuntu7.4")
RUNTIME_ID = "sc-runtime-rust"
ADAPTER_ID = "adapter:sc-runtime-rust"
ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
RUNTIME_CONTRACT = "sc.core.rust-runtime.v1"
HOST = os.environ.get("SC_RUST_RUNTIME_HOST", "127.0.0.1")
PORT = int(os.environ.get("SC_RUST_RUNTIME_PORT", "18101"))
RUSTC_BIN = os.environ.get("SC_RUSTC_BIN", "/usr/bin/rustc")
CARGO_BIN = os.environ.get("SC_CARGO_BIN", "/usr/bin/cargo")
ARTIFACT_ROOT = Path(os.environ.get("SC_RUST_ARTIFACT_ROOT", "/var/lib/sc-rust-runtime/artifacts"))
WORK_ROOT = Path(os.environ.get("SC_RUST_WORK_ROOT", "/var/lib/sc-rust-runtime/work"))
MAX_EXECUTION_SECONDS = int(os.environ.get("SC_RUST_MAX_EXECUTION_SECONDS", "1800"))
MAX_VECTOR = 262144
MAX_GRAPH = 512
MAX_TEXT_BYTES = 65536

OPERATIONS = [
    "prefix_sum",
    "moving_average",
    "connected_components",
    "topological_sort",
    "levenshtein_distance",
    "fnv1a_64",
]
SAFE_OPERATION = set(OPERATIONS)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _version_output(bin_path: str) -> str:
    try:
        p = subprocess.run([bin_path, "--version"], capture_output=True, text=True, timeout=10)
        return ((p.stdout or "") + (p.stderr or "")).strip()
    except Exception:
        return ""


def runtime_ready() -> bool:
    rustc = _version_output(RUSTC_BIN)
    cargo = _version_output(CARGO_BIN)
    return f"rustc {RUSTC_VERSION}" in rustc and f"cargo {CARGO_VERSION}" in cargo


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def validate_payload(operation: str, payload: Any) -> dict[str, Any]:
    if operation not in SAFE_OPERATION or not isinstance(payload, dict):
        raise ValueError("unsupported Rust operation or payload")

    if operation == "prefix_sum":
        values = payload.get("integers")
        if not isinstance(values, list) or not values or len(values) > MAX_VECTOR:
            raise ValueError("prefix_sum requires bounded integer vector")
        out = []
        for value in values:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("prefix_sum values must be integers")
            if value < -(2**62) or value > 2**62:
                raise ValueError("prefix_sum value exceeds bounded i64 range")
            out.append(value)
        return {"integers": out}

    if operation == "moving_average":
        values = payload.get("values")
        if not isinstance(values, list) or not values or len(values) > MAX_VECTOR:
            raise ValueError("moving_average requires bounded numeric vector")
        out = [finite(x, "values") for x in values]
        window = payload.get("window")
        if isinstance(window, bool) or not isinstance(window, int) or not (1 <= window <= len(out)):
            raise ValueError("moving_average window invalid")
        return {"values": out, "window": window}

    if operation == "connected_components":
        matrix = payload.get("adjacency_matrix")
        if not isinstance(matrix, list) or not matrix or len(matrix) > MAX_GRAPH:
            raise ValueError("connected_components requires bounded adjacency_matrix")
        n = len(matrix)
        clean = []
        for row in matrix:
            if not isinstance(row, list) or len(row) != n:
                raise ValueError("adjacency_matrix must be square")
            clean_row = []
            for value in row:
                if isinstance(value, bool) or not isinstance(value, int) or value not in {0, 1}:
                    raise ValueError("adjacency_matrix values must be 0 or 1")
                clean_row.append(value)
            clean.append(clean_row)
        for i in range(n):
            if clean[i][i] != 0:
                raise ValueError("adjacency_matrix diagonal must be zero")
            for j in range(n):
                if clean[i][j] != clean[j][i]:
                    raise ValueError("connected_components adjacency_matrix must be symmetric")
        return {"adjacency_matrix": clean}

    if operation == "topological_sort":
        vertex_count = payload.get("vertex_count")
        edges = payload.get("edge_list")
        if isinstance(vertex_count, bool) or not isinstance(vertex_count, int) or not (1 <= vertex_count <= 10000):
            raise ValueError("topological_sort vertex_count invalid")
        if not isinstance(edges, list) or len(edges) > 100000:
            raise ValueError("topological_sort edge_list invalid")
        clean = []
        for edge in edges:
            if not isinstance(edge, list) or len(edge) != 2:
                raise ValueError("each edge must be [from,to]")
            a, b = edge
            if any(isinstance(x, bool) or not isinstance(x, int) for x in (a, b)):
                raise ValueError("edge vertices must be integers")
            if not (0 <= a < vertex_count and 0 <= b < vertex_count):
                raise ValueError("edge vertex out of range")
            clean.append([a, b])
        return {"vertex_count": vertex_count, "edge_list": clean}

    if operation == "levenshtein_distance":
        a, b = payload.get("text_a"), payload.get("text_b")
        if not isinstance(a, str) or not isinstance(b, str):
            raise ValueError("levenshtein_distance requires text_a and text_b")
        if len(a) > 4096 or len(b) > 4096:
            raise ValueError("levenshtein text length exceeds 4096")
        try:
            a.encode("ascii"); b.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError("levenshtein_distance v1 accepts ASCII text only") from exc
        return {"text_a": a, "text_b": b}

    if operation == "fnv1a_64":
        text = payload.get("text")
        if not isinstance(text, str):
            raise ValueError("fnv1a_64 requires text")
        if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
            raise ValueError("fnv1a_64 text exceeds maximum UTF-8 byte length")
        return {"text": text}

    raise ValueError("unsupported Rust operation")


def rust_i64_vec(values: list[int]) -> str:
    return ",".join(str(int(x)) for x in values)


def rust_f64_vec(values: list[float]) -> str:
    return ",".join(f"{float(x):.17g}_f64" for x in values)


def rust_u8_vec(data: bytes) -> str:
    return ",".join(str(x) for x in data)


def generated_source(operation: str, payload: dict[str, Any]) -> str:
    p = validate_payload(operation, payload)
    header = "#![forbid(unsafe_code)]\n"

    if operation == "prefix_sum":
        values = p["integers"]
        return header + f'''fn main() {{\n    let values: [i64; {len(values)}] = [{rust_i64_vec(values)}];\n    let mut acc: i128 = 0;\n    println!("SC_RESULT int_vector {{}}", values.len());\n    for value in values {{ acc += value as i128; println!("{{}}", acc); }}\n}}\n'''

    if operation == "moving_average":
        values, window = p["values"], p["window"]
        return header + f'''fn main() {{\n    let values: [f64; {len(values)}] = [{rust_f64_vec(values)}];\n    let window: usize = {window};\n    println!("SC_RESULT vector {{}}", values.len() - window + 1);\n    for i in 0..=(values.len()-window) {{\n        let mut sum = 0.0_f64;\n        for j in i..(i+window) {{ sum += values[j]; }}\n        println!("{{:.17}}", sum / window as f64);\n    }}\n}}\n'''

    if operation == "connected_components":
        m = p["adjacency_matrix"]; n = len(m); flat = [x for row in m for x in row]
        return header + f'''fn main() {{\n    let n: usize = {n};\n    let adjacency: [u8; {len(flat)}] = [{rust_u8_vec(bytes(flat))}];\n    let mut component = vec![usize::MAX; n];\n    let mut cid = 0usize;\n    for start in 0..n {{\n        if component[start] != usize::MAX {{ continue; }}\n        let mut stack = vec![start]; component[start] = cid;\n        while let Some(u) = stack.pop() {{\n            for v in 0..n {{\n                if adjacency[u*n+v] != 0 && component[v] == usize::MAX {{ component[v] = cid; stack.push(v); }}\n            }}\n        }}\n        cid += 1;\n    }}\n    println!("SC_RESULT int_vector {{}}", n);\n    for x in component {{ println!("{{}}", x); }}\n}}\n'''

    if operation == "topological_sort":
        n = p["vertex_count"]; edges = p["edge_list"]
        edge_pairs = ",".join(f"({a}usize,{b}usize)" for a,b in edges)
        return header + f'''use std::collections::VecDeque;\nfn main() {{\n    let n: usize = {n};\n    let edges: [(usize,usize); {len(edges)}] = [{edge_pairs}];\n    let mut indegree = vec![0usize; n];\n    let mut graph = vec![Vec::<usize>::new(); n];\n    for (a,b) in edges {{ graph[a].push(b); indegree[b] += 1; }}\n    let mut q = VecDeque::new();\n    for i in 0..n {{ if indegree[i] == 0 {{ q.push_back(i); }} }}\n    let mut order = Vec::with_capacity(n);\n    while let Some(u) = q.pop_front() {{\n        order.push(u);\n        for &v in &graph[u] {{ indegree[v] -= 1; if indegree[v] == 0 {{ q.push_back(v); }} }}\n    }}\n    if order.len() != n {{ eprintln!("SC_ERROR cycle_detected"); std::process::exit(3); }}\n    println!("SC_RESULT int_vector {{}}", order.len());\n    for x in order {{ println!("{{}}", x); }}\n}}\n'''

    if operation == "levenshtein_distance":
        a, b = p["text_a"].encode("ascii"), p["text_b"].encode("ascii")
        return header + f'''fn main() {{\n    let a: [u8; {len(a)}] = [{rust_u8_vec(a)}];\n    let b: [u8; {len(b)}] = [{rust_u8_vec(b)}];\n    let mut prev: Vec<usize> = (0..=b.len()).collect();\n    let mut curr = vec![0usize; b.len()+1];\n    for i in 1..=a.len() {{\n        curr[0] = i;\n        for j in 1..=b.len() {{\n            let cost = if a[i-1] == b[j-1] {{0}} else {{1}};\n            curr[j] = std::cmp::min(std::cmp::min(curr[j-1]+1, prev[j]+1), prev[j-1]+cost);\n        }}\n        std::mem::swap(&mut prev, &mut curr);\n    }}\n    println!("SC_RESULT int_scalar {{}}", prev[b.len()]);\n}}\n'''

    if operation == "fnv1a_64":
        data = p["text"].encode("utf-8")
        return header + f'''fn main() {{\n    let data: [u8; {len(data)}] = [{rust_u8_vec(data)}];\n    let mut hash: u64 = 0xcbf29ce484222325;\n    for byte in data {{ hash ^= byte as u64; hash = hash.wrapping_mul(0x100000001b3); }}\n    println!("SC_RESULT hex64 {{:016x}}", hash);\n}}\n'''

    raise ValueError("unsupported Rust operation")


def parse_output(stdout: str) -> dict[str, Any]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for idx, line in enumerate(lines):
        if not line.startswith("SC_RESULT "):
            continue
        parts = line.split()
        kind = parts[1]
        if kind == "int_scalar":
            return {"kind": kind, "value": int(parts[2])}
        if kind == "hex64":
            value = parts[2].lower()
            if len(value) != 16 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("invalid hex64 result")
            return {"kind": kind, "value": value}
        if kind == "int_vector":
            n = int(parts[2]); values = [int(x) for x in lines[idx+1:idx+1+n]]
            if len(values) != n: raise ValueError("incomplete int_vector result")
            return {"kind": kind, "values": values}
        if kind == "vector":
            n = int(parts[2]); values = [float(x) for x in lines[idx+1:idx+1+n]]
            if len(values) != n: raise ValueError("incomplete vector result")
            return {"kind": kind, "values": values}
    raise ValueError("no SC_RESULT marker")


def execute_native(operation: str, payload: dict[str, Any], timeout_seconds: int, optimization_level: int, run_id: str) -> dict[str, Any]:
    if not runtime_ready():
        raise RuntimeError("Rust runtime is not ready")
    source = generated_source(operation, payload)
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    safe = run_id.replace(":", "_")
    work = WORK_ROOT / safe
    artifacts = ARTIFACT_ROOT / safe
    work.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    source_path = artifacts / "job.rs"
    binary_path = work / "job.bin"
    compile_log = artifacts / "compile.log"
    run_log = artifacts / "run.log"
    result_path = artifacts / "result.json"
    source_path.write_text(source)

    compile_cmd = [
        RUSTC_BIN,
        "--edition=2021",
        f"-Copt-level={optimization_level}",
        "-Coverflow-checks=on",
        str(source_path),
        "-o", str(binary_path),
    ]
    cp = subprocess.run(
        compile_cmd, capture_output=True, text=True,
        timeout=min(timeout_seconds, MAX_EXECUTION_SECONDS), cwd=str(work),
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(work), "LC_ALL": "C.UTF-8"},
    )
    compile_log.write_text((cp.stdout or "") + (cp.stderr or ""))
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr or cp.stdout or "Rust compilation failed")

    start = time.monotonic()
    run = subprocess.run(
        [str(binary_path)], capture_output=True, text=True,
        timeout=min(timeout_seconds, MAX_EXECUTION_SECONDS), cwd=str(work),
        env={"PATH": "/usr/bin:/bin", "HOME": str(work), "LC_ALL": "C.UTF-8"},
    )
    elapsed_ms = int((time.monotonic() - start) * 1000)
    run_log.write_text((run.stdout or "") + (run.stderr or ""))
    binary_path.unlink(missing_ok=True)
    if run.returncode != 0:
        raise RuntimeError(run.stderr or run.stdout or "Rust execution failed")

    native_result = parse_output(run.stdout)
    result = {
        "operation": operation,
        "edition": "2021",
        "elapsed_ms": elapsed_ms,
        "native_result": native_result,
        "source_sha256": file_sha256(source_path),
        "compile_log_sha256": file_sha256(compile_log),
        "run_log_sha256": file_sha256(run_log),
    }
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True))
    return {
        **result,
        "artifacts": [
            {"artifact_kind": "rust-generated-source", "path": str(source_path), "content_sha256": file_sha256(source_path)},
            {"artifact_kind": "rust-result-json", "path": str(result_path), "content_sha256": file_sha256(result_path)},
            {"artifact_kind": "rust-compile-log", "path": str(compile_log), "content_sha256": file_sha256(compile_log)},
            {"artifact_kind": "rust-run-log", "path": str(run_log), "content_sha256": file_sha256(run_log)},
        ],
    }


class PrepareRequest(BaseModel):
    operation: str
    payload: dict[str, Any]
    timeout_seconds: int = Field(default=120, ge=1, le=1800)
    optimization_level: int = Field(default=2, ge=0, le=2)
    job_ref: str | None = Field(default=None, max_length=500)
    environment_ref: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_request(self):
        validate_payload(self.operation, self.payload)
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
        "native_runtime": "rustc",
        "native_runtime_version": RUSTC_VERSION,
        "native_package_version": RUST_PACKAGE_VERSION,
        "cargo_version": CARGO_VERSION,
        "cargo_package_version": CARGO_PACKAGE_VERSION,
        "runtime_kind": "language",
        "language": "rust",
        "edition": "2021",
        "status": "registered",
        "execution_state": "active" if runtime_ready() else "degraded",
        "transport": "HTTP",
        "endpoint": f"http://{HOST}:{PORT}",
        "capabilities": OPERATIONS,
        "lifecycle_methods": [
            "health", "version", "capabilities", "prepare", "execute",
            "cancel", "inspect", "collect_results", "collect_artifacts", "diagnose",
        ],
        "boundaries": {
            "arbitrary_rust_source": False,
            "unsafe_rust_code": False,
            "shell_execution": False,
            "runtime_package_install": False,
            "caller_filesystem_paths": False,
        },
    }


app = FastAPI(title="Sustainable Catalyst Rust Runtime", version=PROVIDER_VERSION)


@app.get("/health")
def health():
    return {
        "ok": runtime_ready(),
        "runtime_id": RUNTIME_ID,
        "version": PROVIDER_VERSION,
        "rustc_version": RUSTC_VERSION,
        "rustc_package_version": RUST_PACKAGE_VERSION,
        "cargo_version": CARGO_VERSION,
        "cargo_package_version": CARGO_PACKAGE_VERSION,
        "rustc_bin": RUSTC_BIN,
        "capabilities": len(OPERATIONS),
    }


@app.get("/version")
def version():
    return {
        "runtime_id": RUNTIME_ID,
        "version": PROVIDER_VERSION,
        "rustc_version": RUSTC_VERSION,
        "cargo_version": CARGO_VERSION,
    }


@app.get("/capabilities")
def capabilities():
    return {"runtime_id": RUNTIME_ID, "version": PROVIDER_VERSION, "operations": OPERATIONS}


@app.get("/v1/core-adapter")
def core_adapter():
    return adapter_descriptor()


@app.post("/v1/core-adapter/prepare")
def prepare(body: PrepareRequest):
    run_id = f"rust-run:{uuid.uuid4()}"
    RUNS[run_id] = RunRecord(run_id=run_id, request=body)
    return {"ok": True, "run_id": run_id, "status": "prepared", "operation": body.operation, "runtime_id": RUNTIME_ID, "runtime_version": PROVIDER_VERSION}


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
        record.result = execute_native(req.operation, req.payload, req.timeout_seconds, req.optimization_level, record.run_id)
        record.status = "completed"
        record.completed_at = now_iso()
        return {"ok": True, "run_id": record.run_id, "status": record.status, "runtime_id": RUNTIME_ID, "runtime_version": PROVIDER_VERSION, "result": record.result}
    except subprocess.TimeoutExpired:
        record.status = "failed"; record.error = "Rust compile or execution timed out"; record.completed_at = now_iso()
        raise HTTPException(status_code=504, detail=record.error)
    except Exception as exc:
        record.status = "failed"; record.error = str(exc); record.completed_at = now_iso()
        raise HTTPException(status_code=500, detail=record.error)


@app.post("/v1/core-adapter/cancel")
def cancel(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None: raise HTTPException(status_code=404, detail="run not found")
    if record.status == "running": raise HTTPException(status_code=409, detail="v1 synchronous provider cannot interrupt an already-running process")
    if record.status in {"completed", "failed"}: return {"ok": True, "run_id": record.run_id, "status": record.status}
    record.status = "cancelled"; record.completed_at = now_iso()
    return {"ok": True, "run_id": record.run_id, "status": record.status}


@app.post("/v1/core-adapter/inspect")
def inspect(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None: raise HTTPException(status_code=404, detail="run not found")
    return {"ok": True, "run_id": record.run_id, "status": record.status, "operation": record.request.operation, "job_ref": record.request.job_ref, "environment_ref": record.request.environment_ref, "created_at": record.created_at, "started_at": record.started_at, "completed_at": record.completed_at, "error": record.error}


@app.post("/v1/core-adapter/collect-results")
def collect_results(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None: raise HTTPException(status_code=404, detail="run not found")
    return {"ok": True, "run_id": record.run_id, "status": record.status, "result": record.result}


@app.post("/v1/core-adapter/collect-artifacts")
def collect_artifacts(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None: raise HTTPException(status_code=404, detail="run not found")
    artifacts = list((record.result or {}).get("artifacts") or [])
    return {"ok": True, "run_id": record.run_id, "status": record.status, "artifacts": artifacts}


@app.post("/v1/core-adapter/diagnose")
def diagnose(body: RunRequest):
    record = RUNS.get(body.run_id)
    if record is None: raise HTTPException(status_code=404, detail="run not found")
    return {"ok": True, "run_id": record.run_id, "status": record.status, "runtime_ready": runtime_ready(), "error": record.error, "native_result": (record.result or {}).get("native_result")}
