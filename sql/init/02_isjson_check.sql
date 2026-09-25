-- Feature: IS JSON CHECK constraint (MariaDB 10.6+)
-- CHECK (metadata IS JSON) rejects any INSERT or UPDATE
-- where the value is not a valid JSON document.

CREATE TABLE IF NOT EXISTS products (
    id       INT          AUTO_INCREMENT PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    metadata JSON         NOT NULL,
    CONSTRAINT chk_metadata_is_json CHECK (metadata IS JSON)
);
