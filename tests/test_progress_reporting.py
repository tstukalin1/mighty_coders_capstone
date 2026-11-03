"""
test_progress_reporting.py -- tests for sql/init/13_progress_reporting.sql and
python/progress_reporting/ (ALTER TABLE ... ADD INDEX with progress reporting)

Covers:
  * ADD INDEX with ALGORITHM=INPLACE, LOCK=NONE, and the lookup using it
  * CHECK TABLE reports OK
  * the PROCESSLIST has the progress columns (STAGE, MAX_STAGE, PROGRESS)
  * ADD INDEX IF NOT EXISTS can run twice; a plain duplicate is error 1061;
    an unknown column is error 1072
  * the init script leaves the airlines table unchanged

Dataset: a small copy of the airlines names (test_pr_airlines). The tests drop
it again, because DDL commits implicitly in MariaDB. Uses the shared `conn`
fixture.
"""

import pymysql
import pytest

ROWS = 5000


@pytest.fixture(autouse=True)
def table(conn):
    def drop():
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS test_pr_airlines")

    drop()
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE test_pr_airlines ("
                    " id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(200))")
        cur.execute("INSERT INTO test_pr_airlines (name)"
                    f" SELECT name FROM airlines WHERE name IS NOT NULL LIMIT {ROWS}")
    conn.commit()
    yield
    drop()


def add_index(cur):
    cur.execute("ALTER TABLE test_pr_airlines ADD INDEX idx_name (name),"
                " ALGORITHM=INPLACE, LOCK=NONE")


class TestAddIndex:
    def test_add_index_inplace_works(self, conn):
        with conn.cursor() as cur:
            add_index(cur)
            cur.execute("SELECT COUNT(*) FROM information_schema.statistics"
                        " WHERE table_schema = DATABASE()"
                        " AND table_name = 'test_pr_airlines' AND index_name = 'idx_name'")
            assert cur.fetchone()[0] == 1

    def test_lookup_uses_the_index_afterwards(self, conn):
        with conn.cursor() as cur:
            cur.execute("EXPLAIN SELECT COUNT(*) FROM test_pr_airlines WHERE name = '135 Airways'")
            assert cur.fetchone()[3] == "ALL"
            add_index(cur)
            cur.execute("EXPLAIN SELECT COUNT(*) FROM test_pr_airlines WHERE name = '135 Airways'")
            row = cur.fetchone()
            assert row[3] in ("ref", "index")
            assert row[5] == "idx_name"

    def test_rows_are_unchanged_by_the_index(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM test_pr_airlines")
            before = cur.fetchone()[0]
            add_index(cur)
            cur.execute("SELECT COUNT(*) FROM test_pr_airlines")
            assert cur.fetchone()[0] == before

    def test_check_table_is_ok(self, conn):
        with conn.cursor() as cur:
            add_index(cur)
            cur.execute("CHECK TABLE test_pr_airlines")
            assert cur.fetchall()[-1][3] == "OK"


class TestProgressColumns:
    def test_processlist_has_progress_columns(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT STAGE, MAX_STAGE, PROGRESS"
                        " FROM information_schema.PROCESSLIST WHERE ID = CONNECTION_ID()")
            assert cur.fetchone() is not None


class TestIndexLimits:
    def test_add_index_if_not_exists_can_run_twice(self, conn):
        with conn.cursor() as cur:
            for _ in range(2):
                cur.execute("ALTER TABLE test_pr_airlines"
                            " ADD INDEX IF NOT EXISTS idx_name (name)")

    def test_duplicate_index_is_error_1061(self, conn):
        with conn.cursor() as cur:
            add_index(cur)
            with pytest.raises(pymysql.err.MySQLError) as exc_info:
                add_index(cur)
        assert exc_info.value.args[0] == 1061

    def test_index_on_unknown_column_is_error_1072(self, conn):
        with conn.cursor() as cur:
            with pytest.raises(pymysql.err.MySQLError) as exc_info:
                cur.execute("ALTER TABLE test_pr_airlines ADD INDEX idx_x (airline_name)")
        assert exc_info.value.args[0] == 1072


class TestInitScript:
    def test_init_script_left_airlines_without_a_demo_index(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM information_schema.statistics"
                        " WHERE table_schema = DATABASE() AND table_name = 'airlines'"
                        " AND index_name = 'idx_name'")
            assert cur.fetchone()[0] == 0

    def test_init_script_dropped_its_demo_table(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM information_schema.tables"
                        " WHERE table_schema = DATABASE() AND table_name = 'progress_demo'")
            assert cur.fetchone()[0] == 0
