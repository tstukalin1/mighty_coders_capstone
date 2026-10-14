''' before: Use normal SQL variables (DECLARE airline_name, DECLARE airline_country, etc.) to retrieve airline data'''


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
    """Create procedure using separate SQL variables."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DROP PROCEDURE IF EXISTS get_airline_before")

        sql = """
        CREATE PROCEDURE get_airline_before(IN p_id INT)
        BEGIN
            DECLARE v_airline_id INT;
            DECLARE v_name VARCHAR(150);
            DECLARE v_country VARCHAR(100);
            DECLARE v_active CHAR(1);

            DECLARE found_record BOOLEAN DEFAULT TRUE;

            DECLARE CONTINUE HANDLER FOR NOT FOUND
                SET found_record = FALSE;

            SELECT airline_id, name, country, active
            INTO v_airline_id, v_name, v_country, v_active
            FROM airlines
            WHERE airline_id = p_id;

            IF found_record THEN
                SELECT
                    v_airline_id AS airline_id,
                    v_name AS name,
                    v_country AS country,
                    v_active AS active;
            ELSE
                SELECT 'Airline not found' AS message;
            END IF;
        END
        """

        cursor.execute(sql)
        print("BEFORE procedure created successfully.")

    finally:
        cursor.close()
        conn.close()


def test_airline(airline_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "CALL get_airline_before(%s)",
            (airline_id,)
        )

        result = cursor.fetchone()

        while cursor.nextset():
            pass

        print(f"\nTesting airline ID: {airline_id}")
        print("Result:", result)

        if result and result.get("message") == "Airline not found":
            print("PASS: Negative scenario")

        elif result and result.get("airline_id") == airline_id:
            print("PASS: Positive scenario")

        else:
            raise AssertionError("Unexpected result")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("=== BEFORE: WITHOUT ROW TYPE ===")

    create_procedure()
    test_airline(2)
    test_airline(-999)

    print("\nBEFORE experiment completed.")
