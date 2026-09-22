#!/usr/bin/env python3
from pathlib import Path
import tempfile
from tests import test_statistical_reasoning_v3300 as v330
from tests import test_analytical_result_provenance_v3200 as v320
from tests import test_analytical_runtime_provider_v3100 as v310
TESTS=[
 v330.test_migration_provider_and_readiness,
 v330.test_ingest_analytics_r_validation_bundle,
 v330.test_coefficients_intervals_and_human_interpretation,
 v330.test_rejects_invalid_boundaries_and_automatic_interpretation,
 v330.test_core_does_not_turn_p_values_or_comparisons_into_verdicts,
 v320.test_migration_seed_and_provider_promotion,
 v320.test_ingest_idempotent_and_lineage_snapshot,
 v320.test_first_class_estimate_uncertainty_and_explicit_lineage,
 v320.test_rejects_boundary_provider_and_mutating_replay,
 v320.test_declared_reference_guards_and_core_boundaries,
 v310.test_migration_and_seeded_r_provider,
 v310.test_request_result_provenance_roundtrip,
 v310.test_provider_capability_guard_and_runtime_boundary,
]
for fn in TESTS:
    with tempfile.TemporaryDirectory() as td: fn(Path(td))
    print('PASS - '+fn.__name__)
print(f"PASS - Platform Core v3.3.0 release tests: {len(TESTS)}/{len(TESTS)}")
