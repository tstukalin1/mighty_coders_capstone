USE mighty_coders;

-- Feature: instant ADD / DROP / MODIFY COLUMN
-- ALGORITHM=INSTANT changes only the table definition, so it takes the same
-- time on 6,000 rows and on 6 million. ALGORITHM=COPY rebuilds the whole table,
-- so its time grows with the number of rows (the "maintenance window").
-- If a change cannot be done instantly, MariaDB raises an error instead of
-- silently copying the table: writing ALGORITHM=INSTANT is a guarantee.
--
-- Uses its own demo table built from airlines (12_flight_dataset.sql), so
-- airlines itself is never changed. python/instant_alter/ times both ways on
-- 300,000 rows; benchmark.py measures them with repeated rounds.

CREATE OR REPLACE TABLE instant_demo (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    name    VARCHAR(200),
    country VARCHAR(100)
);

INSERT INTO instant_demo (name, country)
SELECT name, country FROM airlines;

-- OLD WAY: the table is copied row by row (time grows with the table)
ALTER TABLE instant_demo ADD COLUMN note_copy VARCHAR(50), ALGORITHM=COPY;

-- NEW WAY: only the definition changes (same time for any table size)
ALTER TABLE instant_demo ADD COLUMN note VARCHAR(50), ALGORITHM=INSTANT;
ALTER TABLE instant_demo DROP COLUMN note_copy, ALGORITHM=INSTANT;

-- MODIFY can be instant too, for example making a VARCHAR longer
ALTER TABLE instant_demo MODIFY name VARCHAR(300), ALGORITHM=INSTANT;

-- Limit: changing the type of a column cannot be instant.
--
-- ALTER TABLE instant_demo MODIFY country INT, ALGORITHM=INSTANT;
--
-- Actual error observed:
-- ERROR 1846 (0A000): ALGORITHM=INSTANT is not supported. Reason: Cannot change
-- column type. Try ALGORITHM=COPY
--
-- (Without ALGORITHM=..., MariaDB would quietly fall back to a full copy.)

SHOW COLUMNS FROM instant_demo;

DROP TABLE IF EXISTS instant_demo;
