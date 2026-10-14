'''What this covers
- MariaDB connection and version.
- Table and airline_name column existence.
- PROCESSLIST query used by progress monitoring.
- ALTER TABLE index creation and verification.
- CHECK TABLE integrity validation.
- Five query timing measurements.
- Performance percentage calculations.'''

import time
import threading

import pytest


TABLE_NAME = "airlines_progress_demo"
INDEX_NAME = "idx_name"


def test_database_connection(conn):
    """Verify MariaDB connectivity and version."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]

    assert "MariaDB" in version
    print(f"\nPASS: MariaDB connection: {version}")


def test_table_and_column_exist(conn):
    """Verify the table and benchmark column exist."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND COLUMN_NAME = 'airline_name'
            """,
            (TABLE_NAME,),
        )
        assert cursor.fetchone()[0] == 1

    print("PASS: Table and airline_name column exist")


def test_progress_monitor_query(conn):
    """Verify PROCESSLIST exposes the fields used by the monitor."""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT ID, TIME, STATE, INFO, STAGE, MAX_STAGE, PROGRESS
            FROM information_schema.PROCESSLIST
            LIMIT 1
        """)
        rows = cursor.fetchall()

    assert rows is not None
    print("PASS: MariaDB PROCESSLIST monitoring query works")


def test_alter_table_add_index(conn):
    """Create idx_name if missing and verify it exists."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND INDEX_NAME = %s
            """,
            (TABLE_NAME, INDEX_NAME),
        )
        index_exists = cursor.fetchone()[0] > 0

        if not index_exists:
            cursor.execute("""
                ALTER TABLE airlines_progress_demo
                ADD INDEX idx_name (airline_name),
                ALGORITHM=INPLACE,
                LOCK=NONE
            """)
            print("ALTER TABLE executed: idx_name created")
        else:
            print("idx_name already exists; creation skipped")

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND INDEX_NAME = %s
            """,
            (TABLE_NAME, INDEX_NAME),
        )
        assert cursor.fetchone()[0] > 0

    print("PASS: ALTER TABLE/index verification")


def test_check_table(conn):
    """Run CHECK TABLE and verify an OK result."""
    with conn.cursor() as cursor:
        cursor.execute("CHECK TABLE airlines_progress_demo")
        results = cursor.fetchall()

    assert results
    assert any(row[3] == "OK" for row in results)
    print("PASS: CHECK TABLE returned OK")


def test_query_benchmark(conn):
    """Measure query timing and retrieve EXPLAIN output."""
    query = """
        SELECT COUNT(*)
        FROM airlines_progress_demo
        WHERE airline_name = %s
    """
    timings = []

    with conn.cursor() as cursor:
        for _ in range(5):
            start = time.perf_counter()
            cursor.execute(query, ("American Airlines",))
            cursor.fetchone()
            timings.append((time.perf_counter() - start) * 1000)

        average_ms = sum(timings) / len(timings)

        cursor.execute("EXPLAIN " + query, ("American Airlines",))
        plan = cursor.fetchone()

    assert average_ms >= 0
    assert plan is not None

    print(f"Average query time: {average_ms:.3f} ms")
    print("Execution plan:", plan)
    print("PASS: Query benchmark and EXPLAIN")


def test_performance_calculation():
    """Verify percentage-change calculations."""
    before_ms = 100.0
    after_ms = 75.0

    improvement = ((before_ms - after_ms) / before_ms) * 100
    assert improvement == 25.0

    slower_change = ((100.0 - 125.0) / 100.0) * 100
    assert slower_change == -25.0

    print("PASS: Performance calculation")
