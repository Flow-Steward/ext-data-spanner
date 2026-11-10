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


def toolchain_install():
    sources = json.loads((ROOT / "scripts/go-toolchain-sources.json").read_text())
    selected = json.loads((ROOT / "scripts/go-toolchain-selected.json").read_text())
    if selected.get("version") != sources.get("version") or selected.get("version") != "go1.27.4":
        raise ValueError("Selected SDK differs from the reviewed compiler")
    expected = sources["archives"][selected["host_arch"]]
    if any(selected.get(key) != expected[key] for key in ("url", "sha256")):
        raise ValueError("Selected SDK URL/hash differs from the reviewed archive")
    return {
        "helper_path": "scripts/install-go-toolchain.sh",
        "helper_sha256": digest(ROOT / "scripts/install-go-toolchain.sh"),
        "sources": sources,
        "selected_sdk": selected,
    }


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
        "upstream_commit": "06ea49d9a487a72c22419b5a8d5c22c11f0d7485",
        "upstream_tag": "v1.16.0",
        "source": "https://github.com/googleapis/mcp-toolbox",
        "go_image": (
            "golang:1.27.3-bookworm@sha256:"
            "dc0963f32053e4bc451d24d87e3892d42d01021b61f093e98eb95c0352bb84b0"
        ),
        "go_image_role": "bootstrap",
        "go_toolchain_install": toolchain_install(),
        "registered_prebuilts": (ROOT / "scripts/toolbox-prebuilts.txt").read_text().split(),
        "patch_sha256": digest(
            ROOT / "scripts/patches/0001-flowsteward-driver-bound-query-params.patch"
        ),
        "dependency_patches": {
            "scripts/patches/0003-approved-prebuilt-profiles.patch": digest(
                ROOT / "scripts/patches/0003-approved-prebuilt-profiles.patch"
            ),
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
