import subprocess,sys
from pathlib import Path
import pytest


def test_release_validator_runs_without_site_packages():
    root=Path(__file__).resolve().parents[2]
    cfg=(root/'backend/app/config.py').read_text()
    if 'version: str = "2.37.0.2"' not in cfg:
        pytest.skip('historical v2.37.0.2 release validator is superseded by the current release validator')
    proc=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2370_2_release.py')],cwd=root,text=True,capture_output=True)
    assert proc.returncode==0,proc.stdout+proc.stderr
    assert 'dependency-free release contract' in proc.stdout
