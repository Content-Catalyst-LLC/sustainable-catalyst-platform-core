from pathlib import Path
import ast


def test_v2800_release_contract():
    root = Path(__file__).resolve().parents[2]
    cfg = (root / "backend/app/config.py").read_text()
    assert 'version: str = "2.80.0"' in cfg
    tree = ast.parse((root / "backend/app/migrations.py").read_text())
    migrations = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(target, "id", None) == "MIGRATIONS" for target in node.targets):
            migrations = ast.literal_eval(node.value)
    assert migrations[-1][0] == "0084"
    assert len(migrations[-1][1]) <= 300
    assert (root / "schemas/research-decision-trace-conclusion-governance-v1.schema.json").exists()
    assert (root / "DEPLOY_PLATFORM_CORE_V2800_CONTABO.sh").exists()
    assert (root / "PUSH_PLATFORM_CORE_V2800_FINAL.sh").exists()
