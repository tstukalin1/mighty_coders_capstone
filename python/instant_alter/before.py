"""
before.py -- ADD COLUMN that rebuilds the whole table (ALGORITHM=COPY)

The old way: MariaDB creates a new copy of the table, copies every row into
it, and swaps. The time grows with the number of rows.

Run after the database is up:  python python/instant_alter/before.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

ROWS = 300_000


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS demo_alter_copy")
            cur.execute("CREATE TABLE demo_alter_copy ("
                        " id INT AUTO_INCREMENT PRIMARY KEY, payload VARCHAR(100))")
            cur.execute("INSERT INTO demo_alter_copy (payload)"
                        f" SELECT REPEAT('x', 80) FROM seq_1_to_{ROWS}")
            conn.commit()

            start = time.time()
            cur.execute("ALTER TABLE demo_alter_copy ADD COLUMN note VARCHAR(50), ALGORITHM=COPY")
            elapsed = time.time() - start

            print("[before.py] ADD COLUMN with ALGORITHM=COPY (table rebuilt)")
            print(f"  rows in table : {ROWS:,}")
            print(f"  time taken    : {elapsed:.3f} s")

            cur.execute("DROP TABLE IF EXISTS demo_alter_copy")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
