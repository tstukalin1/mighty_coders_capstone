"""
after.py -- ADD / DROP / MODIFY COLUMN with ALGORITHM=INSTANT

Only the table definition changes, so the time does not depend on the number
of rows. Writing ALGORITHM=INSTANT is also a guarantee: if a change cannot be
done instantly, MariaDB raises an error instead of quietly copying the table.

Dataset: the same 300,000-row demo table as before.py, dropped at the end.

Run after the database is up:  python python/instant_alter/after.py
"""

import os
import sys
import time

import pymysql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

STEPS = [
    ("ADD COLUMN", "ALTER TABLE instant_demo_new ADD COLUMN note VARCHAR(50), ALGORITHM=INSTANT"),
    ("DROP COLUMN", "ALTER TABLE instant_demo_new DROP COLUMN note, ALGORITHM=INSTANT"),
    ("MODIFY (longer VARCHAR)",
     "ALTER TABLE instant_demo_new MODIFY name VARCHAR(300), ALGORITHM=INSTANT"),
]


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS instant_demo_new")
            cur.execute("CREATE TABLE instant_demo_new ("
                        " id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(200), country VARCHAR(100))")
            cur.execute("INSERT INTO instant_demo_new (name, country)"
                        " SELECT a.name, a.country FROM airlines a JOIN seq_1_to_50 s")
            cur.execute("SELECT COUNT(*) FROM instant_demo_new")
            rows = cur.fetchone()[0]

            print("[after.py] Schema changes with ALGORITHM=INSTANT")
            print(f"  rows in table : {rows:,}")
            for label, sql in STEPS:
                start = time.perf_counter()
                cur.execute(sql)
                print(f"  {label:<24}: {(time.perf_counter() - start) * 1000:.1f} ms")

            # limit: a type change cannot be instant, and MariaDB says so
            try:
                cur.execute("ALTER TABLE instant_demo_new MODIFY country INT, ALGORITHM=INSTANT")
                print("  MODIFY to INT worked instantly (unexpected)")
            except pymysql.MySQLError as e:
                print(f"  Limit: MODIFY country to INT -> error {e.args[0]}: {e.args[1]}")

            cur.execute("DROP TABLE IF EXISTS instant_demo_new")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
