import subprocess,sys
from pathlib import Path

def test_v2570_release_validator_rejects_newer_v2580_tree():
    root=Path(__file__).resolve().parents[2]
    r=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2570_release.py')],cwd=root,text=True,capture_output=True)
    assert r.returncode!=0
