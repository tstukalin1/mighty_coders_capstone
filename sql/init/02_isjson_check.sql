-- Feature: JSON CHECK constraint via JSON_VALID() (MariaDB 10.4+)
-- This init script must also run on 11.4 (CI tests both versions), so it uses JSON_VALID.
-- The SQL-standard CHECK (doc IS JSON) needs 12.3.1: see python/json_check/after.py.
-- CHECK (JSON_VALID(metadata)) rejects any INSERT or UPDATE
-- where the value is not a valid JSON document.

CREATE TABLE IF NOT EXISTS products (
    id       INT          AUTO_INCREMENT PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    metadata JSON         NOT NULL,
    CONSTRAINT chk_metadata_json_valid CHECK (JSON_VALID(metadata))
);
