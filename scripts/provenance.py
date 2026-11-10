#!/usr/bin/env python3
"""Record pinned native build provenance and per-target SHA-256 values."""

import hashlib
import json
from pathlib import Path

from native_security import check_floors, inspect_binary

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ("linux-amd64", "linux-arm64")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def binary_modules(path):
    # Static inspection only; release payloads are never executed here.
    record = inspect_binary(path)
    baseline = json.loads((ROOT / "scripts/native-security-baseline.json").read_text())
    check_floors(record, baseline)
    return {"go_modules": record["modules"], "go_version": record["go_version"]}


def main():
    records = {
        target: {
            "path": f"bin/{target}/toolbox",
            **binary_modules(ROOT / f"bin/{target}/toolbox"),
            "sha256": digest(ROOT / f"bin/{target}/toolbox"),
            "size": (ROOT / f"bin/{target}/toolbox").stat().st_size,
        }
        for target in TARGETS
    }
    data = {
        "upstream_commit": "b0010060a939455d91e4f8ba62dc3e72b1892469",
        "upstream_tag": "v1.3.0",
        "source": "https://github.com/googleapis/mcp-toolbox",
        "go_image": (
            "golang:1.26.10-bookworm@sha256:"
            "5de7c99eb78ca5e515a4c340235d0955ec5964a5071c492c15503d7c267da473"
        ),
        "registered_prebuilts": (ROOT / "scripts/toolbox-prebuilts.txt").read_text().split(),
        "patch_sha256": digest(
            ROOT / "scripts/patches/0001-flowsteward-driver-bound-query-params.patch"
        ),
        "dependency_patches": {
            "scripts/patches/0002-go-security-baseline.patch": digest(
                ROOT / "scripts/patches/0002-go-security-baseline.patch"
            )
        },
        "binaries": records,
    }
    (ROOT / "toolbox-provenance.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    (ROOT / "SHA256SUMS").write_text(
        "".join(f"{record['sha256']}  {record['path']}\n" for record in records.values())
    )


if __name__ == "__main__":
    main()
