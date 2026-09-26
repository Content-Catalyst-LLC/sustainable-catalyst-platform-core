from __future__ import annotations

import hashlib
import json
import math
import os
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
GHC_VERSION = os.environ.get("SC_HASKELL_GHC_VERSION", "9.4.7")
GHC_PACKAGE_VERSION = os.environ.get("SC_HASKELL_GHC_PACKAGE_VERSION", "9.4.7-3")
RUNTIME_ID = "sc-runtime-haskell"
ADAPTER_ID = "adapter:sc-runtime-haskell"
ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
RUNTIME_CONTRACT = "sc.core.haskell-runtime.v1"
HOST = os.environ.get("SC_HASKELL_RUNTIME_HOST", "127.0.0.1")
PORT = int(os.environ.get("SC_HASKELL_RUNTIME_PORT", "18098"))
GHC_BIN = os.environ.get("SC_HASKELL_GHC_BIN", "/usr/bin/ghc")
RUNGHC_BIN = os.environ.get("SC_HASKELL_RUNGHC_BIN", "/usr/bin/runghc")
ARTIFACT_ROOT = Path(os.environ.get("SC_HASKELL_ARTIFACT_ROOT", "/var/lib/sc-haskell-runtime/artifacts"))
WORK_ROOT = Path(os.environ.get("SC_HASKELL_WORK_ROOT", "/var/lib/sc-haskell-runtime/work"))
MAX_EXECUTION_SECONDS = int(os.environ.get("SC_HASKELL_MAX_EXECUTION_SECONDS", "600"))
MAX_EDGES = int(os.environ.get("SC_HASKELL_MAX_EDGES", "10000"))
MAX_N = int(os.environ.get("SC_HASKELL_MAX_N", "10000"))

