from pathlib import Path
import subprocess,sys
def test_v2760_validator_is_version_aware():
 root=Path(__file__).resolve().parents[2];p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2760_release.py')],cwd=root,capture_output=True,text=True);assert (p.returncode == 0) == ('version: str = "2.76.0"' in (root/"backend/app/config.py").read_text()),p.stdout+p.stderr
def test_v275_validator_rejects_v2760_tree():
 root=Path(__file__).resolve().parents[2];p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2750_release.py')],cwd=root,capture_output=True,text=True);assert p.returncode!=0
