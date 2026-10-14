
USE mighty_coders;

DROP PROCEDURE IF EXISTS get_airline_row;

DELIMITER //

CREATE PROCEDURE get_airline_row(IN p_id INT)
BEGIN
    DECLARE rec ROW (
        airline_id INT,
        name VARCHAR(150),
        country VARCHAR(100),
        active CHAR(1)
    );

    DECLARE found_record BOOLEAN DEFAULT TRUE;

    DECLARE CONTINUE HANDLER FOR NOT FOUND
        SET found_record = FALSE;

    SELECT airline_id, name, country, active
    INTO rec.airline_id, rec.name, rec.country, rec.active
    FROM airlines
    WHERE airline_id = p_id;

    IF found_record THEN
        SELECT
            rec.airline_id AS airline_id,
            rec.name AS name,
            rec.country AS country,
            rec.active AS active;
    ELSE
        SELECT 'Airline not found' AS message;
    END IF;
END //

DELIMITER ;
