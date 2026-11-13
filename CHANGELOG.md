## 1.3.4 — 2026-11-10

- Rebuild the same Toolbox source and module graph with checksum-pinned Go 1.27.4.
- Preserve approved profiles, bound queries and existing native safety controls.

## 1.3.3 — 2026-11-10

- Upgrade pinned Toolbox to v1.16.0 and Go 1.27.3 with the reviewed dependency graph.
- Retain approved database profiles, driver parameter binding and native security gates.
- Disable startup version checks for fixed offline stdio launches.

# Changelog

## 1.3.7

- Clarify workflow action names, descriptions and field help; add setup and input examples. Existing action IDs, input schemas and runtime behavior are preserved. Move the unchanged test launcher under tests/ so installer runtime checks accept the package.


## 1.3.2

- Rebuild both native targets with Go 1.26.10 and the reviewed module security baseline.
- Retain pinned Toolbox source and driver-bound query safety controls.
- Record actual per-target linked modules and reject stale payloads before release.

## 1.3.1

- Use official database brand artwork with recorded source attribution.


## 1.3.0

- Bind GoogleSQL and PostgreSQL parameter styles to their fixed Spanner interfaces and reject mismatched dialect overrides.

- Forward resolved nested secret environment overrides without changing established precedence.

- Show Spanner throughout setup, connections, dataset catalog and workflow actions.
- Expose only supported Spanner settings and SQL interfaces; preserve relevant authentication and cloud settings.
- Preserve stable extension/connection/action IDs, SQL safety guards, native binaries and provenance.
- Keep the existing 1.2.0 release immutable; publish separate 1.3.0 target archives.

## 1.2.0

- Publish spanner as its own repository and two Linux architecture archives, preserving the existing extension ID.
- Add workflow INSERT, UPDATE and DELETE through native bound driver parameters and explicit host-resolved project connections. No trigger surface is exposed.
- Require account/project scope and an external-effect claim; suppress test-mode writes and report uncertain outcomes without automatic retries.
- Execute SQL writes on a dedicated connection; Spanner uses statement-based DML with explicit commit.
- Preserve dataset saved SQL and visual query scope behavior, capped at 100 rows and 480 KiB inline responses.
- Preserve the byte-exact upstream Apache license and include reproducible pinned-source native builds.

## 1.1.2

- A saved query may use SQL keywords before a parenthesis: `JOIN … USING (id)`,
  `ON (…)`, `EXISTS (subquery)` and `IN (…)`, including a plain `IN ('open', 'paid')`
  list. The read-only check took each of them for a call to an unknown function and
  refused the query. A name that does call something must still be a known
  read-only function, so `nextval(…)`, `pg_sleep(…)` or `dblink_exec(…)` inside
  those parentheses are refused as before.

## 1.1.1

- The logo (`icon.png`) now has a transparent background; in 1.1.0 the Flow Steward wave sat on a black box on dark themes.

## 1.1.0

- Speaks the final extension host contract `extension_host_v2`
  (`runtime.contract_version`) and is built on `flowsteward-extension-sdk` 0.4.0.
  A request of another contract, with a missing execution-scope key
  (`group_id`, `for_each_id`, `step_id`, `step_execution_id`), with both a Group
  and a For each as its owner, or with a step but no step execution, is refused
  with `invalid_host_envelope` before Toolbox is started. An older Flow Steward
  does not run this release.
- Works the same for a step at the root, in a Group or in a For each.
- Logo: `icon.png`, the Flow Steward wave mark.

## 1.0.0

- Initial reference release for Flow Steward dataset connectors.
- Adds read-only Google MCP Toolbox database connector operations for connection tests, schema introspection, query validation, preview, execution, and output-schema inference.
- Includes declarative extension UI pages and a deterministic local smoke test fixture.
- Packages checksum-verified linux-amd64 and linux-arm64 Google MCP Toolbox 1.3.0 source builds.
- Uses bounded MCP stdio with timeout cleanup and sanitized protocol failures.
- Removes SQLite and all private extension persistence paths.
