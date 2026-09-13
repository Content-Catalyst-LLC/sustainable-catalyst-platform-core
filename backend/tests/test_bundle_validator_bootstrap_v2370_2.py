import subprocess
import sys
from pathlib import Path


def test_release_validator_runs_without_site_packages():
    root = Path(__file__).resolve().parents[2]
    proc = subprocess.run(
        [sys.executable, '-S', str(root/'scripts/validate_v2370_2_release.py')],
        cwd=root,
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert 'dependency-free release contract' in proc.stdout
