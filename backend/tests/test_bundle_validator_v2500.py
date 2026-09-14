from pathlib import Path
import subprocess,sys

def test_v250_release_validator():
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2500_release.py')],cwd=root,text=True,capture_output=True)
    assert p.returncode!=0
    assert '2.50.0' in (p.stdout+p.stderr)
