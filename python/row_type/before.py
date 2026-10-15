"""
before.py -- stored procedure without a ROW variable

One DECLARE per column, and one INTO target per column. Adding a column to the
table means editing the procedure in three places.

Run after the database is up:  python python/row_type/before.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP PROCEDURE IF EXISTS demo_get_employee_old")
            cur.execute("CREATE OR REPLACE TABLE demo_emp_old ("
                        " emp_id INT PRIMARY KEY, emp_name VARCHAR(100),"
                        " salary DECIMAL(10,2), department VARCHAR(50))")
            cur.execute("INSERT INTO demo_emp_old VALUES (101, 'Rahul', 50000, 'QA')")
            cur.execute(
                "CREATE PROCEDURE demo_get_employee_old(IN p_id INT) "
                "BEGIN "
                "  DECLARE v_id INT; "
                "  DECLARE v_name VARCHAR(100); "
                "  DECLARE v_salary DECIMAL(10,2); "
                "  DECLARE v_department VARCHAR(50); "
                "  SELECT emp_id, emp_name, salary, department "
                "    INTO v_id, v_name, v_salary, v_department "
                "    FROM demo_emp_old WHERE emp_id = p_id; "
                "  SELECT v_id, v_name, v_salary, v_department; "
                "END"
            )
            cur.execute("CALL demo_get_employee_old(101)")
            row = cur.fetchone()
            while cur.nextset():
                pass

            print("[before.py] procedure with one variable per column")
            print("  variables declared : 4 (v_id, v_name, v_salary, v_department)")
            print("  INTO targets       : 4")
            print(f"  result             : {row}")
            print("  add a column -> edit DECLARE, INTO and SELECT in the procedure")

            cur.execute("DROP PROCEDURE IF EXISTS demo_get_employee_old")
            cur.execute("DROP TABLE IF EXISTS demo_emp_old")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
