"""
before.py -- JSON validated in the application (the old way)

The table is plain TEXT, so the database accepts anything. Each program that
writes to it must check the JSON itself (here with json.loads). A program that
forgets the check stores broken JSON, and nothing stops it.

Run after the database is up:  python python/json_check/before.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

DOCS = ['{"color": "blue", "tags": ["sale"]}', '{"color": "red",']   # the second one is broken


def is_valid_json(text):
    try:
        json.loads(text)
        return True
    except ValueError:
        return False


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS json_demo_old")
            cur.execute("CREATE TABLE json_demo_old (id INT AUTO_INCREMENT PRIMARY KEY, doc TEXT)")
            for doc in DOCS:
                if is_valid_json(doc):          # the check lives in this program only
                    cur.execute("INSERT INTO json_demo_old (doc) VALUES (%s)", (doc,))
                    print(f"[before.py] stored (checked in Python): {doc}")
                else:
                    print(f"[before.py] skipped by the Python check:  {doc}")
            # a second program that forgets the check: the database stores the broken text
            cur.execute("INSERT INTO json_demo_old (doc) VALUES (%s)", (DOCS[1],))
            cur.execute("SELECT COUNT(*) FROM json_demo_old")
            print(f"[before.py] rows now: {cur.fetchone()[0]}, one of them is broken JSON")
            cur.execute("DROP TABLE IF EXISTS json_demo_old")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
