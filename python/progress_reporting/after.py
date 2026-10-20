"""
after.py -- the same ALTER TABLE, watched from a second connection

MariaDB reports STAGE, MAX_STAGE and PROGRESS (percent) for long statements in
information_schema.PROCESSLIST. A second connection reads them while the ALTER
runs on the first one. The lookup time is measured before and after the index.

Dataset: the airline names from the airlines table, repeated 50 times in a demo
table (progress_demo_new). The demo table is dropped at the end, so the script
can be run again at any time.

Run after the database is up:  python python/progress_reporting/after.py
"""

import os
import sys
import threading
import time

import pymysql.cursors

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

TABLE = "progress_demo_new"
SEARCH_VALUE = "American Airlines"
RUNS = 5


def monitor(stop_event, samples):
    """Second connection: print the progress of the ALTER while it runs."""
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            while not stop_event.is_set():
                cur.execute(
                    "SELECT ID, TIME, STATE, STAGE, MAX_STAGE, PROGRESS"
                    " FROM information_schema.PROCESSLIST"
                    " WHERE ID <> CONNECTION_ID() AND INFO LIKE %s",
                    (f"ALTER TABLE {TABLE}%",),
                )
                for row in cur.fetchall():
                    samples.append(row)
                    print(f"  monitor: stage {row['STAGE']}/{row['MAX_STAGE']}"
                          f" | progress {row['PROGRESS'] or 0:.2f}%"
                          f" | state {row['STATE']}")
                stop_event.wait(0.1)
    finally:
        conn.close()


def timed_lookup(cur):
    times = []
    for _ in range(RUNS):
        start = time.perf_counter()
        cur.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE name = %s", (SEARCH_VALUE,))
        cur.fetchone()
        times.append((time.perf_counter() - start) * 1000)
    return sum(times) / len(times)


def access_type(cur):
    cur.execute(f"EXPLAIN SELECT COUNT(*) FROM {TABLE} WHERE name = %s", (SEARCH_VALUE,))
    return cur.fetchone()[3]


def main():
    conn = get_connection()
    stop_event = threading.Event()
    samples = []
    watcher = threading.Thread(target=monitor, args=(stop_event, samples), daemon=True)
    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {TABLE}")
            cur.execute(f"CREATE TABLE {TABLE} ("
                        " id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(200))")
            cur.execute(f"INSERT INTO {TABLE} (name)"
                        " SELECT a.name FROM airlines a JOIN seq_1_to_50 s")
            cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
            rows = cur.fetchone()[0]

            print("[after.py] ALTER TABLE with progress reporting")
            print(f"  rows in table        : {rows:,}")
            before_ms = timed_lookup(cur)
            print(f"  lookup, no index     : {before_ms:.3f} ms, access type {access_type(cur)}")

            watcher.start()
            start = time.perf_counter()
            cur.execute(f"ALTER TABLE {TABLE} ADD INDEX idx_name (name),"
                        " ALGORITHM=INPLACE, LOCK=NONE")
            elapsed = time.perf_counter() - start
            stop_event.set()
            watcher.join(timeout=2)

            print(f"  ALTER TABLE finished : {elapsed:.2f} s")
            print(f"  progress samples seen: {len(samples)}")
            if not samples:
                print("  (the ALTER finished between two samples; use a bigger table to see more)")

            after_ms = timed_lookup(cur)
            print(f"  lookup, with index   : {after_ms:.3f} ms, access type {access_type(cur)}")
            if before_ms > 0:
                print(f"  lookup time change   : {(before_ms - after_ms) / before_ms * 100:.1f}% faster")

            cur.execute(f"CHECK TABLE {TABLE}")
            print(f"  CHECK TABLE          : {cur.fetchall()[-1][3]}")

            cur.execute(f"DROP TABLE IF EXISTS {TABLE}")
    finally:
        stop_event.set()
        conn.close()


if __name__ == "__main__":
    main()
