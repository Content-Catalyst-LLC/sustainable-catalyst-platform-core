from __future__ import annotations

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
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

PROVIDER_VERSION = "1.0.0"
RUNTIME_ID = "sc-runtime-r"
ADAPTER_ID = "adapter:sc-runtime-r"
ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
RUNTIME_OBJECT_CONTRACT = "sc.core.computational-runtime-object.v1"
ENVIRONMENT_CONTRACT = "sc.environment.v1"
HOST = os.environ.get("SC_R_RUNTIME_HOST", "127.0.0.1")
PORT = int(os.environ.get("SC_R_RUNTIME_PORT", "18094"))

SAFE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")
MAX_VECTOR_LENGTH = int(os.environ.get("SC_R_RUNTIME_MAX_VECTOR_LENGTH", "100000"))
MAX_COLUMNS = int(os.environ.get("SC_R_RUNTIME_MAX_COLUMNS", "128"))
MAX_EXECUTION_SECONDS = int(os.environ.get("SC_R_RUNTIME_MAX_EXECUTION_SECONDS", "30"))

CAPABILITIES = [
    "descriptive_summary",
    "quantile_summary",
    "correlation_matrix",
    "linear_regression",
    "t_test",
    "one_way_anova",
]

LEGACY_ALIASES = {
    "descriptive_statistics": "descriptive_summary",
    "summary": "descriptive_summary",
    "describe": "descriptive_summary",
    "quantiles": "quantile_summary",
    "quantile": "quantile_summary",
    "correlation": "correlation_matrix",
    "cor": "correlation_matrix",
    "linear_model": "linear_regression",
    "lm": "linear_regression",
    "ols": "linear_regression",
    "ttest": "t_test",
    "anova": "one_way_anova",
    "aov": "one_way_anova",
    "oneway": "one_way_anova",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def rscript_path() -> str | None:
    return shutil.which("Rscript")


def r_version() -> str | None:
    path = rscript_path()
    if not path:
        return None
    proc = subprocess.run(
        [path, "--version"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    text = (proc.stdout or proc.stderr or "").strip()
    return text or None


def canonical_operation(operation: str) -> str:
    op = str(operation or "").strip()
    op = LEGACY_ALIASES.get(op, op)
    if op not in CAPABILITIES:
        raise ValueError(f"unsupported R operation: {operation}")
    return op


def validate_numeric_vector(values: Any, *, field_name: str = "values") -> list[float]:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list")
    if not values:
        raise ValueError(f"{field_name} cannot be empty")
    if len(values) > MAX_VECTOR_LENGTH:
        raise ValueError(f"{field_name} exceeds maximum vector length")
    out: list[float] = []
    for idx, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field_name}[{idx}] must be numeric")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"{field_name}[{idx}] must be finite")
        out.append(number)
    return out


def validate_named_numeric_columns(data: Any) -> dict[str, list[float]]:
    if not isinstance(data, dict) or not data:
        raise ValueError("data must be a non-empty object of numeric vectors")
    if len(data) > MAX_COLUMNS:
        raise ValueError("data exceeds maximum column count")

    result: dict[str, list[float]] = {}
    lengths: set[int] = set()
    for name, values in data.items():
        if not isinstance(name, str) or not SAFE_NAME.fullmatch(name):
            raise ValueError(f"invalid column name: {name!r}")
        vector = validate_numeric_vector(values, field_name=f"data.{name}")
        result[name] = vector
        lengths.add(len(vector))
    if len(lengths) != 1:
        raise ValueError("all data columns must have equal length")
    return result


def r_num(value: float) -> str:
    return format(float(value), ".17g")


def r_vector(values: list[float]) -> str:
    return "c(" + ",".join(r_num(v) for v in values) + ")"


def tsv_parse(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    rows: list[list[str]] = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        parts = raw.rstrip("\n").split("\t")
        if parts[0] == "__ROW__":
            rows.append(parts[1:])
            continue
        if len(parts) >= 2:
            key = parts[0]
            value = parts[1]
            if value == "NA":
                parsed: Any = None
            else:
                try:
                    parsed = float(value)
                    if parsed.is_integer():
                        parsed = int(parsed)
                except ValueError:
                    parsed = value
            result[key] = parsed
    if rows:
        result["rows"] = rows
    return result


def build_r_script(operation: str, inputs: dict[str, Any]) -> str:
    operation = canonical_operation(operation)

    if operation == "descriptive_summary":
        values = validate_numeric_vector(inputs.get("values"))
        x = r_vector(values)
        return f'''
x <- {x}
cat("n\\t", length(x), "\\n", sep="")
cat("mean\\t", mean(x), "\\n", sep="")
cat("sd\\t", sd(x), "\\n", sep="")
cat("min\\t", min(x), "\\n", sep="")
cat("q1\\t", unname(quantile(x, 0.25, names=FALSE)), "\\n", sep="")
cat("median\\t", median(x), "\\n", sep="")
cat("q3\\t", unname(quantile(x, 0.75, names=FALSE)), "\\n", sep="")
cat("max\\t", max(x), "\\n", sep="")
'''

    if operation == "quantile_summary":
        values = validate_numeric_vector(inputs.get("values"))
        x = r_vector(values)
        return f'''
x <- {x}
q <- quantile(x, probs=c(0,0.25,0.5,0.75,1), names=FALSE)
cat("q0\\t", q[1], "\\n", sep="")
cat("q25\\t", q[2], "\\n", sep="")
cat("q50\\t", q[3], "\\n", sep="")
cat("q75\\t", q[4], "\\n", sep="")
cat("q100\\t", q[5], "\\n", sep="")
'''

    if operation == "correlation_matrix":
        data = validate_named_numeric_columns(inputs.get("data"))
        method = str(inputs.get("method", "pearson"))
        if method not in {"pearson", "spearman", "kendall"}:
            raise ValueError("correlation method must be pearson, spearman, or kendall")
        columns = ",".join(f"{name}={r_vector(values)}" for name, values in data.items())
        return f'''
d <- data.frame({columns}, check.names=FALSE)
m <- cor(d, method="{method}")
cat("columns\\t", paste(colnames(m), collapse=","), "\\n", sep="")
for (i in seq_len(nrow(m))) {{
  cat("__ROW__\\t", rownames(m)[i], "\\t", paste(m[i,], collapse=","), "\\n", sep="")
}}
'''

    if operation == "linear_regression":
        data = validate_named_numeric_columns(inputs.get("data"))
        outcome = str(inputs.get("outcome", ""))
        predictors = inputs.get("predictors")
        if outcome not in data:
            raise ValueError("outcome must name a data column")
        if not isinstance(predictors, list) or not predictors:
            raise ValueError("predictors must be a non-empty list")
        for name in predictors:
            if not isinstance(name, str) or name not in data:
                raise ValueError(f"unknown predictor: {name}")
        if outcome in predictors:
            raise ValueError("outcome cannot also be a predictor")
        columns = ",".join(f"{name}={r_vector(values)}" for name, values in data.items())
        pred = ",".join(f'"{name}"' for name in predictors)
        return f'''
d <- data.frame({columns}, check.names=FALSE)
f <- reformulate(c({pred}), response="{outcome}")
m <- lm(f, data=d)
s <- summary(m)
cat("r_squared\\t", s$r.squared, "\\n", sep="")
cat("adjusted_r_squared\\t", s$adj.r.squared, "\\n", sep="")
cat("sigma\\t", s$sigma, "\\n", sep="")
cat("df_residual\\t", df.residual(m), "\\n", sep="")
cf <- s$coefficients
for (i in seq_len(nrow(cf))) {{
  cat("__ROW__\\t", rownames(cf)[i], "\\t",
      paste(cf[i,], collapse=","), "\\n", sep="")
}}
'''

    if operation == "t_test":
        x = validate_numeric_vector(inputs.get("x"), field_name="x")
        y = validate_numeric_vector(inputs.get("y"), field_name="y")
        paired = bool(inputs.get("paired", False))
        var_equal = bool(inputs.get("var_equal", False))
        if paired and len(x) != len(y):
            raise ValueError("paired t-test requires equal-length x and y")
        alternative = str(inputs.get("alternative", "two.sided"))
        if alternative not in {"two.sided", "less", "greater"}:
            raise ValueError("alternative must be two.sided, less, or greater")
        return f'''
x <- {r_vector(x)}
y <- {r_vector(y)}
t <- t.test(x, y, paired={str(paired).upper()}, var.equal={str(var_equal).upper()}, alternative="{alternative}")
cat("statistic\\t", unname(t$statistic), "\\n", sep="")
cat("parameter\\t", unname(t$parameter), "\\n", sep="")
cat("p_value\\t", t$p.value, "\\n", sep="")
cat("conf_low\\t", t$conf.int[1], "\\n", sep="")
cat("conf_high\\t", t$conf.int[2], "\\n", sep="")
cat("estimate_x\\t", unname(t$estimate[1]), "\\n", sep="")
if (length(t$estimate) > 1) cat("estimate_y\\t", unname(t$estimate[2]), "\\n", sep="")
'''

    if operation == "one_way_anova":
        groups = inputs.get("groups")
        if not isinstance(groups, list) or len(groups) < 2:
            raise ValueError("groups must contain at least two numeric vectors")
        validated = [
            validate_numeric_vector(values, field_name=f"groups[{idx}]")
            for idx, values in enumerate(groups)
        ]
        vectors = ",".join(r_vector(values) for values in validated)
        lengths = ",".join(str(len(values)) for values in validated)
        return f'''
g <- list({vectors})
values <- unlist(g)
group <- factor(rep(seq_along(g), times=c({lengths})))
m <- aov(values ~ group)
s <- summary(m)[[1]]
cat("df_between\\t", s[1,"Df"], "\\n", sep="")
cat("df_within\\t", s[2,"Df"], "\\n", sep="")
cat("f_value\\t", s[1,"F value"], "\\n", sep="")
cat("p_value\\t", s[1,"Pr(>F)"], "\\n", sep="")
'''

    raise ValueError(f"unsupported R operation: {operation}")


def run_r(operation: str, inputs: dict[str, Any]) -> dict[str, Any]:
    path = rscript_path()
    if not path:
        raise RuntimeError("Rscript is not installed or not on PATH")
    script = build_r_script(operation, inputs)
    with tempfile.NamedTemporaryFile("w", suffix=".R", delete=False) as handle:
        handle.write(script)
        script_path = handle.name
    try:
        started = time.monotonic()
        proc = subprocess.run(
            [path, "--vanilla", script_path],
            capture_output=True,
            text=True,
            timeout=MAX_EXECUTION_SECONDS,
        )
        elapsed_ms = int((time.monotonic() - started) * 1000)
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout or "R execution failed").strip())
        return {
            "operation": canonical_operation(operation),
            "elapsed_ms": elapsed_ms,
            "result": tsv_parse(proc.stdout),
        }
    finally:
        try:
            os.unlink(script_path)
        except FileNotFoundError:
            pass


class PrepareRequest(BaseModel):
    operation: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    job_ref: str | None = Field(default=None, max_length=500)
    environment_ref: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        canonical_operation(self.operation)
        build_r_script(self.operation, self.inputs)
        return self


class RunRequest(BaseModel):
    run_id: str = Field(min_length=2, max_length=500)


@dataclass
class RunRecord:
    run_id: str
    operation: str
    inputs: dict[str, Any]
    job_ref: str | None
    environment_ref: str | None
    metadata: dict[str, Any]
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
        "runtime_kind": "language",
        "language": "R",
        "status": "registered",
        "execution_state": "active",
        "transport": "HTTP",
        "endpoint": f"http://{HOST}:{PORT}",
        "capabilities": CAPABILITIES,
        "legacy_provider_aliases": ["catalyst-analytics-r"],
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
            "arbitrary_r_source": False,
            "runtime_package_install": False,
            "shell_execution": False,
            "base_r_operations_only": True,
        },
    }


