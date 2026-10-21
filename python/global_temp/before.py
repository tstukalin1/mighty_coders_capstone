"""
before.py — regular TEMPORARY TABLE (the only option in MariaDB today)

A plain TEMPORARY TABLE is private to the session that creates it --
both its structure and its data disappear when that session ends.
There is no way to share the table's definition across sessions; each
session that needs it must run CREATE TEMPORARY TABLE itself.

This script simulates two separate sessions (two separate connections)
each needing the same scratch table, to show that the table must be
created independently in both.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection


def main():
    # Simulate "session 1"
    conn1 = get_connection()
    try:
        with conn1.cursor() as cur1:
            cur1.execute(
                """
                CREATE TEMPORARY TABLE scratch (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    note VARCHAR(100)
                )
                """
            )
            cur1.execute(
                "INSERT INTO scratch (note) VALUES (%s)", ("from session 1",)
            )
            cur1.execute("SELECT * FROM scratch")
            session1_rows = cur1.fetchall()

        # Simulate "session 2" -- a brand new connection
        conn2 = get_connection()
        try:
            with conn2.cursor() as cur2:
                try:
                    # session 2 has NOT created the table itself yet --
                    # it does not exist from this session's point of view
                    cur2.execute("SELECT * FROM scratch")
                    session2_can_see_it = True
                except Exception as e:
                    session2_can_see_it = False
                    session2_error = str(e)
        finally:
            conn2.close()

        print("[before.py] Regular TEMPORARY TABLE -- not shared across sessions")
        print("Session 1 created the table and inserted a row:")
        for row in session1_rows:
            print(f"  {row}")
        if session2_can_see_it:
            print("Session 2 could see the table (unexpected)")
        else:
            print("Session 2 cannot see the table at all -- it must create its own:")
            print(f"  {session2_error}")
    finally:
        conn1.close()


if __name__ == "__main__":
    main()