"""
after.py -- stored procedure with a ROW variable

One ROW variable holds the whole row. Fields are read as rec.name, and a field
can be changed with SET rec.name = ... . ROW TYPE OF airlines goes one step
further: the variable takes its shape from the table, so no field list is
written at all.

The init script sql/init/09_row_type.sql already creates get_airline_row; this
script also creates two demo procedures and drops them again at the end.

Run after the database is up:  python python/row_type/after.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

PROC_TYPE_OF = "demo_airline_typeof"


def first_row(cur, sql):
    cur.execute(sql)
    row = cur.fetchone()
    while cur.nextset():
        pass
    return row


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            print("[after.py] procedure with a ROW variable")
            print("  variables declared : 1 (rec ROW (id, name, country, active))")
            print("  INTO targets       : 4 fields of the same variable (rec.id ... rec.active)")
            print(f"  get_airline_row(2)       : {first_row(cur, 'CALL get_airline_row(2)')}")
            print(f"  get_airline_row(999999)  : {first_row(cur, 'CALL get_airline_row(999999)')}")

            cur.execute(f"DROP PROCEDURE IF EXISTS {PROC_TYPE_OF}")
            cur.execute(
                f"CREATE PROCEDURE {PROC_TYPE_OF}(IN p_id INT) "
                "BEGIN "
                "  DECLARE a ROW TYPE OF airlines; "
                "  SELECT * INTO a FROM airlines WHERE id = p_id; "
                "  SET a.name = UPPER(a.name); "
                "  SELECT a.id, a.name, a.country, a.active; "
                "END"
            )
            print("  ROW TYPE OF airlines, with SET a.name = UPPER(a.name):")
            print(f"  result for id 2          : {first_row(cur, f'CALL {PROC_TYPE_OF}(2)')}")

            cur.execute(f"DROP PROCEDURE IF EXISTS {PROC_TYPE_OF}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
