import subprocess,sys
from pathlib import Path

def _current_version(root: Path) -> str:
    text=(root/'backend/app/config.py').read_text()
    for line in text.splitlines():
        if 'version: str =' in line:
            return line.split('=',1)[1].strip().strip('\"').strip("'")
    return ''

def test_v274_validator_version_awareness():
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2740_release.py')],cwd=root,capture_output=True,text=True)
    if _current_version(root)=='2.74.0':
        assert p.returncode==0,p.stdout+p.stderr
    else:
        assert p.returncode!=0

def test_v273_validator_rejects_v2740_or_newer_tree():
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2730_release.py')],cwd=root,capture_output=True,text=True)
    assert p.returncode!=0
