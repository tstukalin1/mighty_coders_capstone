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

            # Limit: a sequence is not transactional. A rolled-back INSERT
            # keeps its number used, so the next row leaves a gap.
            conn.autocommit(False)
            cur.execute(
                "INSERT INTO sequence_seq_a (id, label)"
                " VALUES (NEXT VALUE FOR member_id_seq, 'cancelled')"
            )
            conn.rollback()
            cur.execute(
                "INSERT INTO sequence_seq_a (id, label)"
                " VALUES (NEXT VALUE FOR member_id_seq, 'after rollback')"
            )
            conn.commit()
            conn.autocommit(True)
            cur.execute("SELECT id FROM sequence_seq_a WHERE label = 'after rollback'")
            gap_id = cur.fetchone()[0]

            # SETVAL moves the counter, e.g. after importing old data
            cur.execute("SELECT SETVAL(member_id_seq, 1000)")
            cur.execute("SELECT NEXT VALUE FOR member_id_seq")
            after_setval = cur.fetchone()[0]

        print("[after.py] CREATE SEQUENCE -- one shared counter across both tables")
        print("Table A:")
        for row in rows_a:
            print(f"  id={row[0]}  label={row[1]}")
        print("Table B:")
        for row in rows_b:
            print(f"  id={row[0]}  label={row[1]}")
        print(f"Limit: after a rolled-back INSERT the next id is {gap_id}, not 106 (a gap)")
        print(f"SETVAL(member_id_seq, 1000), then NEXT VALUE: {after_setval}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()