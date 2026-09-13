#!/usr/bin/env python3
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
CFG = (ROOT / "backend/app/config.py").read_text()
MIG = (ROOT / "backend/app/migrations.py").read_text()
MOD = (ROOT / "backend/app/models.py").read_text()
MAIN = (ROOT / "backend/app/main.py").read_text()
META = (ROOT / "backend/app/routers/meta.py").read_text()
ROUTER = (ROOT / "backend/app/routers/research_visual_explanations.py").read_text()
SERVICE = (ROOT / "backend/app/services/research_visual_explanations.py").read_text()
WP = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text()
SDK_PY = (ROOT / "backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
SDK_JS = (ROOT / "backend/public_sdk/javascript/index.mjs").read_text()
SDK_JS_PACKAGE = (ROOT / "backend/public_sdk/javascript/package.json").read_text()
SDK_PY_PROJECT = (ROOT / "backend/public_sdk/python/pyproject.toml").read_text()
PORTAL = (ROOT / "backend/app/routers/developer_portal.py").read_text()
REGISTRY = (ROOT / "backend/app/service_registry.py").read_text()

assert 'version: str = "2.39.0"' in CFG
assert "research_librarian_visual_explanation_enabled" in CFG
assert "research_librarian_visual_explanation_public_metadata_enabled" in CFG
assert "SustainableCatalystPlatformCore/2.39.0" in CFG

tree = ast.parse(MIG); migrations = None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MIGRATIONS" for t in node.targets):
        migrations = ast.literal_eval(node.value); break
assert migrations is not None
versions = [version for version, _ in migrations]
assert versions[-1] == "0043" and len(versions) == len(set(versions))
descriptions = dict(migrations)
for version in ("0040", "0041", "0042", "0043"):
    assert len(descriptions[version]) <= 300, (version, len(descriptions[version]))

for name in [
    "ResearchVisualExplanationRecord", "ResearchExplanationNodeRecord", "ResearchExplanationRelationRecord",
    "ResearchExplanationCitationRecord", "ResearchExplanationViewRecord", "ResearchExplanationSnapshotRecord",
]:
    assert f"class {name}" in MOD

assert 'prefix="/v1/research-visual-explanations"' in ROUTER
assert 'prefix="/api/v1/research-visual-explanations"' in ROUTER
assert "research_visual_explanations.router" in MAIN and "research_visual_explanations.public_router" in MAIN
assert '"research_librarian_visual_explanation"' in META
for boundary in [
    "source_retrieval_by_core", "natural_language_generation_by_core", "citation_selection_by_core",
    "source_ranking_by_core", "layout_execution_by_core", "renderer_execution_by_core", "automatic_truth_promotion",
]:
    assert boundary in SERVICE
assert "sc.research-librarian-visual-explanation.v1" in SERVICE
assert "citation_coverage" in SERVICE and "content_hash" in SERVICE
assert "Version: 2.39.0" in WP and "sc_platform_core_research_visual_explanation_status" in WP
assert "research_visual_explanations_readiness" in SDK_PY
assert "researchVisualExplanationsReadiness" in SDK_JS
assert '"version": "2.39.0"' in SDK_JS_PACKAGE
assert 'version = "2.39.0"' in SDK_PY_PROJECT
assert 'sc-platform-core-public-python-v{request.app.state.settings.version}.zip' in PORTAL
assert 'sc-platform-core-public-javascript-v{request.app.state.settings.version}.zip' in PORTAL
assert '"visual-explanations"' in REGISTRY and '"citation-aware-explanations"' in REGISTRY
print(f"PASS - dependency-free release contract; migration ledger max=300, 0043 chars={len(descriptions['0043'])}")
print("PASS - v2.39.0 Research Librarian Visual Explanation release contract")
