"""The release command must reject unsafe bytes even with truthful checksums."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def packager():
    spec = importlib.util.spec_from_file_location("release_packager", ROOT / "scripts/package_extension.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.packaged
@pytest.mark.parametrize("target", ["linux-amd64", "linux-arm64"])
@pytest.mark.parametrize("fault", ["toolchain", "module", "provenance"])
def test_release_preflight_rejects_truthfully_hashed_unsafe_payload(tmp_path, target, fault):
    binary = ROOT / "bin" / target / "toolbox"
    blob = binary.read_bytes()
    provenance = json.loads((ROOT / "toolbox-provenance.json").read_text())
    record = provenance["binaries"][target]
    if fault == "toolchain":
        version = record.get("go_version", "go1.26.2")
        # Preserve ELF offsets while moving to an unreviewed, numerically newer branch.
        unsafe = "go1.27.0" if len(version) == 8 else "go1.27.10"
        assert len(unsafe) == len(version) and version.encode() in blob
        blob = blob.replace(version.encode(), unsafe.encode())
        record["go_version"] = unsafe
    elif fault == "module":
        name = "github.com/go-chi/chi/v5"
        version = record.get("go_modules", {}).get(name, "v5.2.5")
        old = f"dep\t{name}\t{version}\t".encode()
        new = f"dep\t{name}\tv5.0.0\t".encode()
        assert old in blob and len(old) == len(new)
        blob = blob.replace(old, new)
        record.setdefault("go_modules", {})[name] = "v5.0.0"
    else:
        record["go_modules"] = {}
    record["sha256"] = hashlib.sha256(blob).hexdigest()
    record["size"] = len(blob)
    destination = tmp_path / "bin" / target / "toolbox"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(blob)
    destination.chmod(0o755)
    (tmp_path / "toolbox-provenance.json").write_text(json.dumps(provenance))
    message = {"toolchain": "reviewed", "module": "module below security floor",
               "provenance": "module inventory"}[fault]
    with pytest.raises(ValueError, match=message):
        packager()._native_metadata(tmp_path, target)
