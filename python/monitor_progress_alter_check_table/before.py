''' before changes: 
Average query time:NA
Execution plan: NA
Performance comparison: NA'''

import time
import threading
import mysql.connector
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

def monitor_process(stop_event):
    """Monitor the ALTER TABLE operation from a second connection."""
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

            rows = cursor.fetchall()

            for row in rows:
                print(
                    f"Process ID: {row['ID']} | "
                    f"Time: {row['TIME']}s | "
                    f"State: {row['STATE']} | "
                    f"Stage: {row['STAGE']}/{row['MAX_STAGE']} | "
                    f"Progress: {row['PROGRESS']:.2f}%"
                )

            stop_event.wait(0.2)

    finally:
        cursor.close()
        conn.close()


def run_alter_table():
    """Add the index if it does not already exist."""
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
            return

        print("Starting ALTER TABLE...")
        start = time.time()

        cursor.execute("""
            ALTER TABLE airlines_progress_demo
                ADD INDEX idx_name (airline_name),
                ALGORITHM=INPLACE,
                LOCK=NONE
        """)

        print(f"ALTER TABLE completed in {time.time() - start:.2f}s")

    finally:
        cursor.close()
        conn.close()


def run_check_table():
    """Run CHECK TABLE and print its results."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        print("\nRunning CHECK TABLE...")
        start = time.time()

        cursor.execute("CHECK TABLE airlines_progress_demo")
        results = cursor.fetchall()

        for row in results:
            print(row)

        print(f"CHECK TABLE completed in {time.time() - start:.2f}s")

        if not results or not any(row[3] == "OK" for row in results):
            raise RuntimeError("CHECK TABLE did not return OK")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    stop_event = threading.Event()

    monitor = threading.Thread(
        target=monitor_process,
        args=(stop_event,),
        daemon=True,
    )
    monitor.start()

    try:
        run_alter_table()
        run_check_table()
    finally:
        stop_event.set()
        monitor.join(timeout=2)

    print("\nProgress reporting experiment completed.")
