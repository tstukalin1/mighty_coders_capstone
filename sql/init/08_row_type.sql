USE mighty_coders;

-- Feature: ROW data type and ROW TYPE OF (stored routines)
-- A ROW variable holds one whole row in a single variable, instead of one
-- DECLARE per column.

-- ------------------------------------------------------------
-- Example 1: ROW TYPE OF a table
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE employees (
    emp_id     INT PRIMARY KEY,
    emp_name   VARCHAR(100),
    salary     DECIMAL(10,2),
    department VARCHAR(50)
);

INSERT INTO employees VALUES
    (101, 'Rahul', 50000, 'QA'),
    (102, 'John', 60000, 'Development');

DROP PROCEDURE IF EXISTS get_employee;

DELIMITER //
CREATE PROCEDURE get_employee(IN p_id INT)
BEGIN
    DECLARE emp ROW TYPE OF employees;
    DECLARE found_record BOOLEAN DEFAULT TRUE;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET found_record = FALSE;

    SELECT * INTO emp FROM employees WHERE emp_id = p_id;

    IF found_record THEN
        SELECT emp.emp_id AS emp_id, emp.emp_name AS emp_name,
               emp.salary AS salary, emp.department AS department;
    ELSE
        SELECT 'Employee not found' AS message;
    END IF;
END //
DELIMITER ;

-- ------------------------------------------------------------
-- Example 2: ROW with explicit fields, on the flight dataset
-- (the airlines table is created later by flight_dataset.sql; a stored
-- routine only looks the table up when it is called)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS get_airline_row;

DELIMITER //
CREATE PROCEDURE get_airline_row(IN p_id INT)
BEGIN
    DECLARE rec ROW (
        id      INT,
        name    VARCHAR(200),
        country VARCHAR(100),
        active  VARCHAR(5)
    );
    DECLARE found_record BOOLEAN DEFAULT TRUE;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET found_record = FALSE;

    SELECT id, name, country, active
    INTO rec.id, rec.name, rec.country, rec.active
    FROM airlines
    WHERE id = p_id;

    IF found_record THEN
        SELECT rec.id AS id, rec.name AS name,
               rec.country AS country, rec.active AS active;
    ELSE
        SELECT 'Airline not found' AS message;
    END IF;
END //
DELIMITER ;

-- Usage:
--   CALL get_employee(101);
--   CALL get_employee(104);      -- returns 'Employee not found'
--   CALL get_airline_row(1);
