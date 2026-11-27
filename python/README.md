# Demo index

One folder per feature. Each has `before.py` (the old way) and `after.py` (with
the MariaDB feature). Start the database first (`docker compose up -d`, see the
[main README](../README.md)), then run from the repository root.

| Feature | Init script | Run | What you will see |
|---|---|---|---|
| `INET4` / `INET6` | `01_inet.sql`, `03_inet.sql` | `python python/ip_addresses/after.py`<br>`python python/inet/after.py` | Numeric sort, 4-byte storage, error 1292 for invalid addresses |
| `UUID` | `04_uuid.sql` | `python python/uuid_type/after.py` | 16 bytes, invalid values rejected, `DEFAULT UUID()` |
| `RETURNING` | `11_create_or_replace_returning.sql`, `12_flight_dataset.sql` | `python python/returning/after.py`<br>`python python/flight_returning/after.py` | Row back from `INSERT` / `DELETE` in one statement |
| `CREATE SEQUENCE` | `06_sequence.sql` | `python python/sequence/after.py` | One counter shared by two tables; the gap after a rolled-back `INSERT`; `SETVAL` |
| `INTERSECT` / `EXCEPT` | `05_intersect_except.sql` | `python python/intersect_except/after.py` | Set operations on real routes |
| `CREATE OR REPLACE` | `11_create_or_replace_returning.sql` | `python python/create_or_replace/after.py` | Re-runnable script; error 1451 under a foreign key |
| JSON check | `02_isjson_check.sql` | `python python/json_check/before.py`<br>`python python/json_check/after.py` | Python-side check that a second program skips; `CHECK (doc IS JSON)` refusing broken JSON (falls back to `JSON_VALID` before 12.3.1) |
| Invisible columns | `08_invisible_columns.sql` | `python python/invisible_columns/after.py` | `SELECT *` and column-less `INSERT` unchanged |
| `ROW` type | `09_row_type.sql` | `python python/row_type/after.py` | One variable for a whole row, `ROW TYPE OF` |
| Instant `ALTER` | `14_instant_alter.sql` | `python python/instant_alter/before.py`<br>`python python/instant_alter/after.py` | `COPY` rebuild time vs `INSTANT` (a few ms), error 1846 for a type change |
| Progress reporting | `13_progress_reporting.sql` | `python python/progress_reporting/after.py` | Process list watched from a second connection |
| Global temporary tables | `10_global_temp_tables.sql` | `python python/global_temp/after.py` | The real error 1064 (not available on 11.4 or 12.3) |
| `UPDATE` / `DELETE` from a CTE | `07_cte_update_delete.sql` | `python python/cte_update_delete/after.py` | `WITH ... UPDATE` / `WITH ... DELETE` on 12.3; on 11.4 error 1064 and the `JOIN` form |

Run a `before.py` the same way to see the old approach. Benchmark:
`python benchmark.py` from the repository root.
