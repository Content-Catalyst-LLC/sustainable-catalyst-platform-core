from pathlib import Path
import ast


def test_v2790_release_contract():
    root = Path(__file__).resolve().parents[2]
    cfg = (root / "backend/app/config.py").read_text()
    assert 'version: str = "2.79.0"' in cfg
    tree = ast.parse((root / "backend/app/migrations.py").read_text())
    migrations = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(target, "id", None) == "MIGRATIONS" for target in node.targets):
            migrations = ast.literal_eval(node.value)
    assert migrations[-1][0] == "0083"
    assert len(migrations[-1][1]) <= 300
    assert (root / "schemas/research-argument-evidentiary-synthesis-v1.schema.json").exists()
    assert (root / "DEPLOY_PLATFORM_CORE_V2790_CONTABO.sh").exists()
