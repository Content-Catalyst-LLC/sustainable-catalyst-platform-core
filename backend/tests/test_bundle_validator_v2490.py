from pathlib import Path
import subprocess,sys

def test_v249_validator_rejects_newer_v250_tree():
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2490_release.py')],cwd=root,text=True,capture_output=True)
    assert p.returncode != 0
