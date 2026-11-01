# Google Cloud Spanner for Flow Steward

Standalone repository: [Flow-Steward/ext-data-spanner](https://github.com/Flow-Steward/ext-data-spanner). Version **1.2.0** preserves the existing extension ID `flowsteward.data-connector-mcp-toolbox-spanner` and publishes separate Linux AMD64 and ARM64 archives. The packaged native executable contains only this variant’s upstream source and tools.

## Dataset reads

The existing dataset connector supports connection testing, typed schema introspection, saved SQL, visual query scope validation, preview and execution. Runtime values stay separate from SQL text and use native driver parameters. Dataset queries use the native `execute_sql_dql` read-only transaction path and are capped at 100 rows and 480 KiB inline output. This extension exposes no trigger surface.

## Workflow writes

`execute_write` accepts one INSERT, UPDATE or DELETE, using named placeholders such as `UPDATE products SET name = :name WHERE sku = :sku`. Provide `connection_ref`, `sql`, a `params` object and an optional JSON `param_schema`. Database-specific syntax must be supported by the selected server.

The host supplies the matching project connection of type `toolbox_sql_writer`, resolved config/secrets, account/project scope, the exact host-v2 step execution context and a durable `external_effect_id`. Inline connection configuration and secrets are rejected. Test mode suppresses the write before starting a database driver. SQL writes run once on a dedicated driver connection; Spanner uses statement-based Update and explicit Commit without a transaction retry loop. A dispatched failure has an unknown outcome, returns `retryable: false`, and must be inspected before a manual retry.

Successful writes return `status: executed`, `rows`, and `returned_row_count`. Drivers may return an `affected_rows` metadata row. Workflow writes do not turn the dataset read surface into a writable SQL surface.

## Connection and authentication

Select `spanner` for GoogleSQL or `spanner-postgres` for the PostgreSQL dialect; configure cloud project, instance and database. The upstream Google client uses Application Default Credentials inherited by the packaged subprocess. No per-connection service-account JSON field is implemented and no credentials are bundled.

## Rebuild and package

Google MCP Toolbox is pinned to tag `v1.3.0`, commit `b0010060a939455d91e4f8ba62dc3e72b1892469`; the Go container is pinned by digest in `scripts/build_toolbox.sh`.

```sh
./scripts/build_toolbox.sh
python3 scripts/package_extension.py --runtime-target linux-amd64
python3 scripts/package_extension.py --runtime-target linux-arm64
```

The resource-capped Docker builder applies the checked-in native patch, runs binding/source regression tests, and builds both architectures. `toolbox-provenance.json` records source, image, patch digest and native binary SHA-256 values. `SHA256SUMS` records native checksums; `dist/SHA256SUMS` records the two installer archives. The package has exactly its target executable and `.fs-package.yaml` metadata. Builds require upstream source downloads; installation and runtime do not download a driver.

The byte-exact upstream Apache license is preserved in `LICENSE` (SHA-256 `58d1e17ffe5109a7ae296caafcadfdbe6a7d176f0bc4ab01e12a689b0499d8bd`); see `NOTICE` and `THIRD_PARTY.yml`.

## Validation scope

Python extension gates validate host contracts, parameter separation, scope/ref checks, test suppression, output bounds and unknown write outcomes. Native recording-driver tests assert one DML dispatch, including `driver.ErrBadConn`, with SQL and values separate. SQLite additionally exercises real temporary-file INSERT/UPDATE/DELETE with the packaged source driver. Authenticated external services were unavailable: no live Google Cloud Spanner service success is claimed by compile and contract evidence alone.

Read SQL containing a raw backslash or a dollar-quote delimiter (`$$` / `$tag$`), including inside identifiers, is refused before comment/quote parsing; put data values in bound parameters. Top-level LIMIT accepts one integer literal and an optional integer OFFSET; arithmetic limits and comma-offset forms are refused. SQL Server set queries are refused by the bounded TOP form.

Write SQL also refuses raw dollar-quote delimiters before the single-DML scanner, including delimiters inside identifiers. Dollar text and backslashes remain supported in bound data values.

The SQL subset rejects **every raw `$` character** before any read/write lexer, including Unicode dollar tags, quoted text and identifiers. Use named `:parameters` for dollar-containing data. Driver placeholders such as PostgreSQL `$1` are generated only after validation; bound values are unchanged.