app = FastAPI(title="Sustainable Catalyst R Runtime", version=PROVIDER_VERSION)


@app.get("/health")
def health():
    return {
        "ok": rscript_path() is not None,
        "runtime_id": RUNTIME_ID,
        "version": PROVIDER_VERSION,
        "rscript": rscript_path(),
        "r_version": r_version(),
        "capabilities": len(CAPABILITIES),
    }


@app.get("/version")
def version():
    return {
        "runtime_id": RUNTIME_ID,
        "version": PROVIDER_VERSION,
        "r_version": r_version(),
    }


@app.get("/capabilities")
def capabilities():
    return {
        "runtime_id": RUNTIME_ID,
        "version": PROVIDER_VERSION,
        "capabilities": CAPABILITIES,
        "legacy_aliases": LEGACY_ALIASES,
    }


@app.get("/v1/core-adapter")
def core_adapter():
    return adapter_descriptor()


@app.post("/v1/core-adapter/prepare")
def prepare(body: PrepareRequest):
    run_id = f"r-run:{uuid.uuid4()}"
    operation = canonical_operation(body.operation)
    record = RunRecord(
        run_id=run_id,
        operation=operation,
        inputs=body.inputs,
        job_ref=body.job_ref,
        environment_ref=body.environment_ref,
        metadata=body.metadata,
    )
    RUNS[run_id] = record
    return {
        "ok": True,
        "run_id": run_id,
        "status": record.status,
        "operation": operation,
        "runtime_id": RUNTIME_ID,
        "runtime_version": PROVIDER_VERSION,
    }


