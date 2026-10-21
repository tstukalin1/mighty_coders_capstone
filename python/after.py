"""
after.py — INSERT ... RETURNING (MariaDB 10.5+)

RETURNING delivers the inserted row directly in the INSERT response,
without an extra SELECT query.
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
            metadata = {"color": "blue", "weight": 2.0, "tags": ["premium"]}
            cur.execute(  #single query — no extra SELECT needed
                """
                INSERT INTO products (name, metadata)
                VALUES (%s, %s)
                RETURNING id, name, metadata
                """,
                ("Widget B", json.dumps(metadata)),
            )
            row = cur.fetchone()
        print("[after.py] Result via INSERT ... RETURNING:")
        print(f"  id       = {row[0]}")
        print(f"  name     = {row[1]}")
        print(f"  metadata = {row[2]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
