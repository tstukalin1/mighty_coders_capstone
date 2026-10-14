
USE airlines_db;

ALTER TABLE airlines_progress_demo
    ADD INDEX idx_name (airline_name),
    ALGORITHM=INPLACE,
    LOCK=NONE;

