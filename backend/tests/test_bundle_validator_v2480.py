from pathlib import Path
import subprocess,sys

def test_v248_release_validator():
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2480_release.py')],cwd=root,text=True,capture_output=True)
    assert p.returncode==0,p.stdout+p.stderr
    assert 'v2.48.0 Quantitative Reconstruction & Reproduction Handoffs release contract' in p.stdout
