"""
after.py — INSERT ... RETURNING (MariaDB 10.5+), against the real
OpenFlights airlines dataset (6,162+ existing rows).

RETURNING delivers the inserted row directly in the INSERT response,
without an extra SELECT query -- one round trip instead of two.
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
                """
                INSERT INTO airlines (id, name, country)
                VALUES (%s, %s, %s)
                RETURNING id, name, country
                """,
                (700002, "Adwa", "Tigray"),
            )
            row = cur.fetchone()

            # DELETE ... RETURNING also works
            cur.execute(
                "DELETE FROM airlines WHERE id = %s RETURNING id, name",
                (700002,),
            )
            deleted = cur.fetchone()

        print("[after.py] Result via INSERT ... RETURNING:")
        print(f"  id      = {row[0]}")
        print(f"  name    = {row[1]}")
        print(f"  country = {row[2]}")
        print(f"[after.py] Deleted via DELETE ... RETURNING: {deleted}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()