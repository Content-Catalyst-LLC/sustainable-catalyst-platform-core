#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks={
 "backend/app/config.py":["version: str = \"3.3.0\"","statistical_reasoning_object_model_enabled"],
 "backend/app/migrations.py":["(\"0105\"","provider_version=\"2.2.0\"","workspace_adapter_release\":\"3.9.1\""],
 "backend/app/models.py":["statistical_reasoning_objects_v330","statistical_coefficients_v330","statistical_intervals_v330","statistical_interpretations_v330"],
 "backend/app/services/statistical_reasoning.py":["sc.core.statistical-reasoning-object-model.v1","sc.analytics-r.statistical-diagnostics-validation.v1","human-authored"],
 "backend/app/main.py":["statistical_reasoning.router"],
 "schemas/statistical-reasoning-object-model-v1.schema.json":["reasoning_ref"],
}
for rel,needles in checks.items():
    p=root/rel
    if not p.exists(): raise SystemExit(f"missing {rel}")
    t=p.read_text()
    for n in needles:
        if n not in t: raise SystemExit(f"{rel} missing {n}")
print("PASS - Platform Core v3.3.0 release contract")
