'''What is covered
1. Database connection — verifies MariaDB is accessible.
2. Table existence — confirms the airlines table exists.
3. Stored procedure existence — checks that get_airline_row was created.
4. Positive scenario — verifies a real airline returns all four expected fields.
5. Negative scenario — verifies a nonexistent ID returns Airline not found.
6. Multiple records — tests the procedure with up to three existing airline IDs.'''

import pytest


PROCEDURE_NAME = "get_airline_row"
TABLE_NAME = "airlines"


def test_database_connection(conn):
    """Verify MariaDB connection and version."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]

    assert "MariaDB" in version
    print(f"PASS: MariaDB version: {version}")


def test_airlines_table_exists(conn):
    """Verify the airlines table exists."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
            """,
            (TABLE_NAME,),
        )

        assert cursor.fetchone()[0] == 1

    print("PASS: Airlines table exists")


def test_row_procedure_exists(conn):
    """Verify the ROW stored procedure exists."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.ROUTINES
            WHERE ROUTINE_SCHEMA = DATABASE()
              AND ROUTINE_NAME = %s
              AND ROUTINE_TYPE = 'PROCEDURE'
            """,
            (PROCEDURE_NAME,),
        )

        assert cursor.fetchone()[0] == 1

    print("PASS: ROW stored procedure exists")


def test_positive_scenario(conn):
    """Verify an existing airline returns all expected fields."""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT airline_id FROM airlines ORDER BY airline_id LIMIT 1"
        )
        row = cursor.fetchone()

        assert row is not None, "No airline records available"
        airline_id = row[0]

        cursor.callproc(PROCEDURE_NAME, (airline_id,))

        result = None
        for result_set in cursor.stored_results():
            result = result_set.fetchone()
            result_set.close()

    assert result is not None
    assert result["airline_id"] == airline_id
    assert "name" in result
    assert "country" in result
    assert "active" in result

    print(f"PASS: Positive scenario for airline ID {airline_id}")


def test_negative_scenario(conn):
    """Verify a nonexistent airline returns the expected message."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT COALESCE(MAX(airline_id), 0) + 1 FROM airlines")
        missing_id = cursor.fetchone()[0]

        cursor.callproc(PROCEDURE_NAME, (missing_id,))

        result = None
        for result_set in cursor.stored_results():
            result = result_set.fetchone()
            result_set.close()

    assert result is not None
    assert result["message"] == "Airline not found"

    print(f"PASS: Negative scenario for airline ID {missing_id}")


def test_multiple_existing_airlines(conn):
    """Verify the procedure works for multiple existing airline IDs."""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT airline_id FROM airlines ORDER BY airline_id LIMIT 3"
        )
        airline_ids = [row[0] for row in cursor.fetchall()]

        assert airline_ids, "No airline records available"

        for airline_id in airline_ids:
            cursor.callproc(PROCEDURE_NAME, (airline_id,))

            result = None
            for result_set in cursor.stored_results():
                result = result_set.fetchone()
                result_set.close()

            assert result is not None
            assert result["airline_id"] == airline_id

    print(f"PASS: Multiple airline IDs tested: {airline_ids}")
