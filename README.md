# mighty_coders
Capstone Project 1 for Constructor University

**Authors:** Yosef Gebrewahid Kidane, Timofey Stukalin, Dinu Panackal Devassia

---

## Project Goal

Demonstrate a set of modern MariaDB SQL features that remove work you would otherwise do in application code. The project builds real, runnable examples showing what life looks like **with** and **without** each feature — the extra round trip, the column that sorts wrong, the migration that needs a maintenance window.

### Features covered

- **INET4 / INET6** — native IP address types (4 and 16 bytes instead of a string)
- **UUID** — a real UUID type, not `CHAR(36)` or hand-encoded `BINARY(16)`
- **RETURNING** — `INSERT`, `UPDATE`, `DELETE` hand back the rows they touched
- **CREATE SEQUENCE** — sequences as first-class objects, independent of `AUTO_INCREMENT`
- **INTERSECT and EXCEPT** — set operations alongside `UNION`
- **CREATE OR REPLACE** — idempotent DDL that makes migration scripts cleaner
- **IS JSON** — SQL-standard predicate usable inside a `CHECK` constraint
- **Invisible columns** — columns absent from `SELECT *` and unkeyed `INSERT`, but accessible by name
- **ROW type** — composite variables in stored routines
- **Instant ADD / DROP / MODIFY COLUMN** — schema changes that complete immediately on large tables
- **Progress reporting** — long `ALTER TABLE` and `CHECK TABLE` report progress
- **Global temporary tables** — one shared definition, contents private per session
- **UPDATE / DELETE with CTEs** — a `WITH` clause feeding the statement that changes data

### Evaluation criteria

1. At least two features used where they genuinely belong (depth)
2. Side-by-side before/after comparison — the extra round trip, the string column that sorts wrong, the migration full of `DROP TABLE IF EXISTS` (depth)
3. Measured difference where possible — queries saved, bytes saved, migration time (execution)
4. Runnable examples a reader can paste into their own schema (usability)
5. Clear guidance on when each feature is worth reaching for, and when it is not (documentation)

---

## Tech stack

- **Database:** MariaDB
- **Application code:** Python
