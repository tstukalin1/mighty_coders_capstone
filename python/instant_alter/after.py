"""
after.py -- ADD COLUMN / DROP COLUMN with ALGORITHM=INSTANT

Only the table definition changes, so the time does not depend on the number
of rows. If a change cannot be done instantly MariaDB raises an error instead
of copying the table.

Run after the database is up:  python python/instant_alter/after.py
"""

import os
import sys
import time

import pymysql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

ROWS = 300_000


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS demo_alter_instant")
            cur.execute("CREATE TABLE demo_alter_instant ("
                        " id INT AUTO_INCREMENT PRIMARY KEY, payload VARCHAR(100))")
            cur.execute("INSERT INTO demo_alter_instant (payload)"
                        f" SELECT REPEAT('x', 80) FROM seq_1_to_{ROWS}")
            conn.commit()

            start = time.time()
            cur.execute("ALTER TABLE demo_alter_instant ADD COLUMN note VARCHAR(50), ALGORITHM=INSTANT")
            add_time = time.time() - start

            start = time.time()
            cur.execute("ALTER TABLE demo_alter_instant DROP COLUMN note, ALGORITHM=INSTANT")
            drop_time = time.time() - start

            print("[after.py] ADD / DROP COLUMN with ALGORITHM=INSTANT")
            print(f"  rows in table : {ROWS:,}")
            print(f"  ADD COLUMN    : {add_time:.3f} s")
            print(f"  DROP COLUMN   : {drop_time:.3f} s")

            # limit: changing a column type cannot be instant
            try:
                cur.execute("ALTER TABLE demo_alter_instant MODIFY payload INT, ALGORITHM=INSTANT")
                print("  MODIFY with INSTANT worked (unexpected)")
            except pymysql.err.MySQLError as exc:
                print(f"  Limit: MODIFY payload VARCHAR(100)->INT is not instant: {exc.args}")

            cur.execute("DROP TABLE IF EXISTS demo_alter_instant")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()