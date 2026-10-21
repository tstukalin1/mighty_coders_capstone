"""
before.py — DROP ... IF EXISTS + CREATE (classic approach)

Re-creating an object safely takes two statements. A plain CREATE on
its own fails as soon as the object already exists.
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
            # --- Table: two statements -------------------------------
            cur.execute("DROP TABLE IF EXISTS replace_demo")
            cur.execute(
                "CREATE TABLE replace_demo (id INT PRIMARY KEY, name VARCHAR(100), age INT)"
            )
            cur.executemany(
                "INSERT INTO replace_demo (id, name, age) VALUES (%s, %s, %s)",
                [(1, "Yosief", 26), (2, "Dinu", 24), (3, "Timofey", 22)],
            )

            # A plain CREATE on an existing table fails
            try:
                cur.execute("CREATE TABLE replace_demo (id INT PRIMARY KEY)")
                plain_create_error = None
            except pymysql.err.MySQLError as e:
                plain_create_error = e.args

            # --- View: two statements, run twice ---------------------
            cur.execute("DROP VIEW IF EXISTS replace_demo_view")
            cur.execute(
                "CREATE VIEW replace_demo_view AS "
                "SELECT id, name, age FROM replace_demo WHERE age < 30"
            )
            cur.execute("SELECT * FROM replace_demo_view")
            view_v1 = cur.fetchall()

            try:
                cur.execute(
                    "CREATE VIEW replace_demo_view AS "
                    "SELECT id, name, age FROM replace_demo WHERE age < 25"
                )
                plain_view_error = None
            except pymysql.err.MySQLError as e:
                plain_view_error = e.args

            cur.execute("DROP VIEW IF EXISTS replace_demo_view")
            cur.execute(
                "CREATE VIEW replace_demo_view AS "
                "SELECT id, name, age FROM replace_demo WHERE age < 25"
            )
            cur.execute("SELECT * FROM replace_demo_view")
            view_v2 = cur.fetchall()

            # cleanup
            cur.execute("DROP VIEW IF EXISTS replace_demo_view")
            cur.execute("DROP TABLE IF EXISTS replace_demo")

        print("[before.py] DROP IF EXISTS + CREATE (two statements each)")
        print(f"Plain CREATE TABLE on existing table failed: {plain_create_error}")
        print(f"View (age < 30): {view_v1}")
        print(f"Plain CREATE VIEW on existing view failed:  {plain_view_error}")
        print(f"View after DROP + CREATE (age < 25): {view_v2}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()