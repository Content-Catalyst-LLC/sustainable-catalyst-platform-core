from pathlib import Path
import subprocess,sys

def test_v2590_validator_accepts_current_tree():
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,str(root/'scripts/validate_v2590_release.py')],cwd=root,text=True,capture_output=True)
    assert p.returncode==0,p.stdout+p.stderr
