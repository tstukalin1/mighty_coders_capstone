import pytest


@pytest.fixture(autouse=True)
def setup_tables(conn):
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_enrolled_python")
        cur.execute("DROP TABLE IF EXISTS test_enrolled_sql")
        cur.execute("CREATE TABLE test_enrolled_python (student VARCHAR(100) NOT NULL)")
        cur.execute("CREATE TABLE test_enrolled_sql    (student VARCHAR(100) NOT NULL)")
        for s in ("alice", "bob", "carol", "dave"):
            cur.execute("INSERT INTO test_enrolled_python VALUES (%s)", (s,))
        for s in ("bob", "carol", "eve", "frank"):
            cur.execute("INSERT INTO test_enrolled_sql VALUES (%s)", (s,))
    conn.commit()
    yield
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_enrolled_python")
        cur.execute("DROP TABLE IF EXISTS test_enrolled_sql")
    conn.commit()


class TestIntersect:
    def test_intersect_returns_common_students(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT student FROM test_enrolled_python"
                " INTERSECT"
                " SELECT student FROM test_enrolled_sql"
                " ORDER BY student"
            )
            result = [r[0] for r in cur.fetchall()]
        assert result == ["bob", "carol"]

    def test_intersect_count(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM ("
                "  SELECT student FROM test_enrolled_python"
                "  INTERSECT"
                "  SELECT student FROM test_enrolled_sql"
                ") t"
            )
            count = cur.fetchone()[0]
        assert count == 2


class TestExcept:
    def test_except_python_minus_sql(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT student FROM test_enrolled_python"
                " EXCEPT"
                " SELECT student FROM test_enrolled_sql"
                " ORDER BY student"
            )
            result = [r[0] for r in cur.fetchall()]
        assert result == ["alice", "dave"]

    def test_except_sql_minus_python(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT student FROM test_enrolled_sql"
                " EXCEPT"
                " SELECT student FROM test_enrolled_python"
                " ORDER BY student"
            )
            result = [r[0] for r in cur.fetchall()]
        assert result == ["eve", "frank"]

    def test_except_is_not_symmetric(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT student FROM test_enrolled_python"
                " EXCEPT SELECT student FROM test_enrolled_sql"
            )
            a = {r[0] for r in cur.fetchall()}
            cur.execute(
                "SELECT student FROM test_enrolled_sql"
                " EXCEPT SELECT student FROM test_enrolled_python"
            )
            b = {r[0] for r in cur.fetchall()}
        assert a != b
