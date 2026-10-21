"""
before.py — adding a column WITHOUT INVISIBLE

Adding a new column to an existing table changes the result of
SELECT * and breaks any INSERT statement that doesn't list columns
explicitly -- both now need to account for the new column.
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
                CREATE OR REPLACE TABLE invisible_old (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100)
                )
                """
            )

            names = ["Yosief", "Dinu", "Timofey"]
            for name in names:
                cur.execute("INSERT INTO invisible_old (name) VALUES (%s)", (name,))

            cur.execute("SELECT * FROM invisible_old")
            before_add = cur.fetchall()

            # Add a new column WITHOUT INVISIBLE
            cur.execute("ALTER TABLE invisible_old ADD COLUMN added_column VARCHAR(100)")

            cur.execute("SELECT * FROM invisible_old")
            after_add = cur.fetchall()

            # A column-less INSERT must now account for the new column
            cur.execute(
                "INSERT INTO invisible_old VALUES (NULL, %s, %s)",
                ("Anna", "added without a note"),
            )

            cur.execute("SELECT * FROM invisible_old")
            final_rows = cur.fetchall()

        print("[before.py] Column added WITHOUT INVISIBLE")
        print("Before adding column, SELECT *:")
        for row in before_add:
            print(f"  {row}")
        print("After adding column, SELECT * (shape changed):")
        for row in after_add:
            print(f"  {row}")
        print("After column-less INSERT (had to supply all 3 values):")
        for row in final_rows:
            print(f"  {row}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()