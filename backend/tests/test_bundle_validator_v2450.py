import subprocess,sys
from pathlib import Path

def test_v2450_release_validator_rejects_newer_v2460_source():
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2450_release.py')],cwd=root,text=True,capture_output=True)
    assert p.returncode != 0
