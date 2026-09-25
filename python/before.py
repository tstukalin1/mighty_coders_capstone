"""
before.py — INSERT + SELECT (classic approach)

After INSERT, we fetch the inserted row with a separate SELECT query
using cursor.lastrowid.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db import get_connection


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            metadata = {"color": "red", "weight": 1.5, "tags": ["sale", "new"]}
            cur.execute(
                "INSERT INTO products (name, metadata) VALUES (%s, %s)",
                ("Widget A", json.dumps(metadata)),
            )
            inserted_id = cur.lastrowid  #ID of the inserted row
            cur.execute(
                "SELECT id, name, metadata FROM products WHERE id = %s",
                (inserted_id,),
            )
            row = cur.fetchone()
        print("[before.py] Result via INSERT + SELECT:")
        print(f"  id       = {row[0]}")
        print(f"  name     = {row[1]}")
        print(f"  metadata = {row[2]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
