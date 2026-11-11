# Spanner for Flow Steward

Flow Steward extension `flowsteward.data-connector-mcp-toolbox-spanner`, version **1.3.6**.

Connect Spanner to Flow Steward for saved SQL datasets and workflow data changes. Choose the GoogleSQL or PostgreSQL profile to match the database dialect. Dataset operations test the connection, inspect typed schemas, validate queries against selected tables and columns, preview results, execute saved SQL and infer output schemas. Reads use the read-only path and return at most 100 rows and 480 KiB of inline output.

The separate execute_write action accepts one INSERT, UPDATE or DELETE with named parameters, a values object and an optional parameter schema. Parameters let the same SQL step accept different record identifiers and workflow values. For example, read a set of application records, route each record through a review process, then update the processing state or insert the workflow result. Read-only Dataset access stays separate from workflow mutations.

Configure the Google Cloud project, Spanner instance and database, and grant the server’s Application Default Credentials identity access to that database. The selected profile fixes the dialect and parameter binder; it is not a free-form dialect toggle. Schema changes, transaction scripts and database triggers are unavailable. Combine saved reads with explicit updates to connect application records to approvals, notifications and follow-up processing.

Select the Spanner GoogleSQL or Spanner PostgreSQL profile and configure project, instance and database. Provide server-side Application Default Credentials with appropriate database privileges; workflow connections do not accept a password or inline service-account JSON.

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

The bounded SQL subset refuses raw dollar characters and backslashes in read SQL; write SQL also refuses raw dollar characters. Put those values in bound parameters. A top-level read LIMIT accepts one integer literal with an optional integer OFFSET. The existing SQL safety guards and database-specific settings validation remain in force.

## Upgrade compatibility

The visible name is Spanner. The legacy extension ID `flowsteward.data-connector-mcp-toolbox-spanner`, project connection type `toolbox_sql_writer`, dataset connector IDs and action IDs remain unchanged so existing installations and workflows can upgrade. These are internal compatibility identifiers, not a second database selector.

## Technical implementation and packaging

Google MCP Toolbox is implementation tooling, pinned to tag `v1.16.0`, commit `06ea49d9a487a72c22419b5a8d5c22c11f0d7485`. Its fixed native build registers only this repository's Spanner interfaces. Installation and runtime download no drivers. Native binaries are rebuilt for this release.

To package the existing verified binaries:

```sh
python3 scripts/package_extension.py --runtime-target linux-amd64
python3 scripts/package_extension.py --runtime-target linux-arm64
```

`scripts/build_toolbox.sh` is the optional pinned implementation rebuild; it cannot select another database. `toolbox-provenance.json`, `THIRD_PARTY.yml` and root `SHA256SUMS` describe the native payloads. Each installer ZIP contains exactly one executable for its target and target/native metadata. The byte-exact Apache-2.0 license is in `LICENSE`; implementation notices are in `NOTICE`.

## Verification limits

Manifest isolation checks cover friendly names, database-specific fields, credential separation and the exact shipped SQL profiles. Contract tests cover scope/ref checks, parameter separation, test-mode suppression, output bounds and unknown write outcomes. No live Spanner credentials were supplied; compile and contract evidence does not establish a successful authenticated database connection.

Native payloads are rebuilt with pinned Go 1.27.4 and the reviewed module security baseline. Per-target toolchain, linked modules, size and SHA-256 are recorded in `toolbox-provenance.json`; static packaged checks reject stale native dependencies.

The native build freezes the previously approved prebuilt YAML from Toolbox v1.3.0
using `0003-approved-prebuilt-profiles.patch`; the implementation source and recorded
version remain Toolbox v1.16.0. Unused source, tool, prompt and resource registrations
are removed. Managed stdio launches use `--disable-version-check`.

The pinned Go 1.27.3 image supplies only the bootstrap operating environment.
Before any Go command, the build installs the checksum-verified official Go
1.27.4 SDK recorded in `scripts/go-toolchain-sources.json`; provenance records
the installer, selected SDK, and actual compiler embedded in each payload.

## Automated releases

CI runs on pull requests and pushes to `main`. Official releases run through the
pinned shared GitHub Actions workflow using `.github/release-config.json` to test,
package both Linux runtime targets, and publish the release assets automatically.
Manual ZIP uploads are not part of the release process.

After merging the version **1.3.6** update into `main`, create and push its tag:

```sh
git switch main
git pull --ff-only
git tag -a v1.3.6 -m "Release v1.3.6"
git push origin v1.3.6
```

To rerun the workflow for an existing tag without moving it:

```sh
gh workflow run release.yml --ref main -f tag=v1.3.6
```

The manifest remains the source for release identity and catalog descriptions.
The shared workflow installs the verified first-party SDK wheel before test
dependencies. Where native payloads are absent from source, the recipe restores
only the listed missing files from checksum-pinned published archives; the source
packager still verifies their provenance before packaging.
