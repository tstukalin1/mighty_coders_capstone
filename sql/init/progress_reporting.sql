USE mighty_coders;

-- Feature: progress reporting for a long ALTER TABLE
-- MariaDB reports STAGE, MAX_STAGE and PROGRESS (percent) for long statements
-- in SHOW FULL PROCESSLIST and information_schema.PROCESSLIST. They can only
-- be watched from a SECOND connection while the ALTER runs on the first one;
-- python/progress_reporting/after.py does exactly that.
--
-- This script runs after flight_dataset.sql (alphabetical order) and uses its
-- own demo table, built from the airlines names, so airlines itself is never
-- changed. The table is dropped again at the end.

-- 1. Demo table: the airline names repeated 50 times (about 300,000 rows)
CREATE OR REPLACE TABLE progress_demo (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200)
);

INSERT INTO progress_demo (name)
SELECT a.name FROM airlines a JOIN seq_1_to_50 s;

-- 2. Active operations (only this session is listed here)
SHOW FULL PROCESSLIST;

-- 3. Add an index without blocking reads and writes
ALTER TABLE progress_demo
    ADD INDEX IF NOT EXISTS idx_name (name),
    ALGORITHM=INPLACE,
    LOCK=NONE;

-- 4. Check table integrity
CHECK TABLE progress_demo;

-- 5. Active operations again
SHOW FULL PROCESSLIST;

-- Limit: adding an index that already exists is an error.
--
-- ALTER TABLE progress_demo ADD INDEX idx_name (name);
--
-- Actual error observed:
-- ERROR 1061 (42000): Duplicate key name 'idx_name'
--
-- (ADD INDEX IF NOT EXISTS above is the way to avoid it.)

-- 6. Clean up
DROP TABLE IF EXISTS progress_demo;