OPERATIONS = [
    "gcd",
    "lcm",
    "rational_reduce",
    "factorial",
    "fibonacci",
    "binomial_coefficient",
    "integer_power",
    "graph_reachable",
]
SAFE_OPERATION = set(OPERATIONS)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ghc_ready() -> bool:
    try:
        proc = subprocess.run(
            [GHC_BIN, "--numeric-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.returncode == 0 and proc.stdout.strip() == GHC_VERSION
    except Exception:
        return False


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_payload(operation: str, payload: Any) -> dict[str, Any]:
    if operation not in SAFE_OPERATION:
        raise ValueError("unsupported Haskell operation")
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    def integer(name: str, *, required: bool = True) -> int | None:
        if name not in payload:
            if required:
                raise ValueError(f"missing integer field: {name}")
            return None
        value = payload[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer")
        return value

    out: dict[str, Any] = {}
    if operation in {"gcd", "lcm"}:
        out["a"] = integer("a")
        out["b"] = integer("b")
    elif operation == "rational_reduce":
        out["numerator"] = integer("numerator")
        out["denominator"] = integer("denominator")
        if out["denominator"] == 0:
            raise ValueError("denominator cannot be zero")
    elif operation in {"factorial", "fibonacci"}:
        out["n"] = integer("n")
        if out["n"] < 0 or out["n"] > MAX_N:
            raise ValueError(f"n must be between 0 and {MAX_N}")
    elif operation == "binomial_coefficient":
        out["n"] = integer("n")
        out["k"] = integer("k")
        if out["n"] < 0 or out["n"] > MAX_N or out["k"] < 0 or out["k"] > out["n"]:
            raise ValueError(f"binomial coefficient requires 0 <= k <= n <= {MAX_N}")
    elif operation == "integer_power":
        out["base"] = integer("base")
        out["exponent"] = integer("exponent")
        if out["exponent"] < 0 or out["exponent"] > MAX_N:
            raise ValueError(f"exponent must be between 0 and {MAX_N}")
    elif operation == "graph_reachable":
        source = integer("source")
        target = integer("target")
        edges = payload.get("edges")
        if not isinstance(edges, list):
            raise ValueError("edges must be an array")
        if len(edges) > MAX_EDGES:
            raise ValueError(f"graph exceeds maximum edge count {MAX_EDGES}")
        clean_edges: list[list[int]] = []
        for edge in edges:
            if not isinstance(edge, list) or len(edge) != 2:
                raise ValueError("each graph edge must be [from,to]")
            a, b = edge
            if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, int) or not isinstance(b, int):
                raise ValueError("graph nodes must be integers")
            clean_edges.append([a, b])
        out = {"source": source, "target": target, "edges": clean_edges}
    return out


def haskell_source(operation: str, payload: dict[str, Any]) -> str:
    payload = validate_payload(operation, payload)
    header = [
        "module Main where",
        "import Data.Ratio",
        "import Data.List (nub)",
        "",
        "jsonString :: String -> String",
        'jsonString s = "\\\"" ++ s ++ "\\\""',
        "",
        "factorial :: Integer -> Integer",
        "factorial n = product [1..n]",
        "",
        "fib :: Integer -> Integer",
        "fib n = go n 0 1 where",
        "  go 0 a _ = a",
        "  go m a b = go (m-1) b (a+b)",
        "",
        "choose :: Integer -> Integer -> Integer",
        "choose n k",
        "  | k < 0 || k > n = 0",
        "  | otherwise = product [n-k'+1..n] `div` product [1..k']",
        "  where k' = min k (n-k)",
        "",
        "reachable :: [(Integer,Integer)] -> Integer -> Integer -> Bool",
        "reachable edges source target = walk [] [source] where",
        "  walk _ [] = False",
        "  walk seen (x:xs)",
        "    | x == target = True",
        "    | x `elem` seen = walk seen xs",
        "    | otherwise = let next = [b | (a,b) <- edges, a == x]",
        "                  in walk (x:seen) (xs ++ next)",
        "",
    ]

    if operation == "gcd":
        expr = f'gcd ({payload["a"]} :: Integer) ({payload["b"]} :: Integer)'
        main = f'main = putStrLn ("{{\\\"operation\\\":\\\"gcd\\\",\\\"value\\\":" ++ jsonString (show ({expr})) ++ "}}")'
    elif operation == "lcm":
        expr = f'lcm ({payload["a"]} :: Integer) ({payload["b"]} :: Integer)'
        main = f'main = putStrLn ("{{\\\"operation\\\":\\\"lcm\\\",\\\"value\\\":" ++ jsonString (show ({expr})) ++ "}}")'
    elif operation == "rational_reduce":
        n, d = payload["numerator"], payload["denominator"]
        main = "\n".join([
            "main = do",
            f"  let r = ({n} :: Integer) % ({d} :: Integer)",
            '  putStrLn ("{\\\"operation\\\":\\\"rational_reduce\\\",\\\"numerator\\\":" ++ jsonString (show (numerator r)) ++ ",\\\"denominator\\\":" ++ jsonString (show (denominator r)) ++ "}")',
        ])
    elif operation == "factorial":
        n = payload["n"]
        main = f'main = putStrLn ("{{\\\"operation\\\":\\\"factorial\\\",\\\"value\\\":" ++ jsonString (show (factorial ({n} :: Integer))) ++ "}}")'
    elif operation == "fibonacci":
        n = payload["n"]
        main = f'main = putStrLn ("{{\\\"operation\\\":\\\"fibonacci\\\",\\\"value\\\":" ++ jsonString (show (fib ({n} :: Integer))) ++ "}}")'
    elif operation == "binomial_coefficient":
        n, k = payload["n"], payload["k"]
        main = f'main = putStrLn ("{{\\\"operation\\\":\\\"binomial_coefficient\\\",\\\"value\\\":" ++ jsonString (show (choose ({n} :: Integer) ({k} :: Integer))) ++ "}}")'
    elif operation == "integer_power":
        b, e = payload["base"], payload["exponent"]
        main = f'main = putStrLn ("{{\\\"operation\\\":\\\"integer_power\\\",\\\"value\\\":" ++ jsonString (show (({b} :: Integer) ^ ({e} :: Integer))) ++ "}}")'
    elif operation == "graph_reachable":
        edges = ",".join(f"({a},{b})" for a,b in payload["edges"])
        source, target = payload["source"], payload["target"]
        main = "\n".join([
            f"edges :: [(Integer,Integer)]",
            f"edges = [{edges}]",
            f"main = putStrLn (\"{{\\\"operation\\\":\\\"graph_reachable\\\",\\\"reachable\\\":\" ++ (if reachable edges ({source}::Integer) ({target}::Integer) then \"true\" else \"false\") ++ \"}}\")",
        ])
    else:
        raise ValueError("unsupported Haskell operation")
    return "\n".join(header + [main, ""])


def execute_haskell(*, operation: str, payload: dict[str, Any], timeout_seconds: int, run_id: str) -> dict[str, Any]:
    if not ghc_ready():
        raise RuntimeError(f"GHC is not ready at {GHC_BIN}")
    validated = validate_payload(operation, payload)
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    safe_run = run_id.replace(":", "_")
    run_dir = WORK_ROOT / safe_run
    artifact_dir = ARTIFACT_ROOT / safe_run
    run_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    source_path = artifact_dir / "Main.hs"
    result_path = artifact_dir / "result.json"
    log_path = artifact_dir / "run.log"
    source_path.write_text(haskell_source(operation, validated))

    command = [RUNGHC_BIN, str(source_path)]
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
    log_path.write_text(
        "COMMAND=" + " ".join(command) + "\n"
        + "RETURN_CODE=" + str(proc.returncode) + "\n"
        + "STDOUT:\n" + (proc.stdout or "") + "\nSTDERR:\n" + (proc.stderr or "")
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "Haskell execution failed").strip())
    lines = [x.strip() for x in (proc.stdout or "").splitlines() if x.strip()]
    if not lines:
        raise RuntimeError("Haskell execution returned no result")
    try:
        native_result = json.loads(lines[-1])
    except Exception as exc:
        raise RuntimeError(f"Haskell result was not valid JSON: {lines[-1]}") from exc

    result = {
        "operation": operation,
        "elapsed_ms": elapsed_ms,
        "native_result": native_result,
        "source_sha256": file_sha256(source_path),
        "log_sha256": file_sha256(log_path),
    }
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True))
    return {
        **result,
        "artifacts": [
            {"artifact_kind": "haskell-generated-source", "path": str(source_path), "content_sha256": file_sha256(source_path)},
            {"artifact_kind": "haskell-result-json", "path": str(result_path), "content_sha256": file_sha256(result_path)},
            {"artifact_kind": "haskell-run-log", "path": str(log_path), "content_sha256": file_sha256(log_path)},
        ],
    }


