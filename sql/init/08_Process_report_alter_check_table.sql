USE mighty_coders;

-- 1. View active database operations
SHOW FULL PROCESSLIST;

-- 2. Add an index to the demo table
ALTER TABLE airlines
    ADD INDEX idx_name (airline_name),
    ALGORITHM=INPLACE,
    LOCK=NONE;

-- 3. Check table integrity
CHECK TABLE airlines;

-- 4. View active database operations again
SHOW FULL PROCESSLIST;
