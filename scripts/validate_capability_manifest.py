#!/usr/bin/env python3

import json
import sys
from pathlib import Path


def _fail(msg: str) -> int:
    print(f"[capability-manifest] ERROR: {msg}")
    return 1


def main() -> int:
    root_dir = Path(__file__).resolve().parent.parent
    manifest_path = root_dir / ".agents" / "vendor" / "capability-manifest.json"

    if not manifest_path.exists():
        return _fail(f"Manifest not found: {manifest_path}")

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    capabilities = data.get("capabilities", [])
    if not isinstance(capabilities, list):
        return _fail("'capabilities' must be a list")

    ids: set[str] = set()
    destinations: set[str] = set()

    for item in capabilities:
        capability_id = item.get("id")
        destination = item.get("destination_path")
        if not capability_id or not destination:
            return _fail("Each capability must have 'id' and 'destination_path'")

        if capability_id in ids:
            return _fail(f"Duplicate capability id: {capability_id}")
        ids.add(capability_id)

        if destination in destinations:
            return _fail(f"Duplicate destination path: {destination}")
        destinations.add(destination)

        if not destination.startswith(".agents/vendor/"):
            return _fail(
                f"Destination must be inside .agents/vendor/: {capability_id} -> {destination}"
            )

        target = root_dir / destination
        if not target.exists():
            return _fail(f"Destination file/folder does not exist: {destination}")

    print("[capability-manifest] OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
