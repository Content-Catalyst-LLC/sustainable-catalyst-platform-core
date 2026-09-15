import subprocess,sys
from pathlib import Path
from app.config import Settings

def test_v2600_release_validator_is_release_specific():
    root=Path(__file__).resolve().parents[2]
    r=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2600_release.py')],cwd=root,text=True,capture_output=True)
    if Settings().version=='2.60.0':
        assert r.returncode==0,r.stdout+r.stderr
    else:
        assert r.returncode!=0,'v2.60 validator must reject a newer release tree'
