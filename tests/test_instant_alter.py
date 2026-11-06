"""Instant ADD / DROP / MODIFY COLUMN (python/instant_alter/, sql/init/14_instant_alter.sql).

The server counts every column change it did instantly in the global status
variable Innodb_instant_alter_column. The tests use it to prove which ALTERs
were instant and which rebuilt the table. ALTER TABLE commits implicitly, so
the fixture drops the demo table itself.
"""

import pymysql
import pytest

def instant_count(cur):
    cur.execute("SHOW GLOBAL STATUS LIKE 'Innodb_instant_alter_column'")
    return int(cur.fetchone()[1])


def columns(cur):
    cur.execute("SHOW COLUMNS FROM test_instant_alter")
    return {row[0]: row[1] for row in cur.fetchall()}


@pytest.fixture(autouse=True)
def demo_table(conn):
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_instant_alter")
        cur.execute("CREATE TABLE test_instant_alter ("
                    " id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(200), country VARCHAR(100))")
        cur.execute("INSERT INTO test_instant_alter (name, country)"
                    " SELECT CONCAT('Airline ', seq), 'Germany' FROM seq_1_to_1000")
    conn.commit()
    yield
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_instant_alter")
    conn.commit()


def test_add_column_is_instant(conn):
    with conn.cursor() as cur:
        before = instant_count(cur)
        cur.execute("ALTER TABLE test_instant_alter ADD COLUMN note VARCHAR(50), ALGORITHM=INSTANT")
        assert instant_count(cur) == before + 1
        assert "note" in columns(cur)


def test_instant_column_default_applies_to_old_rows(conn):
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE test_instant_alter ADD COLUMN status VARCHAR(10) NOT NULL DEFAULT 'active',"
                    " ALGORITHM=INSTANT")
        cur.execute("SELECT COUNT(*) FROM test_instant_alter WHERE status = 'active'")
        assert cur.fetchone()[0] == 1000


def test_drop_column_is_instant_and_keeps_rows(conn):
    with conn.cursor() as cur:
        before = instant_count(cur)
        cur.execute("ALTER TABLE test_instant_alter DROP COLUMN country, ALGORITHM=INSTANT")
        assert instant_count(cur) == before + 1
        assert "country" not in columns(cur)
        cur.execute("SELECT COUNT(*) FROM test_instant_alter")
        assert cur.fetchone()[0] == 1000


def test_longer_varchar_is_instant(conn):
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE test_instant_alter MODIFY name VARCHAR(300), ALGORITHM=INSTANT")
        assert columns(cur)["name"] == "varchar(300)"


def test_type_change_is_refused_with_instant(conn):
    with conn.cursor() as cur:
        with pytest.raises(pymysql.MySQLError) as exc:
            cur.execute("ALTER TABLE test_instant_alter MODIFY country INT, ALGORITHM=INSTANT")
        assert exc.value.args[0] == 1846
        assert columns(cur)["country"] == "varchar(100)"   # nothing changed


def test_copy_rebuilds_instead_of_instant(conn):
    with conn.cursor() as cur:
        before = instant_count(cur)
        cur.execute("ALTER TABLE test_instant_alter ADD COLUMN note VARCHAR(50), ALGORITHM=COPY")
        assert instant_count(cur) == before          # the old way: not counted as instant
        assert "note" in columns(cur)
