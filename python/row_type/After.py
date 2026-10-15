'''AFTER: Use MariaDB's ROW data type to group the airline fields into one record, with additional positive and negative test cases'''

import time
import threading
import mysql.connector
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db import get_connection

def get_connection():
    """Create a new MariaDB connection."""
    return mysql.connector.connect(**DB_CONFIG)


def create_procedure():
    """Create procedure using MariaDB ROW data type."""
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
        print("ROW stored procedure created successfully.")

    finally:
        cursor.close()
        conn.close()


def test_airline(airline_id, should_exist):
    """Validate positive and negative scenarios."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        start = time.perf_counter()

        cursor.execute("CALL get_airline_row(%s)", (airline_id,))
        result = cursor.fetchone()

        while cursor.nextset():
            pass

        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"\nAirline ID: {airline_id}")
        print("Result:", result)
        print(f"Execution time: {elapsed_ms:.3f} ms")

        if should_exist:
            assert result is not None
            assert result.get("airline_id") == airline_id
            assert "name" in result
            assert "country" in result
            assert "active" in result

            print("PASS: Positive scenario")
        else:
            assert result is not None
            assert result.get("message") == "Airline not found"

            print("PASS: Negative scenario")

        return True

    except AssertionError:
        print("FAIL: Validation failed")
        return False

    finally:
        cursor.close()
        conn.close()


def get_existing_ids(limit=3):
    """Select real airline IDs for positive testing."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT airline_id
            FROM airlines
            ORDER BY airline_id
            LIMIT %s
            """,
            (limit,),
        )
        return [row[0] for row in cursor.fetchall()]

    finally:
        cursor.close()
        conn.close()


def main():
    print("=== AFTER: WITH ROW TYPE ===")

    create_procedure()

    existing_ids = get_existing_ids()

    if not existing_ids:
        raise RuntimeError(
            "No airline records found in the airlines table."
        )

    tests = [(airline_id, True) for airline_id in existing_ids]

    # Find a missing ID for the negative test.
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT MAX(airline_id) FROM airlines")
        maximum_id = cursor.fetchone()[0]
        missing_id = (maximum_id or 0) + 1
    finally:
        cursor.close()
        conn.close()

    tests.append((missing_id, False))

    passed = 0

    for airline_id, should_exist in tests:
        if test_airline(airline_id, should_exist):
            passed += 1

    failed = len(tests) - passed

    print("\n=== TEST SUMMARY ===")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed:
        raise AssertionError("Some tests failed.")

    print("\nROW Type experiment completed successfully.")


if __name__ == "__main__":
    main()
