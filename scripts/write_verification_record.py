#!/usr/bin/env python3
"""Emit CI evidence after a successful proof check."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    manifest_path = ROOT / "proof-manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)

    aggregate = hashlib.sha256()
    for source in sorted(manifest["sources"], key=lambda entry: entry["path"]):
        aggregate.update(source["path"].encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(bytes.fromhex(source["sha256"]))

    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repository = os.environ.get("GITHUB_REPOSITORY", "local")
    run_id = os.environ.get("GITHUB_RUN_ID")
    run_url = f"{server_url}/{repository}/actions/runs/{run_id}" if run_id else None

    record = {
        "schema_version": 1,
        "result": "passed",
        "exit_code": 0,
        "result_derivation": (
            "The record writer runs only after the manifest command exits with "
            "status 0; therefore exit_code 0 maps to result passed."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "repository": repository,
        "commit": os.environ.get("GITHUB_SHA", "local-uncommitted"),
        "run_id": run_id,
        "run_url": run_url,
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "proof_sources_sha256": aggregate.hexdigest(),
        "toolchain": manifest["toolchain"],
        "command": manifest["verification"]["command"],
    }

    output = arguments.output
    if not output.is_absolute():
        output = ROOT / output
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {output} ({sha256_file(output)})")


if __name__ == "__main__":
    main()
