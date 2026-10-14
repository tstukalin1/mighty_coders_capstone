''' after changes: 
Average query time:mentioned
Execution plan: displayed
Performance comparison: added'''

import time
import threading
import mysql.connector
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db import get_connection

def monitor_process(stop_event):
    """Monitor ALTER TABLE and CHECK TABLE operations."""
    conn = mysql.connector.connect(**DB_CONFIG)
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
                    INFO LIKE 'ALTER TABLE airlines_progress_demo%'
                    OR INFO LIKE 'CHECK TABLE airlines_progress_demo%'
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
    """Measure query execution time and display EXPLAIN output."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    query = f"""
        SELECT COUNT(*)
        FROM {TABLE_NAME}
        WHERE airline_name = %s
    """

    try:
        print(f"\n=== {label} ===")
        timings = []

        for run in range(BENCHMARK_RUNS):
            start = time.perf_counter()

            cursor.execute(query, (SEARCH_VALUE,))
            result = cursor.fetchone()

            elapsed = time.perf_counter() - start
            timings.append(elapsed * 1000)

            print(
                f"Run {run + 1}: {elapsed * 1000:.3f} ms "
                f"| Matching rows: {result[0]}"
            )

        average_ms = sum(timings) / len(timings)
        print(f"Average query time: {average_ms:.3f} ms")

        cursor.execute("EXPLAIN " + query, (SEARCH_VALUE,))
        columns = [item[0] for item in cursor.description]
        plan = cursor.fetchone()

        print("\nExecution plan:")
        print(dict(zip(columns, plan)))

        return average_ms

    finally:
        cursor.close()
        conn.close()


def run_alter_table():
    """Create the index if it does not exist."""
    conn = mysql.connector.connect(**DB_CONFIG)
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
            ALTER TABLE airlines_progress_demo
            ADD INDEX idx_name (airline_name),
            ALGORITHM=INPLACE,
            LOCK=NONE
        """)

        print(
            f"ALTER TABLE completed in "
            f"{time.perf_counter() - start:.2f}s"
        )
        return True

    finally:
        cursor.close()
        conn.close()


def run_check_table():
    """Check table integrity."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        print("\nRunning CHECK TABLE...")
        start = time.perf_counter()

        cursor.execute("CHECK TABLE airlines_progress_demo")
        results = cursor.fetchall()

        for row in results:
            print(row)

        print(
            f"CHECK TABLE completed in "
            f"{time.perf_counter() - start:.2f}s"
        )

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
        # Benchmark the table before attempting the ALTER.
        before_ms = benchmark_query("BEFORE INDEX CREATION")

        # Create the index, if required.
        index_created = run_alter_table()

        # Benchmark again after the ALTER attempt.
        after_ms = benchmark_query("AFTER INDEX CREATION")

        print("\n=== PERFORMANCE COMPARISON ===")
        print(f"Before average: {before_ms:.3f} ms")
        print(f"After average:  {after_ms:.3f} ms")

        if before_ms > 0:
            improvement = ((before_ms - after_ms) / before_ms) * 100
            print(f"Change in query time: {improvement:.2f}%")

            if improvement > 0:
                print("Result: Query execution became faster.")
            elif improvement < 0:
                print("Result: Query execution became slower.")
            else:
                print("Result: No measurable change.")

        if not index_created:
            print(
                "\nNote: The index already existed. "
                "This is not a clean first-time before/after test."
            )

        run_check_table()

    finally:
        stop_event.set()
        monitor.join(timeout=2)

    print("\nEnhanced progress reporting experiment completed.")


if __name__ == "__main__":
    main()
