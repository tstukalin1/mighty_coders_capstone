"""
before.py — INSERT + SELECT (classic approach), against the real
OpenFlights airlines dataset (6,162+ existing rows).

After INSERT, a separate SELECT is needed to fetch the row back --
two round trips for one logical operation.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO airlines (id, name, country) VALUES (%s, %s, %s)",
                (700001, "Mekelle", "Tigray"),
            )
            cur.execute(
                "SELECT id, name, country FROM airlines WHERE id = %s", (700001,)
            )
            row = cur.fetchone()

            # cleanup
            cur.execute("DELETE FROM airlines WHERE id = %s", (700001,))

        print("[before.py] Result via INSERT + SELECT:")
        print(f"  id      = {row[0]}")
        print(f"  name    = {row[1]}")
        print(f"  country = {row[2]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()