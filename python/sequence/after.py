"""
after.py — CREATE SEQUENCE (MariaDB)

A sequence is a standalone object, independent of any table. One
sequence can be shared across multiple tables, producing globally
unique, continuously incrementing values -- something AUTO_INCREMENT
cannot do.
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
                "CREATE OR REPLACE SEQUENCE member_id_seq START WITH 100 INCREMENT BY 1"
            )
            cur.execute(
                """
                CREATE OR REPLACE TABLE sequence_seq_a (
                    id INT PRIMARY KEY,
                    label VARCHAR(50)
                )
                """
            )
            cur.execute(
                """
                CREATE OR REPLACE TABLE sequence_seq_b (
                    id INT PRIMARY KEY,
                    label VARCHAR(50)
                )
                """
            )

            # Alternate inserts between table A and B to show the
            # shared counter advancing across both.
            names = ["Yosief", "Dinu", "Timofey"]
            for name in names:
                cur.execute(
                    """
                    INSERT INTO sequence_seq_a (id, label)
                    VALUES (NEXT VALUE FOR member_id_seq, %s)
                    """,
                    (name,),
                )
                cur.execute(
                    """
                    INSERT INTO sequence_seq_b (id, label)
                    VALUES (NEXT VALUE FOR member_id_seq, %s)
                    """,
                    (name,),
                )

            cur.execute("SELECT id, label FROM sequence_seq_a")
            rows_a = cur.fetchall()
            cur.execute("SELECT id, label FROM sequence_seq_b")
            rows_b = cur.fetchall()

        print("[after.py] CREATE SEQUENCE -- one shared counter across both tables")
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