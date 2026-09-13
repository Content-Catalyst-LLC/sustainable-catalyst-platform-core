import subprocess
import sys
from pathlib import Path


def test_v2390_release_validator_runs_without_site_packages():
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run([sys.executable, "-S", str(root / "scripts/validate_v2390_release.py")], cwd=root, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "dependency-free release contract" in result.stdout
