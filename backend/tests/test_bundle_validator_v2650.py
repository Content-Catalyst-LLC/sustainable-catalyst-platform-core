from pathlib import Path
import subprocess,sys
def test_v2650_validator_rejects_newer_current_tree():
    root=Path(__file__).resolve().parents[2];p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2650_release.py')],cwd=root,capture_output=True,text=True);assert p.returncode!=0
def test_v2640_validator_rejects_newer_tree():
    root=Path(__file__).resolve().parents[2];p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2640_release.py')],cwd=root,capture_output=True,text=True);assert p.returncode!=0
