"""
before.py -- stored procedure without a ROW variable

One DECLARE per column and one INTO target per column. Adding a column to the
query means editing the procedure in three places.

Dataset: the airlines table. The procedure is created for the demo and dropped
again at the end, so the script can be run any number of times.

Run after the database is up:  python python/row_type/before.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

PROC = "demo_airline_old"


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP PROCEDURE IF EXISTS {PROC}")
            cur.execute(
                f"CREATE PROCEDURE {PROC}(IN p_id INT) "
                "BEGIN "
                "  DECLARE v_id INT; "
                "  DECLARE v_name VARCHAR(200); "
                "  DECLARE v_country VARCHAR(100); "
                "  DECLARE v_active VARCHAR(5); "
                "  SELECT id, name, country, active "
                "    INTO v_id, v_name, v_country, v_active "
                "    FROM airlines WHERE id = p_id; "
                "  SELECT v_id AS id, v_name AS name, "
                "         v_country AS country, v_active AS active; "
                "END"
            )
            cur.execute(f"CALL {PROC}(2)")
            row = cur.fetchone()
            while cur.nextset():
                pass

            print("[before.py] procedure with one variable per column")
            print("  variables declared : 4 (v_id, v_name, v_country, v_active)")
            print("  INTO targets       : 4")
            print(f"  result for id 2    : {row}")
            print("  add a column -> edit DECLARE, INTO and SELECT in the procedure")

            cur.execute(f"DROP PROCEDURE IF EXISTS {PROC}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
