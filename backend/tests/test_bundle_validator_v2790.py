from pathlib import Path
import ast


def test_v2790_release_contract():
    root = Path(__file__).resolve().parents[2]
    tree = ast.parse((root / "backend/app/migrations.py").read_text())
    migrations = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(target, "id", None) == "MIGRATIONS" for target in node.targets):
            migrations = ast.literal_eval(node.value)
    migration = next(item for item in migrations if item[0] == "0083")
    assert len(migration[1]) <= 300
    assert (root / "schemas/research-argument-evidentiary-synthesis-v1.schema.json").exists()
