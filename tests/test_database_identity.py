"""One database per installable extension, with settings the pinned runtime uses."""

from pathlib import Path
import ast
import json
import yaml
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATABASE = "spanner"
NAME = "Spanner"
EXPECTED_FIELDS = ["project", "instance", "database", "dialect"]
EXPECTED_PREBUILTS = ["spanner", "spanner-postgres"]
PUBLIC_ENV = [
    "SPANNER_PROJECT",
    "SPANNER_INSTANCE",
    "SPANNER_DATABASE",
    "SPANNER_DIALECT",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_QUOTA_PROJECT",
    "GOOGLE_CLOUD_UNIVERSE_DOMAIN",
    "GOOGLE_API_USE_MTLS_ENDPOINT",
    "GOOGLE_API_USE_CLIENT_CERTIFICATE",
    "SPANNER_EMULATOR_HOST",
]
SECRET_ENV = ["GOOGLE_APPLICATION_CREDENTIALS"]


def manifest():
    return yaml.safe_load((ROOT / "extension.yaml").read_text())


def test_one_database_identity_and_friendly_names():
    data = manifest()
    contract = data["runtime"]["extension_contract_v2"]
    assert data["extension_id"] == "flowsteward.data-connector-mcp-toolbox-" + DATABASE
    assert data["display_name"] == NAME
    assert data["version"] == "1.3.0"
    assert len(contract["connection_types"]) == len(contract["dataset_connectors"]) == 1
    writer = contract["connection_types"][0]
    dataset = contract["dataset_connectors"][0]
    assert writer["connection_type_id"] == "toolbox_sql_writer"
    assert writer["display_name"] == NAME + " connection"
    assert dataset["connector_id"] == dataset["connector_type_id"] == "toolbox_database"
    assert dataset["display_name"] == NAME + " database"
    assert dataset["source_extension_name"] == dataset["source_provider"] == NAME
    variant = json.loads((ROOT / "variant.json").read_text())
    assert variant == {"prebuilts": EXPECTED_PREBUILTS, "display_name": NAME}


@pytest.mark.parametrize("surface", ["extension", "writer", "dataset"])
def test_settings_expose_only_this_database(surface):
    data = manifest()["runtime"]["extension_contract_v2"]
    schema = (
        yaml.safe_load((ROOT / "schemas/config.schema.yaml").read_text())
        if surface == "extension"
        else data["connection_types"][0]["config_schema"]
        if surface == "writer"
        else data["dataset_connectors"][0]["connection_schema"]
    )
    expected = {"prebuilt", *EXPECTED_FIELDS}
    if surface != "writer":
        expected.add("env")
    assert set(schema["properties"]) == expected
    assert set(schema["properties"]["prebuilt"]["enum"]) == set(EXPECTED_PREBUILTS)
    assert schema["additionalProperties"] is False
    assert "allOf" not in schema  # No hidden all-database conditional branches.
    if "env" in schema["properties"]:
        env = schema["properties"]["env"]
        assert env["additionalProperties"] is False
        assert set(env["properties"]) == set(PUBLIC_ENV)


def test_all_runtime_mapped_settings_are_retained():
    tree = ast.parse((ROOT / "main.py").read_text())
    mapping = next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "TOOLBOX_ENV_FIELDS"
    )
    required = set().union(*(set(mapping[p].values()) for p in EXPECTED_PREBUILTS)) - {"password"}
    assert set(EXPECTED_FIELDS) == required


def test_credentials_match_the_database_authentication():
    contract = manifest()["runtime"]["extension_contract_v2"]
    writer = contract["connection_types"][0]["secret_schema"]
    expected = set() if DATABASE == "spanner" else {"password"}
    assert set(writer["properties"]) == expected
    for schema in [
        contract["dataset_connectors"][0]["secret_schema"],
        yaml.safe_load((ROOT / "schemas/secrets.schema.yaml").read_text()),
    ]:
        assert set(schema["properties"]) == expected | {"env"}
        assert schema["properties"]["env"]["additionalProperties"] is False
        assert set(schema["properties"]["env"]["properties"]) == set(SECRET_ENV)


def test_build_metadata_registers_only_this_database():
    data = manifest()["runtime"]["extension_contract_v2"]["dataset_connectors"][0]
    assert {r["source_kind"] for r in data["connector_catalog"]} == set(EXPECTED_PREBUILTS)
    assert set((ROOT / "scripts/toolbox-prebuilts.txt").read_text().split()) == set(
        EXPECTED_PREBUILTS
    )
    native = json.loads((ROOT / "toolbox-provenance.json").read_text())
    assert set(native["binaries"]) == {"linux-amd64", "linux-arm64"}
    assert sorted(
        yaml.safe_load((ROOT / "THIRD_PARTY.yml").read_text())["build"]["registered_prebuilts"]
    ) == sorted(EXPECTED_PREBUILTS)


def test_visible_ui_describes_only_this_database():
    visible = (ROOT / "extension.yaml").read_text() + "\n" + (ROOT / "variant.json").read_text()
    visible += "\n" + "\n".join(p.read_text() for p in (ROOT / "ui").rglob("*.yaml"))
    for forbidden in [
        "Data Connector MCP Toolbox",
        "Toolbox SQL writer",
        "Google MCP Toolbox database source",
        "Google MCP Toolbox",
    ]:
        assert forbidden not in visible
    setup = yaml.safe_load((ROOT / "ui/components/overview.yaml").read_text())
    assert NAME in setup["title"]
    assert NAME in setup["body"]
