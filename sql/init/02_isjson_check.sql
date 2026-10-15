-- Feature: JSON CHECK constraint via JSON_VALID() (MariaDB 10.4+)
-- CHECK (JSON_VALID(metadata)) rejects any INSERT or UPDATE
-- where the value is not a valid JSON document.

CREATE TABLE IF NOT EXISTS products (
    id       INT          AUTO_INCREMENT PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    metadata JSON         NOT NULL,
    CONSTRAINT chk_metadata_is_json CHECK (JSON_VALID(metadata))
);
