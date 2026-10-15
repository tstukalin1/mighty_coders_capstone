"""
test_row_type.py -- tests for sql/init/08_row_type.sql and 10_instant_alter.sql

Covers:
  * ROW TYPE OF in a stored procedure (found and not-found case)
  * the row variable following the table after ADD COLUMN
  * ALTER TABLE ... ALGORITHM=INSTANT (ADD COLUMN, DROP COLUMN)
  * ADD COLUMN IF NOT EXISTS, and the duplicate-column error 1060

The tests use their own table and procedure (test_rt_*) so they never change
the employees table from the init scripts. DDL commits implicitly in MariaDB,
so the fixture drops everything again at teardown.
Uses the shared `conn` fixture from tests/conftest.py.
"""

import pymysql
import pytest

GET_EMPLOYEE = (
    "CREATE OR REPLACE PROCEDURE test_rt_get_employee(IN p_id INT) "
    "BEGIN "
    "  DECLARE emp ROW TYPE OF test_rt_emp; "
    "  DECLARE found_record BOOLEAN DEFAULT TRUE; "
    "  DECLARE CONTINUE HANDLER FOR NOT FOUND SET found_record = FALSE; "
    "  SELECT * INTO emp FROM test_rt_emp WHERE emp_id = p_id; "
    "  IF found_record THEN "
    "    SELECT emp.emp_id, emp.emp_name, emp.salary; "
    "  ELSE "
    "    SELECT 'Employee not found' AS message; "
    "  END IF; "
    "END"
)


def call(cur, sql):
    """Run a CALL and return its (single) result set rows."""
    cur.execute(sql)
    rows = cur.fetchall()
    while cur.nextset():
        pass
    return rows


def error_code(exc_info):
    return exc_info.value.args[0]


@pytest.fixture(autouse=True)
def setup_objects(conn):
    def drop_all():
        with conn.cursor() as cur:
            cur.execute("DROP PROCEDURE IF EXISTS test_rt_get_employee")
            cur.execute("DROP TABLE IF EXISTS test_rt_emp")

    drop_all()
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE test_rt_emp ("
            "  emp_id INT PRIMARY KEY, emp_name VARCHAR(100), salary DECIMAL(10,2))"
        )
        cur.execute("INSERT INTO test_rt_emp VALUES (101, 'Rahul', 50000), (102, 'John', 60000)")
        cur.execute(GET_EMPLOYEE)
    conn.commit()
    yield
    drop_all()


class TestRowTypeOf:
    def test_returns_the_requested_employee(self, conn):
        with conn.cursor() as cur:
            rows = call(cur, "CALL test_rt_get_employee(101)")
        assert len(rows) == 1
        assert rows[0][0] == 101
        assert rows[0][1] == "Rahul"
        assert float(rows[0][2]) == 50000.0

    def test_returns_a_different_employee(self, conn):
        with conn.cursor() as cur:
            rows = call(cur, "CALL test_rt_get_employee(102)")
        assert rows[0][1] == "John"

    def test_unknown_id_returns_not_found_message(self, conn):
        with conn.cursor() as cur:
            rows = call(cur, "CALL test_rt_get_employee(999)")
        assert rows == (("Employee not found",),)

    def test_row_variable_follows_table_after_add_column(self, conn):
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE test_rt_emp ADD COLUMN email VARCHAR(150)")
            cur.execute("UPDATE test_rt_emp SET email = 'rahul@gmail.com' WHERE emp_id = 101")
            cur.execute(
                "CREATE OR REPLACE PROCEDURE test_rt_get_employee(IN p_id INT) "
                "BEGIN "
                "  DECLARE emp ROW TYPE OF test_rt_emp; "
                "  SELECT * INTO emp FROM test_rt_emp WHERE emp_id = p_id; "
                "  SELECT emp.emp_name, emp.email; "
                "END"
            )
            rows = call(cur, "CALL test_rt_get_employee(101)")
        assert rows == (("Rahul", "rahul@gmail.com"),)


class TestInstantAlter:
    def test_add_column_instant(self, conn):
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE test_rt_emp ADD COLUMN email VARCHAR(150), ALGORITHM=INSTANT")
            cur.execute("SELECT email FROM test_rt_emp WHERE emp_id = 101")
            assert cur.fetchone()[0] is None

    def test_existing_rows_are_kept(self, conn):
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE test_rt_emp ADD COLUMN email VARCHAR(150), ALGORITHM=INSTANT")
            cur.execute("SELECT COUNT(*) FROM test_rt_emp")
            assert cur.fetchone()[0] == 2

    def test_drop_column_instant(self, conn):
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE test_rt_emp DROP COLUMN salary, ALGORITHM=INSTANT")
            cur.execute(
                "SELECT COUNT(*) FROM information_schema.columns"
                " WHERE table_schema = DATABASE() AND table_name = 'test_rt_emp'"
                " AND column_name = 'salary'"
            )
            assert cur.fetchone()[0] == 0

    def test_add_column_if_not_exists_can_run_twice(self, conn):
        with conn.cursor() as cur:
            for _ in range(2):
                cur.execute(
                    "ALTER TABLE test_rt_emp ADD COLUMN IF NOT EXISTS email VARCHAR(150),"
                    " ALGORITHM=INSTANT"
                )

    def test_duplicate_column_is_error_1060(self, conn):
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE test_rt_emp ADD COLUMN email VARCHAR(150)")
            with pytest.raises(pymysql.err.MySQLError) as exc_info:
                cur.execute("ALTER TABLE test_rt_emp ADD COLUMN email VARCHAR(150)")
        assert error_code(exc_info) == 1060

    def test_changing_column_type_cannot_be_instant(self, conn):
        with conn.cursor() as cur:
            with pytest.raises(pymysql.err.MySQLError):
                cur.execute(
                    "ALTER TABLE test_rt_emp MODIFY emp_name INT, ALGORITHM=INSTANT"
                )


class TestInitScriptsLoaded:
    def test_employees_has_columns_from_both_scripts(self, conn):
        with conn.cursor() as cur:
            try:
                cur.execute("SHOW COLUMNS FROM employees")
            except pymysql.err.MySQLError as exc:
                if exc.args[0] == 1146:
                    pytest.skip("employees missing: 08_row_type.sql not loaded")
                raise
            columns = [r[0] for r in cur.fetchall()]
        assert columns == ["emp_id", "emp_name", "salary", "department", "email", "joining_date"]

    def test_get_employee_procedure_exists(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM information_schema.routines"
                " WHERE routine_schema = DATABASE() AND routine_name = 'get_employee'"
            )
            if cur.fetchone()[0] == 0:
                pytest.skip("get_employee missing: 08_row_type.sql not loaded")
            rows = call(cur, "CALL get_employee(101)")
        assert rows[0][1] == "Rahul"