@app.post("/v1/core-adapter/execute")
def execute(body: RunRequest):
    record = RUNS.get(body.run_id)
    if not record:
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
    try:
        record.result = run_r(record.operation, record.inputs)
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
    except Exception as exc:
        record.status = "failed"
        record.error = str(exc)
        record.completed_at = now_iso()
        raise HTTPException(status_code=500, detail=record.error)


@app.post("/v1/core-adapter/cancel")
def cancel(body: RunRequest):
    record = RUNS.get(body.run_id)
    if not record:
        raise HTTPException(status_code=404, detail="run not found")
    if record.status in {"running", "completed", "failed"}:
        raise HTTPException(status_code=409, detail=f"cannot cancel {record.status} run")
    record.status = "cancelled"
    record.completed_at = now_iso()
    return {"ok": True, "run_id": record.run_id, "status": record.status}


@app.get("/v1/core-adapter/inspect")
def inspect(run_id: str):
    record = RUNS.get(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "ok": True,
        "run_id": record.run_id,
        "operation": record.operation,
        "status": record.status,
        "job_ref": record.job_ref,
        "environment_ref": record.environment_ref,
        "created_at": record.created_at,
        "started_at": record.started_at,
        "completed_at": record.completed_at,
        "error": record.error,
    }


@app.get("/v1/core-adapter/results")
def results(run_id: str):
    record = RUNS.get(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "ok": True,
        "run_id": record.run_id,
        "status": record.status,
        "result": record.result,
    }


@app.get("/v1/core-adapter/artifacts")
def artifacts(run_id: str):
    record = RUNS.get(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "ok": True,
        "run_id": record.run_id,
        "status": record.status,
        "artifacts": [],
    }


@app.get("/v1/core-adapter/diagnose")
def diagnose(run_id: str):
    record = RUNS.get(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "ok": True,
        "run_id": record.run_id,
        "status": record.status,
        "runtime_id": RUNTIME_ID,
        "runtime_version": PROVIDER_VERSION,
        "rscript_available": rscript_path() is not None,
        "r_version": r_version(),
        "error": record.error,
    }


@app.get("/v1/legacy/analytical-provider")
def legacy_provider():
    return {
        "ok": True,
        "legacy_provider_id": "catalyst-analytics-r",
        "legacy_provider_version": "2.0.1",
        "canonical_runtime_id": RUNTIME_ID,
        "canonical_runtime_version": PROVIDER_VERSION,
        "compatibility_state": "alias",
        "legacy_aliases": LEGACY_ALIASES,
    }
