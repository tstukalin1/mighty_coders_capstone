"""
after.py -- CHECK (doc IS JSON): the database refuses broken JSON (MariaDB 12.3.1+)

IS JSON is the SQL-standard predicate (MDEV-37072). As a CHECK constraint it
rejects broken JSON from every program, so no application has to remember the
check. On an older server (11.4) IS JSON is a syntax error (1064); there the
demo falls back to CHECK (JSON_VALID(doc)), which does the same job.

Run after the database is up:  python python/json_check/after.py
"""

import os
import sys

import pymysql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

DOCS = ['{"color": "blue", "tags": ["sale"]}', '{"color": "red",']   # the second one is broken


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS json_demo_new")
            try:
                cur.execute("CREATE TABLE json_demo_new (id INT AUTO_INCREMENT PRIMARY KEY,"
                            " doc TEXT, CONSTRAINT chk_doc CHECK (doc IS JSON))")
                print("[after.py] CHECK (doc IS JSON) created")
            except pymysql.MySQLError as e:
                print(f"[after.py] IS JSON failed: error {e.args[0]} (needs MariaDB 12.3.1);"
                      " using CHECK (JSON_VALID(doc)) instead")
                cur.execute("CREATE TABLE json_demo_new (id INT AUTO_INCREMENT PRIMARY KEY,"
                            " doc TEXT, CONSTRAINT chk_doc CHECK (JSON_VALID(doc)))")
            for doc in DOCS:
                try:
                    cur.execute("INSERT INTO json_demo_new (doc) VALUES (%s)", (doc,))
                    print(f"[after.py] stored:   {doc}")
                except pymysql.MySQLError as e:
                    print(f"[after.py] refused:  {doc}  (error {e.args[0]})")
            cur.execute("SELECT COUNT(*) FROM json_demo_new")
            print(f"[after.py] rows now: {cur.fetchone()[0]}, all valid JSON")
            cur.execute("DROP TABLE IF EXISTS json_demo_new")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
