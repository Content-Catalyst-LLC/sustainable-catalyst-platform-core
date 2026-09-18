import subprocess,sys
from pathlib import Path
def test_current_validator_accepts_v2720_tree():
 root=Path(__file__).resolve().parents[2]; p=subprocess.run([sys.executable,"-S",str(root/"scripts/validate_v2720_release.py")],cwd=root,capture_output=True,text=True); assert p.returncode==0,p.stdout+p.stderr
def test_v271_validator_rejects_v2720_tree():
 root=Path(__file__).resolve().parents[2]; p=subprocess.run([sys.executable,"-S",str(root/"scripts/validate_v2710_release.py")],cwd=root,capture_output=True,text=True); assert p.returncode!=0
