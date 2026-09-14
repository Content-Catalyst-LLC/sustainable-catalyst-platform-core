from pathlib import Path
import subprocess,sys

def test_v251_release_validator():
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2510_release.py')],cwd=root,text=True,capture_output=True)
    assert p.returncode==0,p.stdout+p.stderr
    assert 'v2.51.0 Reproducible Investigation Packages release contract' in p.stdout
