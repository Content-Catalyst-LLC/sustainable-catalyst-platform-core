#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "=== PYTHON ADAPTER TESTS (DEPENDENCY-FREE) ==="
"$PYTHON_BIN" - "$ROOT" <<'PY'
from pathlib import Path
import importlib.util
import sys
import traceback

root = Path(sys.argv[1])
test_path = root / "core_adapter/tests/test_adapter.py"

spec = importlib.util.spec_from_file_location("catalyst_julia_v030_tests", test_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

tests = sorted(
    (name, value)
    for name, value in vars(module).items()
    if name.startswith("test_") and callable(value)
)

failed = []
for name, fn in tests:
    try:
        fn()
        print(f"PASS - {name}")
    except Exception as exc:
        failed.append((name, exc))
        print(f"FAIL - {name}: {exc}")
        traceback.print_exc()

if failed:
    raise SystemExit(1)

if len(tests) != 5:
    raise SystemExit(f"Expected 5 adapter tests, discovered {len(tests)}")

print(f"PASS - Catalyst Julia Runtime v0.3.0 Python adapter tests: {len(tests)}/5")
PY

echo "=== JSON / CONTRACT VALIDATION ==="
"$PYTHON_BIN" - "$ROOT" <<'PY'
from pathlib import Path
import json
import sys

root = Path(sys.argv[1])

for path in root.rglob("*.json"):
    json.loads(path.read_text(encoding="utf-8"))

descriptor = json.loads((root / "core_adapter/runtime_descriptor.json").read_text())
assert descriptor["service_version"] == "0.3.0"
assert descriptor["core_adapter_contract_version"] == "sc.core.runtime-adapter.v1"
assert descriptor["core_object_contract_version"] == "sc.core.computational-runtime-object.v1"
assert descriptor["adapter_status"] == "registered"
assert len(descriptor["required_adapter_methods"]) == 10

example = json.loads((root / "examples/core-runtime-adapter-v030.json").read_text())
assert example["adapter_contract"] == "sc.core.runtime-adapter.v1"
assert example["runtime"]["provider_version"] == "0.3.0"
assert example["status"] == "registered"

print("PASS - JSON + Core adapter contract validation")
PY

echo "=== SHELL SYNTAX / RELEASE MARKERS ==="
for script in "$ROOT"/*.sh "$ROOT"/deploy/*.sh; do
  bash -n "$script"
done

grep -q 'version = "0.3.0"' "$ROOT/runtime/Project.toml"
grep -q 'const VERSION = "0.3.0"' "$ROOT/runtime/src/CatalystJuliaRuntime.jl"
grep -q 'sc.core.runtime-adapter.v1' "$ROOT/runtime/src/CatalystJuliaRuntime.jl"
grep -q 'sc.core.computational-runtime-object.v1' "$ROOT/runtime/src/CatalystJuliaRuntime.jl"

echo "PASS - shell syntax"
echo "PASS - static release markers"
echo "PASS - Catalyst Julia Runtime v0.3.0 static release validation"
echo "NOTE - Native Julia tests run on the Julia 1.13 deployment target."
