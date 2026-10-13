"""
after.py — INSERT ... RETURNING / DELETE ... RETURNING (MariaDB 10.5+)

The statement itself hands back the rows it touched, so the extra
SELECTs disappear. RETURNING reports only the rows of its own
statement: it is not a history of earlier statements.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

MATRICULATION = "40000001"


def main():
    conn = get_connection()
    statements = 0
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO team_members (name, matriculation_number, age)
                VALUES (%s, %s, %s)
                RETURNING id, name, age, age + 1 AS age_next_year
                """,
                ("Anna", MATRICULATION, 23),
            )
            statements += 1
            row = cur.fetchone()

            cur.execute(
                "DELETE FROM team_members WHERE matriculation_number = %s RETURNING id, name",
                (MATRICULATION,),
            )
            statements += 1
            deleted = cur.fetchall()

            # Multi-row INSERT: every inserted row comes back from one statement
            cur.execute(
                """
                INSERT INTO team_members (name, matriculation_number, age)
                VALUES (%s, %s, %s), (%s, %s, %s)
                RETURNING id, name
                """,
                ("Anna", "40000002", 23, "Berhe", "40000003", 24),
            )
            multi_rows = cur.fetchall()

            cur.execute(
                "DELETE FROM team_members WHERE matriculation_number IN (%s, %s)",
                ("40000002", "40000003"),
            )

        print("[after.py] With RETURNING")
        print(f"  inserted row     = {row[:3]}")
        print(f"  age_next_year    = {row[3]} (computed by RETURNING)")
        print(f"  deleted rows     = {deleted}")
        print(f"  statements sent  = {statements}")
        print(f"  multi-row INSERT returned = {multi_rows}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()