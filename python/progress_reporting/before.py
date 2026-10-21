"""
before.py -- a long ALTER TABLE with no way to see how far it has got

The old way: start ALTER TABLE ... ADD INDEX and wait. Nothing tells you
whether it is 10% or 90% done. The lookup that needs the index is also slow,
because without it MariaDB reads every row.

Dataset: the airline names from the airlines table, repeated 50 times in a demo
table (progress_demo_old). The demo table is dropped at the end, so the script
can be run again at any time.

Run after the database is up:  python python/progress_reporting/before.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

TABLE = "progress_demo_old"
SEARCH_VALUE = "American Airlines"
RUNS = 5


def timed_lookup(cur):
    times = []
    for _ in range(RUNS):
        start = time.perf_counter()
        cur.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE name = %s", (SEARCH_VALUE,))
        cur.fetchone()
        times.append((time.perf_counter() - start) * 1000)
    return sum(times) / len(times)


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {TABLE}")
            cur.execute(f"CREATE TABLE {TABLE} ("
                        " id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(200))")
            cur.execute(f"INSERT INTO {TABLE} (name)"
                        " SELECT a.name FROM airlines a JOIN seq_1_to_50 s")
            cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
            rows = cur.fetchone()[0]

            print("[before.py] ALTER TABLE without progress reporting")
            print(f"  rows in table        : {rows:,}")
            print(f"  lookup, no index     : {timed_lookup(cur):.3f} ms (average of {RUNS})")

            cur.execute(f"EXPLAIN SELECT COUNT(*) FROM {TABLE} WHERE name = %s", (SEARCH_VALUE,))
            print(f"  access type          : {cur.fetchone()[3]}  (ALL = reads every row)")

            start = time.perf_counter()
            cur.execute(f"ALTER TABLE {TABLE} ADD INDEX idx_name (name),"
                        " ALGORITHM=INPLACE, LOCK=NONE")
            print(f"  ALTER TABLE finished : {time.perf_counter() - start:.2f} s")
            print("  progress during ALTER: none visible, you can only wait")

            cur.execute(f"DROP TABLE IF EXISTS {TABLE}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
