from pathlib import Path
import subprocess,sys
def test_v2630_validator_rejects_newer_tree():
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2630_release.py')],cwd=root,text=True,capture_output=True)
    assert p.returncode!=0,'v2.63 validator must reject a v2.64 tree'
