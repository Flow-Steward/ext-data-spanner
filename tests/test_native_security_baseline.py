"""Release gates inspect actual linked modules without running Linux payloads."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("native_inspector", ROOT / "scripts/native_security.py")
SECURITY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SECURITY)
BASELINE = json.loads((ROOT / "scripts/native-security-baseline.json").read_text())


@pytest.mark.packaged
@pytest.mark.parametrize("target", ["linux-amd64", "linux-arm64"])
def test_shipped_native_security_floors_and_provenance(target):
    binary = ROOT / "bin" / target / "toolbox"
    actual = SECURITY.inspect_binary(binary)
    SECURITY.check_floors(actual, BASELINE)
    provenance = json.loads((ROOT / "toolbox-provenance.json").read_text())
    record = provenance["binaries"][target]
    assert provenance["go_image_role"] == "bootstrap"
    install = provenance["go_toolchain_install"]
    assert install["helper_sha256"] == hashlib.sha256(
        (ROOT / install["helper_path"]).read_bytes()
    ).hexdigest()
    assert install["sources"] == json.loads(
        (ROOT / "scripts/go-toolchain-sources.json").read_text()
    )
    assert install["selected_sdk"]["version"] == "go1.27.4"
    sdk = install["sources"]["archives"][install["selected_sdk"]["host_arch"]]
    assert install["selected_sdk"]["url"] == sdk["url"]
    assert install["selected_sdk"]["sha256"] == sdk["sha256"]
    assert record["go_modules"] == actual["modules"]
    assert record["go_version"] == actual["go_version"] == "go1.27.4"
    assert record["sha256"] == hashlib.sha256(binary.read_bytes()).hexdigest()
    assert record["size"] == binary.stat().st_size


@pytest.mark.parametrize("version", ["go1.26.2", "go1.26.10", "go1.27.0", "go1.27.1", "go1.27.3"])
def test_unreviewed_toolchain_is_rejected_including_prior_compiler(version):
    with pytest.raises(ValueError, match="reviewed"):
        SECURITY.check_floors(
            {"go_version": version, "modules": {}, "module_gaps": []}, BASELINE
        )


def test_native_metadata_rejects_all_module_replacements():
    with pytest.raises(ValueError, match="replacements"):
        SECURITY._modules("dep\texample.com/module\tv1.0.0\th1:abc\n=>\texample.com/replacement\tv2.0.0\th1:def\n", [], "fixture")
