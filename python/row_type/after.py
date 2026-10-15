"""
after.py -- stored procedure with ROW TYPE OF

One ROW variable holds the whole row, and its shape follows the table.
After a column is added, the same procedure can read it with no change to
DECLARE or SELECT * INTO.

Run after the database is up:  python python/row_type/after.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP PROCEDURE IF EXISTS demo_get_employee_new")
            cur.execute("CREATE OR REPLACE TABLE demo_emp_new ("
                        " emp_id INT PRIMARY KEY, emp_name VARCHAR(100),"
                        " salary DECIMAL(10,2), department VARCHAR(50))")
            cur.execute("INSERT INTO demo_emp_new VALUES (101, 'Rahul', 50000, 'QA')")
            cur.execute(
                "CREATE PROCEDURE demo_get_employee_new(IN p_id INT) "
                "BEGIN "
                "  DECLARE emp ROW TYPE OF demo_emp_new; "
                "  SELECT * INTO emp FROM demo_emp_new WHERE emp_id = p_id; "
                "  SELECT emp.emp_id, emp.emp_name, emp.salary, emp.department; "
                "END"
            )
            cur.execute("CALL demo_get_employee_new(101)")
            row = cur.fetchone()
            while cur.nextset():
                pass

            print("[after.py] procedure with ROW TYPE OF")
            print("  variables declared : 1 (emp ROW TYPE OF demo_emp_new)")
            print("  INTO targets       : 1 (SELECT * INTO emp)")
            print(f"  result             : {row}")

            # the row variable follows the table definition
            cur.execute("ALTER TABLE demo_emp_new ADD COLUMN email VARCHAR(150), ALGORITHM=INSTANT")
            cur.execute("UPDATE demo_emp_new SET email = 'rahul@gmail.com' WHERE emp_id = 101")
            cur.execute(
                "CREATE OR REPLACE PROCEDURE demo_get_employee_new(IN p_id INT) "
                "BEGIN "
                "  DECLARE emp ROW TYPE OF demo_emp_new; "
                "  SELECT * INTO emp FROM demo_emp_new WHERE emp_id = p_id; "
                "  SELECT emp.emp_name, emp.email; "
                "END"
            )
            cur.execute("CALL demo_get_employee_new(101)")
            print(f"  after ADD COLUMN email, emp.email is available: {cur.fetchone()}")
            while cur.nextset():
                pass

            cur.execute("DROP PROCEDURE IF EXISTS demo_get_employee_new")
            cur.execute("DROP TABLE IF EXISTS demo_emp_new")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
