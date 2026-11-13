"""Check source-only CI contracts and freshly generated native metadata fixtures."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import zipfile

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ("toolbox-provenance.json", "SHA256SUMS", "packages.txt", "scripts/go-toolchain-selected.json")


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_binary(path, machine):
    version = b"go1.27.4"
    modules = bytes.fromhex("3077af0c9274080241e1c107e6d618e6f932433186182072008242104116d8f2")
    blob = b"\xff Go buildinf:" + bytes([8, 2]) + bytes(16)
    blob += bytes([len(version)]) + version + bytes([len(modules)]) + modules
    payload = bytearray(256)
    payload[:16] = b"\x7fELF\x02\x01\x01" + bytes(9)
    struct.pack_into("<HHIQQQIHHHHHH", payload, 16, 2, machine, 1, 0, 64, 128, 0, 64, 56, 1, 64, 2, 0)
    struct.pack_into("<IIQQQQQQ", payload, 64, 1, 6, 256, 4096, 4096, len(blob), len(blob), 16)
    struct.pack_into("<IIQQQQIIQQ", payload, 192, 0, 1, 3, 4096, 256, len(blob), 0, 0, 16, 0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(payload) + blob)
    path.chmod(0o755)


def native_fixture(tmp_path, monkeypatch):
    root = tmp_path / "extension"
    root.mkdir()
    shutil.copytree(ROOT / "scripts", root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    for name in ("LICENSE", "NOTICE", "extension.yaml", "variant.json"):
        shutil.copy2(ROOT / name, root / name)
    sources = json.loads((root / "scripts/go-toolchain-sources.json").read_text())
    selected = {"version": sources["version"], "host_arch": "amd64", **sources["archives"]["amd64"]}
    (root / "scripts/go-toolchain-selected.json").write_text(json.dumps(selected))
    (root / "packages.txt").write_text("fixture source registration\n")
    for target, machine in (("linux-amd64", 62), ("linux-arm64", 183)):
        fixture_binary(root / "bin" / target / "toolbox", machine)
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    provenance = load_script("provenance")
    monkeypatch.setattr(provenance, "ROOT", root)
    provenance.main()
    return root


def test_native_metadata_is_regenerated_from_actual_binary_bytes(tmp_path, monkeypatch):
    root = native_fixture(tmp_path, monkeypatch)
    provenance = json.loads((root / "toolbox-provenance.json").read_text())
    assert provenance["upstream_commit"] == "45ed205cc8682ed066c82e0b65bcd0e8fc3becce"
    assert provenance["upstream_tag"] == "v1.17.0"
    expected = []
    for target, record in provenance["binaries"].items():
        binary = root / "bin" / target / "toolbox"
        assert record["sha256"] == hashlib.sha256(binary.read_bytes()).hexdigest()
        assert record["size"] == binary.stat().st_size
        assert record["go_version"] == "go1.27.4"
        expected.append(f"{record['sha256']}  bin/{target}/toolbox\n")
    assert (root / "SHA256SUMS").read_text() == "".join(expected)


def test_package_contains_generated_untracked_native_metadata(tmp_path, monkeypatch):
    root = native_fixture(tmp_path, monkeypatch)
    package = load_script("package_extension")
    archive = package.package_extension(root, "linux-amd64", tmp_path / "out")
    with zipfile.ZipFile(archive) as payload:
        prefix = package.TOP_FOLDER + "/"
        for name in GENERATED:
            assert payload.read(prefix + name) == (root / name).read_bytes()
        assert prefix + "bin/linux-arm64/toolbox" not in payload.namelist()


@pytest.mark.parametrize("missing", GENERATED)
def test_package_rejects_missing_generated_metadata(tmp_path, monkeypatch, missing):
    root = native_fixture(tmp_path, monkeypatch)
    (root / missing).unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        load_script("package_extension").package_extension(root, "linux-amd64", tmp_path / "out")


def test_native_ci_cannot_restore_previous_release_binaries():
    config_path = ROOT / ".github/release-config.json"
    if not config_path.exists():
        pytest.skip("source CI configuration is excluded from installer archives")
    config = json.loads(config_path.read_text())
    assert config["payload_sources"] == []
    assert "tests/test_native_build_contract.py" in config["test_paths"]
    for name in ("ci.yml", "release.yml"):
        workflow = yaml.safe_load((ROOT / ".github/workflows" / name).read_text())
        job = next(iter(workflow["jobs"].values()))
        assert job["with"]["build_native"] is True
    build = (ROOT / "scripts/build_toolbox.sh").read_text()
    assert "${FS_TOOLBOX_SOURCE_DIR:-${TOOLBOX_SOURCE:-}}" in build
    assert "https://github.com/googleapis/mcp-toolbox.git" in build
    assert "-mod=readonly" in build
    assert "/private/tmp/" not in build
    ignored = (ROOT / ".gitignore").read_text().splitlines()
    assert all("/" + name in ignored for name in GENERATED)
    assert "/scripts/native-build-identities.json" not in ignored


def test_committed_build_identities_match_reviewed_patches_and_module_floors():
    identity = json.loads((ROOT / "scripts/native-build-identities.json").read_text())
    assert identity["toolbox_commit"] == "45ed205cc8682ed066c82e0b65bcd0e8fc3becce"
    assert identity["toolbox_tag"] == "v1.17.0"
    patches = list((ROOT / "scripts/patches").glob("*.patch"))
    security_patch = next(path for path in patches if "security" in path.name)
    profile_patch = next(path for path in patches if "profile" in path.name)
    assert identity["module_patch_sha256"] == hashlib.sha256(security_patch.read_bytes()).hexdigest()
    assert identity["profile_patch_sha256"] == hashlib.sha256(profile_patch.read_bytes()).hexdigest()
    baseline = json.loads((ROOT / "scripts/native-security-baseline.json").read_text())
    third_party = yaml.safe_load((ROOT / "THIRD_PARTY.yml").read_text())
    build = third_party["build"]
    if "patched_dependencies" in build:
        assert build["patched_dependencies"] == baseline["modules"]
    else:
        assert build["security_baseline"] == "scripts/native-security-baseline.json"
