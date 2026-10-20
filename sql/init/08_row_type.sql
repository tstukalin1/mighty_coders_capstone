USE mighty_coders;

-- Feature: ROW data type (stored routines)
-- A ROW variable holds one whole row in a single variable, instead of one
-- DECLARE and one INTO target per column.
--
-- Dataset: the airlines table from flight_dataset.sql. That script runs later
-- (init scripts run in alphabetical order); this is fine because a stored
-- routine only looks its table up when it is called.

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

    DECLARE CONTINUE HANDLER FOR NOT FOUND
        SET found_record = FALSE;

    SELECT id, name, country, active
    INTO rec.id, rec.name, rec.country, rec.active
    FROM airlines
    WHERE id = p_id;

    IF found_record THEN
        SELECT
            rec.id      AS id,
            rec.name    AS name,
            rec.country AS country,
            rec.active  AS active;
    ELSE
        SELECT 'Airline not found' AS message;
    END IF;
END //

DELIMITER ;

-- Usage (after flight_dataset.sql has loaded the airlines):
--   CALL get_airline_row(2);        -- 135 Airways, United States, N
--   CALL get_airline_row(999999);   -- Airline not found
