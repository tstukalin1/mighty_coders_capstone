''' after changes: 
Average query time:mentioned
Execution plan: displayed
Performance comparison: added'''

import time
import threading
import mysql.connector
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

TABLE_NAME = "airlines"
INDEX_NAME = "idx_name"
SEARCH_VALUE = "American Airlines"
BENCHMARK_RUNS = 5
an Airlines"
BENCHMARK_RUNS = 5


def get_connection():
    """Create a new MariaDB connection."""
    return mysql.connector.connect(**DB_CONFIG)


def monitor_process(stop_event):
    """Monitor ALTER TABLE and CHECK TABLE operations."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        print("Monitoring MariaDB processes...")

        while not stop_event.is_set():
            cursor.execute("""
                SELECT ID, TIME, STATE, INFO, STAGE,
                       MAX_STAGE, PROGRESS
                FROM information_schema.PROCESSLIST
                WHERE ID <> CONNECTION_ID()
                  AND INFO IS NOT NULL
                  AND (
                    INFO LIKE 'ALTER TABLE airlines%'
                    OR INFO LIKE 'CHECK TABLE airlines%'
                  )
            """)

            for row in cursor.fetchall():
                progress = row["PROGRESS"] or 0
                print(
                    f"Process ID: {row['ID']} | "
                    f"Time: {row['TIME']}s | "
                    f"State: {row['STATE']} | "
                    f"Stage: {row['STAGE']}/{row['MAX_STAGE']} | "
                    f"Progress: {progress:.2f}%"
                )

            stop_event.wait(0.2)

    finally:
        cursor.close()
        conn.close()


def benchmark_query(label):
    """Measure query time and display EXPLAIN output."""
    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
        SELECT COUNT(*)
        FROM `{TABLE_NAME}`
        WHERE name = %s
    """

    try:
        print(f"\n=== {label} ===")
        timings = []

        for run in range(BENCHMARK_RUNS):
            start = time.perf_counter()
            cursor.execute(query, (SEARCH_VALUE,))
            result = cursor.fetchone()
            elapsed_ms = (time.perf_counter() - start) * 1000
            timings.append(elapsed_ms)

            print(
                f"Run {run + 1}: {elapsed_ms:.3f} ms "
                f"| Matching rows: {result[0]}"
            )

        average_ms = sum(timings) / len(timings)
        print(f"Average query time: {average_ms:.3f} ms")

        cursor.execute("EXPLAIN " + query, (SEARCH_VALUE,))
        columns = [item[0] for item in cursor.description]
        print("Execution plan:", dict(zip(columns, cursor.fetchone())))

        return average_ms

    finally:
        cursor.close()
        conn.close()


def run_alter_table():
    """Create the index if it does not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND INDEX_NAME = %s
        """, (TABLE_NAME, INDEX_NAME))

        if cursor.fetchone()[0]:
            print(f"Index {INDEX_NAME} already exists; skipping ALTER TABLE.")
            return False

        print("\nStarting ALTER TABLE...")
        start = time.perf_counter()

        cursor.execute("""
            ALTER TABLE airlines
            ADD INDEX idx_name (name),
            ALGORITHM=INPLACE,
            LOCK=NONE
        """)

        print(f"ALTER TABLE completed in {time.perf_counter() - start:.2f}s")
        return True

    finally:
        cursor.close()
        conn.close()


def run_check_table():
    """Check table integrity."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("\nRunning CHECK TABLE...")
        start = time.perf_counter()

        cursor.execute("CHECK TABLE airlines")
        results = cursor.fetchall()

        for row in results:
            print(row)

        print(f"CHECK TABLE completed in {time.perf_counter() - start:.2f}s")

        if not results or not any(row[3] == "OK" for row in results):
            raise RuntimeError("CHECK TABLE did not return OK")

    finally:
        cursor.close()
        conn.close()


def main():
    stop_event = threading.Event()

    monitor = threading.Thread(
        target=monitor_process,
        args=(stop_event,),
        daemon=True,
    )
    monitor.start()

    try:
        before_ms = benchmark_query("BEFORE INDEX CREATION")
        index_created = run_alter_table()
        after_ms = benchmark_query("AFTER INDEX CREATION")

        print("\n=== PERFORMANCE COMPARISON ===")
        print(f"Before average: {before_ms:.3f} ms")
        print(f"After average:  {after_ms:.3f} ms")

        if before_ms > 0:
            change = ((before_ms - after_ms) / before_ms) * 100
            print(f"Query time reduction: {change:.2f}%")

            if change > 0:
                print("Result: Query execution became faster.")
            elif change < 0:
                print("Result: Query execution became slower.")
            else:
                print("Result: No measurable change.")

        if not index_created:
            print("Note: Index already existed; no new index was created.")

        run_check_table()

    finally:
        stop_event.set()
        monitor.join(timeout=2)

    print("\nEnhanced progress reporting experiment completed.")


if __name__ == "__main__":
    main()

