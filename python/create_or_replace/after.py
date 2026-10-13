"""
after.py — CREATE OR REPLACE (MariaDB)

One statement replaces the object whether or not it exists. It works on
tables and views, but it still respects foreign keys: a table that
another table references cannot be replaced.
"""

import sys
import os

import pymysql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # --- Table: one statement, safe to repeat ----------------
            cur.execute(
                "CREATE OR REPLACE TABLE replace_demo (id INT PRIMARY KEY, name VARCHAR(100), age INT)"
            )
            cur.executemany(
                "INSERT INTO replace_demo (id, name, age) VALUES (%s, %s, %s)",
                [(1, "Yosief", 26), (2, "Dinu", 24), (3, "Timofey", 22)],
            )
            cur.execute("SELECT COUNT(*) FROM replace_demo")
            rows_before = cur.fetchone()[0]

            # Replace it with a different definition: no error, data is gone
            cur.execute(
                "CREATE OR REPLACE TABLE replace_demo "
                "(id INT PRIMARY KEY, name VARCHAR(100), age INT, city VARCHAR(100))"
            )
            cur.execute("SELECT COUNT(*) FROM replace_demo")
            rows_after = cur.fetchone()[0]

            # --- View: one statement, run twice ----------------------
            cur.executemany(
                "INSERT INTO replace_demo (id, name, age, city) VALUES (%s, %s, %s, %s)",
                [(1, "Yosief", 26, "Bremen"), (2, "Dinu", 24, "Bremen"), (3, "Timofey", 22, "Bremen")],
            )
            cur.execute(
                "CREATE OR REPLACE VIEW replace_demo_view AS "
                "SELECT id, name, age FROM replace_demo WHERE age < 30"
            )
            cur.execute("SELECT * FROM replace_demo_view")
            view_v1 = cur.fetchall()

            cur.execute(
                "CREATE OR REPLACE VIEW replace_demo_view AS "
                "SELECT id, name, age FROM replace_demo WHERE age < 25"
            )
            cur.execute("SELECT * FROM replace_demo_view")
            view_v2 = cur.fetchall()

            # --- Limit: foreign key blocks replacing the parent ------
            cur.execute("CREATE OR REPLACE TABLE replace_demo_child (id INT PRIMARY KEY, parent_id INT)")
            cur.execute("DROP TABLE replace_demo_child")
            cur.execute("CREATE OR REPLACE TABLE replace_demo_parent (id INT PRIMARY KEY)")
            cur.execute("INSERT INTO replace_demo_parent (id) VALUES (1)")
            cur.execute(
                "CREATE OR REPLACE TABLE replace_demo_child ("
                "id INT PRIMARY KEY, parent_id INT, "
                "FOREIGN KEY (parent_id) REFERENCES replace_demo_parent(id))"
            )
            cur.execute("INSERT INTO replace_demo_child (id, parent_id) VALUES (1, 1)")
            try:
                cur.execute("CREATE OR REPLACE TABLE replace_demo_parent (id INT PRIMARY KEY)")
                fk_error = None
            except pymysql.err.MySQLError as e:
                fk_error = e.args

            # cleanup (child first, because of the foreign key)
            cur.execute("DROP VIEW IF EXISTS replace_demo_view")
            cur.execute("DROP TABLE IF EXISTS replace_demo_child")
            cur.execute("DROP TABLE IF EXISTS replace_demo_parent")
            cur.execute("DROP TABLE IF EXISTS replace_demo")

        print("[after.py] CREATE OR REPLACE (one statement each)")
        print(f"Rows before replacing the table: {rows_before}, after: {rows_after}")
        print(f"View (age < 30): {view_v1}")
        print(f"View replaced (age < 25), no error: {view_v2}")
        print(f"Replacing a referenced parent table failed: {fk_error}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()