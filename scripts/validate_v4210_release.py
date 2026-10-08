#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def check(label: str, condition: bool) -> None:
    if not condition:
        raise SystemExit(f"{label}=FAIL")
    print(f"{label}=PASS")


config = (ROOT / "backend/app/config.py").read_text()
main = (ROOT / "backend/app/main.py").read_text()
profiles = (ROOT / "backend/app/services/connector_execution_profiles.py").read_text()
router = (ROOT / "backend/app/routers/connector_execution_profiles.py").read_text()
scheduler = (ROOT / "backend/scripts/run_connector_scheduler.py").read_text()
readme = (ROOT / "README.md").read_text()
changelog = (ROOT / "CHANGELOG.md").read_text()
env_example_path = ROOT / "backend/.env.example"
env_example = env_example_path.read_text() if env_example_path.exists() else ""

m = re.search(r'version: str = "(\d+)\.(\d+)\.(\d+)"', config)
version = tuple(map(int, m.groups())) if m else (0, 0, 0)

check("PLATFORM_CORE_V4210_BACKEND_VERSION", version >= (4, 21, 0))
check(
    "PLATFORM_CORE_V4210_PROFILE_CONTRACT",
    'CONTRACT_VERSION = "sc.core.parameterized-connector-execution-profile.v1"' in profiles,
)
check("PLATFORM_CORE_V4210_PROFILE_COUNT", profiles.count("        _p(") == 22)
check(
    "PLATFORM_CORE_V4210_SCHEDULER_SAFE_DEFAULT",
    "parameterized_profile_scheduler_enabled: bool = False" in config,
)
check(
    "PLATFORM_CORE_V4210_ALLOWLIST",
    "parameterized_profile_scheduler_ids" in config
    and "SC_CORE_PARAMETERIZED_PROFILE_IDS" in config,
)
check(
    "PLATFORM_CORE_V4210_MAX_PER_PASS",
    "parameterized_profile_max_per_pass" in config,
)
check(
    "PLATFORM_CORE_V4210_ROUTE_MOUNT",
    "connector_execution_profiles.router" in main
    and "connector_execution_profiles.public_router" in main,
)
check(
    "PLATFORM_CORE_V4210_API_SURFACE",
    '/v1/connector-profiles' in router
    and '/public/v1/connector-profiles' in router,
)
check(
    "PLATFORM_CORE_V4210_SCHEDULER_INTEGRATION",
    "schedule_parameterized_profiles" in scheduler
    and "profile_requested_by" in scheduler,
)
check(
    "PLATFORM_CORE_V4210_ACTIVITY_ISOLATION",
    "ConnectorWorkItem.requested_by == requested_by" in scheduler,
)
check(
    "PLATFORM_CORE_V4210_DYNAMIC_PARAMETERS",
    all(
        token in profiles
        for token in (
            "{{today}}",
            "{{current_year}}",
            "year_minus_",
            "date_minus_",
            "{{ecmwf_date}}",
            "{{ecmwf_run}}",
        )
    ),
)
check(
    "PLATFORM_CORE_V4210_SECRET_BOUNDARY",
    "Credential-like execution parameter is forbidden" in profiles,
)
check(
    "PLATFORM_CORE_V4210_TEMPLATE_BOUNDARY",
    "Template profiles cannot be scheduler eligible." in profiles,
)
check(
    "PLATFORM_CORE_V4210_EPISTEMIC_BOUNDARY",
    "execution_does_not_establish_truth" in profiles
    and "automatic_evidence_promotion" in profiles,
)
check(
    "PLATFORM_CORE_V4210_README",
    "v4.21.0 — Parameterized Connector Execution Profiles" in readme,
)
check(
    "PLATFORM_CORE_V4210_CHANGELOG",
    "v4.21.0 — Parameterized Connector Execution Profiles" in changelog,
)
check(
    "PLATFORM_CORE_V4210_ENV_EXAMPLE",
    "SC_CORE_PARAMETERIZED_PROFILE_SCHEDULER_ENABLED=false" in env_example,
)
check(
    "PLATFORM_CORE_V4210_TEST_COVERAGE",
    (ROOT / "backend/tests/test_connector_execution_profiles_v4210.py").exists(),
)
check(
    "PLATFORM_CORE_V4210_DOC",
    (ROOT / "docs/PLATFORM_CORE_V4210_PARAMETERIZED_CONNECTOR_EXECUTION_PROFILES.md").exists(),
)
check(
    "PLATFORM_CORE_V4210_NO_DB_MIGRATION",
    'database_migration: Literal["none"]' in profiles,
)

print("PLATFORM_CORE_V4210_VALIDATION=PASS")
