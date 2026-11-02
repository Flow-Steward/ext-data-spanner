# Spanner for Flow Steward

Connect **Spanner** datasets and run parameterized workflow writes. This repository contains one installable Spanner extension, version **1.3.1**, with separate Linux AMD64 and ARM64 archives. No other database can be selected or installed from this package.

## Set up a Spanner connection

Create a project connection using these settings:

| Setting | Meaning |
| --- | --- |
| `project` | Spanner google cloud project. Required. |
| `instance` | Spanner spanner instance. Required. |
| `database` | Spanner database. Required. |

Choose **Spanner (GoogleSQL)** (`spanner`) or **Spanner (PostgreSQL)** (`spanner-postgres`). Both are interfaces to the same database product. The profile fixes both the native SQL dialect and parameter binder. There is no separate editable dialect setting: choose the PostgreSQL profile for PostgreSQL SQL. Conflicting legacy dialect values are rejected before a provider starts.

The server uses Application Default Credentials inherited by the native subprocess. Grant the service identity access to the selected project, instance and database. There is no connection password or service-account JSON contents field. Dataset advanced environment preserves the named Spanner project/instance/database variables, Google project/quota/universe and mTLS settings, emulator host, and the server-side `GOOGLE_APPLICATION_CREDENTIALS` path in secret environment. Resolved dataset secret environment values are forwarded to the native process. Workflow writes use the server's inherited ADC identity; their connection settings do not accept an arbitrary environment map. Ambient SPANNER_DIALECT cannot override the selected interface.

## Read datasets and write from workflows

Datasets support connection testing, typed schema introspection, saved SQL, visual-query resource scope validation, bounded previews and execution. Read queries use the native read-only path and are capped at 100 rows and 480 KiB inline output. No trigger surface is exposed.

`execute_write` runs one INSERT, UPDATE or DELETE on the selected Spanner project connection. Provide `connection_ref`, SQL with named `:parameters`, a `params` object and optional JSON `param_schema`. Values stay separate from SQL and use native driver binding. The server must support the supplied SQL syntax.

The host resolves matching project configuration and secrets, account/project scope, execution context and a durable external-effect claim. Test mode suppresses writes before a driver starts. Writes execute once; uncertain dispatched failures return `retryable: false` and require checking the database before a manual retry. Workflow writes do not make dataset queries writable.

The bounded SQL subset refuses raw dollar characters and backslashes in read SQL; write SQL also refuses raw dollar characters. Put those values in bound parameters. A top-level read LIMIT accepts one integer literal with an optional integer OFFSET. The existing SQL safety guards are unchanged; 1.3.0 adds database-specific settings validation and preserves native payloads.

## Upgrade compatibility

The visible name is Spanner. The legacy extension ID `flowsteward.data-connector-mcp-toolbox-spanner`, project connection type `toolbox_sql_writer`, dataset connector IDs and action IDs remain unchanged so existing installations and workflows can upgrade. These are internal compatibility identifiers, not a second database selector.

## Technical implementation and packaging

Google MCP Toolbox is implementation tooling, pinned to tag `v1.3.0`, commit `b0010060a939455d91e4f8ba62dc3e72b1892469`. Its fixed native build registers only this repository's Spanner interfaces. Installation and runtime download no drivers. Existing native binaries and provenance are unchanged by the 1.3.0 UI/schema correction.

To package the existing verified binaries:

```sh
python3 scripts/package_extension.py --runtime-target linux-amd64
python3 scripts/package_extension.py --runtime-target linux-arm64
```

`scripts/build_toolbox.sh` is the optional pinned implementation rebuild; it cannot select another database. `toolbox-provenance.json`, `THIRD_PARTY.yml` and root `SHA256SUMS` describe the native payloads. Each installer ZIP contains exactly one executable for its target and target/native metadata. The byte-exact Apache-2.0 license is in `LICENSE`; implementation notices are in `NOTICE`.

## Verification limits

Manifest isolation checks cover friendly names, database-specific fields, credential separation and the exact shipped SQL profiles. Contract tests cover scope/ref checks, parameter separation, test-mode suppression, output bounds and unknown write outcomes. No live Spanner credentials were supplied; compile and contract evidence does not establish a successful authenticated database connection.
