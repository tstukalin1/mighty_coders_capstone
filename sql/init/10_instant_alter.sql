USE mighty_coders;

-- Feature: instant ALTER TABLE (ADD / DROP COLUMN without rebuilding the table)
-- ALGORITHM=INSTANT only changes the table definition, so it takes the same
-- time on 10 rows and on 10 million rows. If MariaDB cannot do a change
-- instantly it raises an error instead of silently copying the table.
-- Needs the employees table from 08_row_type.sql.

-- IF NOT EXISTS makes the script safe to re-run.
ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS email VARCHAR(150),
    ADD COLUMN IF NOT EXISTS joining_date DATE,
    ALGORITHM=INSTANT;

UPDATE employees SET email = 'rahul@gmail.com', joining_date = '2024-01-15' WHERE emp_id = 101;
UPDATE employees SET email = 'john@gmail.com',  joining_date = '2023-06-20' WHERE emp_id = 102;

-- Limit: adding a column that already exists is an error.
--
-- ALTER TABLE employees ADD COLUMN email VARCHAR(150);
--
-- Actual error observed:
-- ERROR 1060 (42S21): Duplicate column name 'email'
--
-- (ADD COLUMN IF NOT EXISTS above is the way to avoid it.)

SELECT * FROM employees;
