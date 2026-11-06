"""
before.py -- adding a column the old way: the whole table is copied

ALTER TABLE ... ALGORITHM=COPY writes every row into a new copy of the table.
The time grows with the number of rows, which is why such a migration used to
need a maintenance window.

Dataset: the airlines table repeated 50 times in a demo table (about 300,000
rows). airlines itself is not changed, and the demo table is dropped at the end.

Run after the database is up:  python python/instant_alter/before.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS instant_demo_old")
            cur.execute("CREATE TABLE instant_demo_old ("
                        " id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(200), country VARCHAR(100))")
            cur.execute("INSERT INTO instant_demo_old (name, country)"
                        " SELECT a.name, a.country FROM airlines a JOIN seq_1_to_50 s")
            cur.execute("SELECT COUNT(*) FROM instant_demo_old")
            rows = cur.fetchone()[0]

            start = time.perf_counter()
            cur.execute("ALTER TABLE instant_demo_old ADD COLUMN note VARCHAR(50), ALGORITHM=COPY")
            seconds = time.perf_counter() - start

            print("[before.py] ADD COLUMN with ALGORITHM=COPY (the table is rebuilt)")
            print(f"  rows in table : {rows:,}")
            print(f"  ADD COLUMN    : {seconds * 1000:.1f} ms")

            cur.execute("DROP TABLE IF EXISTS instant_demo_old")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
