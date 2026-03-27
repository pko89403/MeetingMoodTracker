import json
import subprocess
import sys
from pathlib import Path


def test_capability_manifest_integrity() -> None:
    root_dir = Path(__file__).parent.parent.parent
    manifest_path = root_dir / ".agents" / "vendor" / "capability-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    capabilities = manifest["capabilities"]

    ids: set[str] = set()
    destinations: set[str] = set()
    for item in capabilities:
        capability_id = item["id"]
        destination = item["destination_path"]
        assert capability_id not in ids
        ids.add(capability_id)

        assert destination not in destinations
        destinations.add(destination)

        assert destination.startswith(".agents/vendor/")
        assert (root_dir / destination).exists()


def test_capability_manifest_validator_script() -> None:
    root_dir = Path(__file__).parent.parent.parent
    result = subprocess.run(
        [sys.executable, "scripts/validate_capability_manifest.py"],
        cwd=str(root_dir),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
