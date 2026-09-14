from pathlib import Path
import subprocess,sys

def test_v249_release_validator():
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2490_release.py')],cwd=root,text=True,capture_output=True)
    assert p.returncode==0,p.stdout+p.stderr
    assert 'v2.49.0 Testimony, Statements & Documentary Evidence release contract' in p.stdout
