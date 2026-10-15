"""
before.py — AUTO_INCREMENT (classic approach)

Each table's AUTO_INCREMENT counter is independent. Two separate
tables inserting rows will each start their own numbering from 1,
with no way to share a single counter between them.
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
                CREATE OR REPLACE TABLE sequence_auto_a (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    label VARCHAR(50)
                )
                """
            )
            cur.execute(
                """
                CREATE OR REPLACE TABLE sequence_auto_b (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    label VARCHAR(50)
                )
                """
            )

            names = ["Yosief", "Dinu", "Timofey"]
            for name in names:
                cur.execute(
                    "INSERT INTO sequence_auto_a (label) VALUES (%s)", (name,)
                )
            for name in names:
                cur.execute(
                    "INSERT INTO sequence_auto_b (label) VALUES (%s)", (name,)
                )

            cur.execute("SELECT id, label FROM sequence_auto_a")
            rows_a = cur.fetchall()
            cur.execute("SELECT id, label FROM sequence_auto_b")
            rows_b = cur.fetchall()

        print("[before.py] AUTO_INCREMENT -- each table counts independently")
        print("Table A:")
        for row in rows_a:
            print(f"  id={row[0]}  label={row[1]}")
        print("Table B:")
        for row in rows_b:
            print(f"  id={row[0]}  label={row[1]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()