"""
test_row_type.py -- tests for sql/init/08_row_type.sql (ROW data type)

Covers:
  * get_airline_row from the init script: found, not found, NULL country
  * the ROW result equals the old one-variable-per-column result
  * ROW TYPE OF airlines, and changing a field with SET rec.name = ...
  * a ROW with the wrong number of INTO targets is an error

Dataset: the airlines table (flight_dataset.sql). The tests only read it. They
create their own procedures (test_rt_*) and drop them again, because DDL
commits implicitly in MariaDB. Uses the shared `conn` fixture.
"""

import pymysql
import pytest

OLD_WAY = (
    "CREATE PROCEDURE test_rt_old(IN p_id INT) "
    "BEGIN "
    "  DECLARE v_id INT; "
    "  DECLARE v_name VARCHAR(200); "
    "  DECLARE v_country VARCHAR(100); "
    "  DECLARE v_active VARCHAR(5); "
    "  SELECT id, name, country, active INTO v_id, v_name, v_country, v_active "
    "    FROM airlines WHERE id = p_id; "
    "  SELECT v_id, v_name, v_country, v_active; "
    "END"
)

TYPE_OF = (
    "CREATE PROCEDURE test_rt_type_of(IN p_id INT) "
    "BEGIN "
    "  DECLARE a ROW TYPE OF airlines; "
    "  SELECT * INTO a FROM airlines WHERE id = p_id; "
    "  SELECT a.id, a.name, a.country, a.active; "
    "END"
)

SET_FIELD = (
    "CREATE PROCEDURE test_rt_set_field(IN p_id INT) "
    "BEGIN "
    "  DECLARE a ROW TYPE OF airlines; "
    "  SELECT * INTO a FROM airlines WHERE id = p_id; "
    "  SET a.name = UPPER(a.name); "
    "  SELECT a.name; "
    "END"
)

WRONG_COUNT = (
    "CREATE PROCEDURE test_rt_wrong_count(IN p_id INT) "
    "BEGIN "
    "  DECLARE rec ROW (id INT, name VARCHAR(200), country VARCHAR(100), active VARCHAR(5)); "
    "  SELECT id, name INTO rec.id, rec.name, rec.country, rec.active "
    "    FROM airlines WHERE id = p_id; "
    "END"
)

PROCS = ["test_rt_old", "test_rt_type_of", "test_rt_set_field", "test_rt_wrong_count"]


def call(cur, sql):
    """Run a CALL and return the rows of its (single) result set."""
    cur.execute(sql)
    rows = cur.fetchall()
    while cur.nextset():
        pass
    return rows


@pytest.fixture(autouse=True)
def procedures(conn):
    def drop_all():
        with conn.cursor() as cur:
            for name in PROCS:
                cur.execute(f"DROP PROCEDURE IF EXISTS {name}")

    drop_all()
    with conn.cursor() as cur:
        cur.execute(OLD_WAY)
        cur.execute(TYPE_OF)
        cur.execute(SET_FIELD)
    conn.commit()
    yield
    drop_all()


class TestGetAirlineRow:
    def test_procedure_exists(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM information_schema.routines"
                        " WHERE routine_schema = DATABASE() AND routine_name = 'get_airline_row'")
            assert cur.fetchone()[0] == 1

    def test_returns_the_requested_airline(self, conn):
        with conn.cursor() as cur:
            rows = call(cur, "CALL get_airline_row(2)")
        assert rows == ((2, "135 Airways", "United States", "N"),)

    def test_returns_a_different_airline(self, conn):
        with conn.cursor() as cur:
            rows = call(cur, "CALL get_airline_row(3)")
        assert rows[0][1] == "1Time Airline"
        assert rows[0][2] == "South Africa"

    def test_unknown_id_returns_not_found_message(self, conn):
        with conn.cursor() as cur:
            rows = call(cur, "CALL get_airline_row(999999)")
        assert rows == (("Airline not found",),)

    def test_null_country_stays_null(self, conn):
        with conn.cursor() as cur:
            rows = call(cur, "CALL get_airline_row(-1)")
        assert rows == ((-1, "Unknown", None, "Y"),)


class TestRowCompared:
    def test_row_gives_same_result_as_one_variable_per_column(self, conn):
        with conn.cursor() as cur:
            new = call(cur, "CALL get_airline_row(2)")
            old = call(cur, "CALL test_rt_old(2)")
        assert new == old

    def test_row_type_of_airlines_returns_the_row(self, conn):
        with conn.cursor() as cur:
            rows = call(cur, "CALL test_rt_type_of(2)")
        assert rows == ((2, "135 Airways", "United States", "N"),)

    def test_a_row_field_can_be_changed(self, conn):
        with conn.cursor() as cur:
            rows = call(cur, "CALL test_rt_set_field(2)")
            cur.execute("SELECT name FROM airlines WHERE id = 2")
            stored = cur.fetchone()[0]
        assert rows == (("135 AIRWAYS",),)
        assert stored == "135 Airways"      # only the variable changed, not the table


class TestRowLimits:
    def test_wrong_number_of_targets_is_an_error(self, conn):
        with conn.cursor() as cur:
            with pytest.raises(pymysql.err.MySQLError):
                cur.execute(WRONG_COUNT)
                call(cur, "CALL test_rt_wrong_count(2)")
