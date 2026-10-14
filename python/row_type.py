
import mysql.connector

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "1234",
    "database": "mighty_coders",
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def create_procedure():
    """Create the MariaDB ROW-type stored procedure."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DROP PROCEDURE IF EXISTS get_airline_row")

        sql = """
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
        END
        """

        cursor.execute(sql)
        print("Stored procedure created successfully.")

    finally:
        cursor.close()
        conn.close()


def test_airline(airline_id):
    """Call the procedure and validate its result."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("CALL get_airline_row(%s)", (airline_id,))
        result = cursor.fetchone()

        while cursor.nextset():
            pass

        print(f"\nTesting airline ID: {airline_id}")
        print("Result:", result)

        if result and result.get("message") == "Airline not found":
            assert airline_id == -999
            print("PASS: Negative scenario")

        elif result and result.get("airline_id") == airline_id:
            assert "name" in result
            assert "country" in result
            assert "active" in result
            print("PASS: Positive scenario")

        else:
            raise AssertionError(f"Unexpected result: {result}")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    create_procedure()
    test_airline(2)
    test_airline(-999)
