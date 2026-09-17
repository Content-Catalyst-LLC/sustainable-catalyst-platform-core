from pathlib import Path
import subprocess, sys, re


def _current_version(root: Path) -> str:
    text=(root/'backend/app/config.py').read_text()
    m=re.search(r'version:\s*str\s*=\s*"([^"]+)"', text)
    assert m, 'Platform Core version not found in config.py'
    return m.group(1)


def test_v2660_validator_matches_tree_version():
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2660_release.py')],cwd=root,capture_output=True,text=True)
    if _current_version(root) == '2.66.0':
        assert p.returncode == 0, p.stdout+p.stderr
    else:
        assert p.returncode != 0, 'v2.66 validator must reject a newer tree'


def test_v2650_validator_rejects_newer_tree():
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-S',str(root/'scripts/validate_v2650_release.py')],cwd=root,capture_output=True,text=True)
    assert p.returncode != 0
