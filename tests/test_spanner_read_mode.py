"""Spanner reads must use the upstream read-only tool, not a write transaction."""

import pytest
import main


@pytest.mark.parametrize("prebuilt", ["spanner", "spanner-postgres"])
def test_dataset_read_uses_read_only_native_tool(monkeypatch, prebuilt):
    monkeypatch.setattr(main, "_connection_config", lambda request: {"prebuilt": prebuilt})
    monkeypatch.setattr(
        main, "_query_definition", lambda request: {"sql": "SELECT sku FROM products WHERE sku='a'"}
    )
    monkeypatch.setattr(main, "_dataset_scope", lambda request: {"products": None})
    calls = []

    def invoke(config, secrets, tool, params, **kwargs):
        calls.append(tool)
        return [{"sku": "a"}]

    monkeypatch.setattr(main, "_invoke_toolbox", invoke)
    result = main._execute_sql({"action": {"input": {}}}, preview=False)
    assert calls == ["execute_sql_dql"]
    assert result["rows"] == [{"sku": "a"}]
