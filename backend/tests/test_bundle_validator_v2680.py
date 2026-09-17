import subprocess,sys
from pathlib import Path
def test_v2680_validator_rejects_newer_tree():
 root=Path(__file__).resolve().parents[2];p=subprocess.run([sys.executable,"-S",str(root/"scripts/validate_v2680_release.py")],cwd=root,capture_output=True,text=True);assert p.returncode!=0
