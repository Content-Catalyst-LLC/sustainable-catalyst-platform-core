from pathlib import Path
import subprocess,sys
def test_current_validator_accepts_v2740_tree():
 root=Path(__file__).resolve().parents[2]; p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2740_release.py')],cwd=root,capture_output=True,text=True); assert p.returncode==0,p.stdout+p.stderr
def test_v273_validator_rejects_v2740_tree():
 root=Path(__file__).resolve().parents[2]; p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2730_release.py')],cwd=root,capture_output=True,text=True); assert p.returncode!=0
