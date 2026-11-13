# Spanner workflow writes

Use a **Dataset saved query** to read rows with SELECT. Use **SQL: Insert, update or delete rows**
(`execute_write`) when a workflow must insert, update or delete data, for example
to record the outcome of an approval or import job.

## Configure the connection

Create a Spanner project connection using one of the profiles listed in this
extension's connection form. Configure its database endpoint/profile fields and
place credentials in connection secrets. Select that connection in the workflow
action. The database user needs permission on the target table. The connection
setup and supported profiles are described in the repository README.

## Save a processing result

1. Add **SQL: Insert, update or delete rows** and select the connection.
2. Set **SQL write statement** to one statement supported by your database:

   ```sql
   INSERT INTO workflow_results (record_id, status) VALUES (:record_id, :status)
   ```

3. Set **Parameters (JSON)**, binding workflow values as needed:

   ```json
   {"record_id":1042,"status":"approved"}
   ```

4. Set **Parameter types (JSON Schema)** to declare every SQL placeholder:

   ```json
   {"type":"object","properties":{"record_id":{"type":"integer"},"status":{"type":"string"}},"required":["record_id","status"]}
   ```

Use the same fields for a single UPDATE or DELETE. Named values remain separate
from SQL and are bound by the database driver. Do not use multi-statement scripts,
DDL or transaction-control commands. The connector does not translate statements
between SQL dialects; the server must support the supplied syntax.

Parameter types are required whenever placeholders are used; supported scalar
types are string, integer, number, boolean and null. Omit Parameters and the type
schema only for a statement without placeholders.

The result reports execution status and any returned rows. `returned_row_count`
counts returned rows, not every affected row. Test mode validates the input and
suppresses the write. If the connection fails after dispatch, inspect the database
before repeating the action because the statement may already have committed.
