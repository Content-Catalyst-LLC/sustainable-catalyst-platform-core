import subprocess,sys
from pathlib import Path

def test_v2460_release_validator_runs_without_site_packages():
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2460_release.py')],cwd=root,text=True,capture_output=True)
    assert p.returncode==0,p.stdout+p.stderr
    assert 'v2.46.0 Forensic Spatial/Temporal Evidence Integration release contract' in p.stdout