class PrepareRequest(BaseModel):
    operation: str
    payload: dict[str, Any]
    timeout_seconds: int = Field(default=60, ge=1, le=600)
    job_ref: str | None = Field(default=None, max_length=500)
    environment_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

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
        "native_runtime": "GHC",
        "native_runtime_version": GHC_VERSION,
        "native_package_version": GHC_PACKAGE_VERSION,
        "runtime_kind": "language",
        "language": "haskell",
        "status": "registered",
        "execution_state": "active" if ghc_ready() else "degraded",
        "transport": "HTTP",
        "endpoint": f"http://{HOST}:{PORT}",
        "capabilities": OPERATIONS,
        "lifecycle_methods": [
            "health", "version", "capabilities", "prepare", "execute",
            "cancel", "inspect", "collect_results", "collect_artifacts", "diagnose",
        ],
        "boundaries": {
            "arbitrary_haskell_source": False,
            "shell_execution": False,
            "runtime_package_install": False,
            "caller_filesystem_paths": False,
        },
    }


app = FastAPI(title="Sustainable Catalyst Haskell Runtime", version=PROVIDER_VERSION)


@app.get("/health")
def health():
    return {
        "ok": ghc_ready(),
        "runtime_id": RUNTIME_ID,
        "version": PROVIDER_VERSION,
        "ghc_version": GHC_VERSION,
        "ghc_package_version": GHC_PACKAGE_VERSION,
        "ghc_bin": GHC_BIN,
        "runghc_bin": RUNGHC_BIN,
        "capabilities": len(OPERATIONS),
    }


@app.get("/version")
def version():
    return {
        "runtime_id": RUNTIME_ID,
        "version": PROVIDER_VERSION,
        "ghc_version": GHC_VERSION,
        "ghc_package_version": GHC_PACKAGE_VERSION,
    }


@app.get("/capabilities")
def capabilities():
    return {"runtime_id": RUNTIME_ID, "version": PROVIDER_VERSION, "operations": OPERATIONS}


@app.get("/v1/core-adapter")
def core_adapter():
    return adapter_descriptor()


@app.post("/v1/core-adapter/prepare")
def prepare(body: PrepareRequest):
    run_id = f"haskell-run:{uuid.uuid4()}"
    RUNS[run_id] = RunRecord(run_id=run_id, request=body)
    return {
        "ok": True,
        "run_id": run_id,
        "status": "prepared",
        "operation": body.operation,
        "runtime_id": RUNTIME_ID,
        "runtime_version": PROVIDER_VERSION,
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
        record.result = execute_haskell(
            operation=req.operation,
            payload=req.payload,
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
        record.error = "Haskell execution timed out"
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
        "runtime_ready": ghc_ready(), "error": record.error,
        "native_result": (record.result or {}).get("native_result"),
    }
