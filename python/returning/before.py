"""
before.py — INSERT/DELETE without RETURNING (classic approach)

Getting the new row, a computed value, or the deleted rows back takes
extra statements. Runs against team_members (created by
sql/init/11_create_or_replace_returning.sql).
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
                "INSERT INTO team_members (name, matriculation_number, age) VALUES (%s, %s, %s)",
                ("Anna", MATRICULATION, 23),
            )
            statements += 1
            new_id = cur.lastrowid

            cur.execute("SELECT id, name, age FROM team_members WHERE id = %s", (new_id,))
            statements += 1
            row = cur.fetchone()
            age_next_year = row[2] + 1  # computed in the application

            # To know what a DELETE removed, it has to be read first
            cur.execute(
                "SELECT id, name FROM team_members WHERE matriculation_number = %s",
                (MATRICULATION,),
            )
            statements += 1
            to_delete = cur.fetchall()

            cur.execute(
                "DELETE FROM team_members WHERE matriculation_number = %s",
                (MATRICULATION,),
            )
            statements += 1

        print("[before.py] Without RETURNING")
        print(f"  inserted row     = {row}")
        print(f"  age_next_year    = {age_next_year} (computed in Python)")
        print(f"  deleted rows     = {to_delete} (read before deleting)")
        print(f"  statements sent  = {statements}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()