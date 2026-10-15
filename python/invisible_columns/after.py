"""
after.py — adding a column WITH INVISIBLE

A column marked INVISIBLE is excluded from SELECT * and from
INSERT statements that don't name columns explicitly, but is still
fully usable when named directly. Adding a technical column this
way does not change the behavior of existing SELECT * or
column-less INSERT statements.
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
                CREATE OR REPLACE TABLE invisible_new (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100)
                )
                """
            )

            names = ["Yosief", "Dinu", "Timofey"]
            for name in names:
                cur.execute("INSERT INTO invisible_new (name) VALUES (%s)", (name,))

            cur.execute("SELECT * FROM invisible_new")
            before_add = cur.fetchall()

            # Add the new column WITH INVISIBLE
            cur.execute(
                "ALTER TABLE invisible_new ADD COLUMN added_column VARCHAR(100) INVISIBLE"
            )

            # SELECT * does NOT show added_column -- shape unchanged
            cur.execute("SELECT * FROM invisible_new")
            after_add = cur.fetchall()

            # Naming it explicitly DOES show it
            cur.execute("SELECT id, name, added_column FROM invisible_new")
            explicit_select = cur.fetchall()

            # A column-less INSERT still works fine
            cur.execute("INSERT INTO invisible_new (name) VALUES (%s)", ("Anna",))

            cur.execute("SELECT * FROM invisible_new")
            after_insert_star = cur.fetchall()
            cur.execute("SELECT id, name, added_column FROM invisible_new")
            after_insert_explicit = cur.fetchall()

            # Inserting WITH the invisible column named explicitly also works
            cur.execute(
                "INSERT INTO invisible_new (name, added_column) VALUES (%s, %s)",
                ("Frankfurt", "city in Germany"),
            )
            cur.execute("SELECT id, name, added_column FROM invisible_new")
            final_rows = cur.fetchall()

        print("[after.py] Column added WITH INVISIBLE")
        print("Before adding column, SELECT *:")
        for row in before_add:
            print(f"  {row}")
        print("After adding INVISIBLE column, SELECT * (shape unchanged):")
        for row in after_add:
            print(f"  {row}")
        print("Explicit SELECT naming added_column (now visible):")
        for row in explicit_select:
            print(f"  {row}")
        print("After column-less INSERT ('Anna'), SELECT *:")
        for row in after_insert_star:
            print(f"  {row}")
        print("Same, with added_column named explicitly:")
        for row in after_insert_explicit:
            print(f"  {row}")
        print("Final state, after inserting with added_column set explicitly:")
        for row in final_rows:
            print(f"  {row}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()