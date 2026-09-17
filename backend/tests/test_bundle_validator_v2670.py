from pathlib import Path
import subprocess,sys
def test_current_validator_accepts_v2670_tree():
 root=Path(__file__).resolve().parents[2];p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2670_release.py')],cwd=root,capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
def test_v2660_validator_rejects_newer_tree():
 root=Path(__file__).resolve().parents[2];p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2660_release.py')],cwd=root,capture_output=True,text=True);assert p.returncode!=0
