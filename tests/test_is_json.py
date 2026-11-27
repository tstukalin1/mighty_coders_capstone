"""IS JSON (feature 7): the SQL-standard predicate, added in MariaDB 12.3.1 (MDEV-37072).

On 12.3.1 and newer the tests check that it works; on an older server (CI also runs 11.4)
they check that it is refused with a syntax error, so the README's version claim is tested
on both sides.
"""
import pymysql
import pytest

IS_JSON_FROM = (12, 3, 1)


@pytest.fixture
def docs(conn, version):
    if version < IS_JSON_FROM:
        pytest.skip("IS JSON needs MariaDB 12.3.1")
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_is_json")
        # TEXT, not JSON: a JSON column already gets an automatic JSON_VALID check
        cur.execute("CREATE TABLE test_is_json (id INT AUTO_INCREMENT PRIMARY KEY,"
                    " doc TEXT, CONSTRAINT chk_doc CHECK (doc IS JSON))")
    conn.commit()
    yield
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_is_json")
    conn.commit()


def test_is_json_predicate(conn, version):
    with conn.cursor() as cur:
        if version < IS_JSON_FROM:
            with pytest.raises(pymysql.MySQLError) as exc:
                cur.execute("""SELECT '{"a": 1}' IS JSON""")
            assert exc.value.args[0] == 1064
            return
        cur.execute("""SELECT '{"a": 1}' IS JSON, '[1, 2]' IS JSON, 'x' IS JSON, '{"a":' IS JSON""")
        assert cur.fetchone() == (1, 1, 0, 0)


def test_check_is_json_accepts_valid_documents(conn, docs):
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO test_is_json (doc) VALUES ('{"color": "blue"}'), ('[1, 2, 3]')""")
        cur.execute("SELECT COUNT(*) FROM test_is_json")
        assert cur.fetchone()[0] == 2


@pytest.mark.parametrize("bad", ["not json", '{"a":', "{'single': 'quotes'}"])
def test_check_is_json_rejects_invalid_documents(conn, docs, bad):
    with conn.cursor() as cur:
        with pytest.raises(pymysql.MySQLError) as exc:
            cur.execute("INSERT INTO test_is_json (doc) VALUES (%s)", (bad,))
        assert exc.value.args[0] == 4025   # CONSTRAINT `chk_doc` failed


def test_is_json_value_types(conn, docs):
    with conn.cursor() as cur:
        cur.execute("""SELECT '{"a": 1}' IS JSON OBJECT, '[1]' IS JSON ARRAY, '[1]' IS JSON OBJECT""")
        assert cur.fetchone() == (1, 1, 0)


def test_is_json_with_unique_keys(conn, docs):
    with conn.cursor() as cur:
        cur.execute("""SELECT '{"a": 1, "a": 2}' IS JSON, '{"a": 1, "a": 2}' IS JSON WITH UNIQUE KEYS""")
        assert cur.fetchone() == (1, 0)
