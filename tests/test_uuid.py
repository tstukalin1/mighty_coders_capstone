import pytest
import pymysql


@pytest.fixture(autouse=True)
def setup_table(conn):
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_sessions")
        cur.execute(
            "CREATE TABLE test_sessions ("
            "  id INT AUTO_INCREMENT PRIMARY KEY,"
            "  session_id UUID NOT NULL DEFAULT UUID(),"
            "  user_name  VARCHAR(100) NOT NULL"
            ")"
        )
    conn.commit()
    yield
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_sessions")
    conn.commit()


class TestUUIDType:
    def test_auto_generated_uuid_is_not_none(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO test_sessions (user_name) VALUES (%s)", ("alice",)
            )
            cur.execute("SELECT session_id FROM test_sessions WHERE user_name = 'alice'")
            row = cur.fetchone()
        assert row is not None
        assert row[0] is not None

    def test_auto_generated_uuid_has_correct_format(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO test_sessions (user_name) VALUES (%s)", ("bob",)
            )
            cur.execute("SELECT session_id FROM test_sessions WHERE user_name = 'bob'")
            row = cur.fetchone()
        session_id = str(row[0])
        assert len(session_id) == 36
        assert session_id.count("-") == 4

    def test_explicit_valid_uuid_accepted(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO test_sessions (session_id, user_name) VALUES (%s, %s)",
                ("550e8400-e29b-41d4-a716-446655440000", "carol"),
            )
            cur.execute(
                "SELECT session_id FROM test_sessions WHERE user_name = 'carol'"
            )
            row = cur.fetchone()
        assert str(row[0]) == "550e8400-e29b-41d4-a716-446655440000"

    def test_invalid_uuid_rejected(self, conn):
        with pytest.raises(pymysql.err.OperationalError):
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO test_sessions (session_id, user_name) VALUES (%s, %s)",
                    ("not-a-uuid", "mallory"),
                )

    def test_two_rows_get_different_uuids(self, conn):
        with conn.cursor() as cur:
            cur.execute("INSERT INTO test_sessions (user_name) VALUES (%s)", ("x",))
            cur.execute("INSERT INTO test_sessions (user_name) VALUES (%s)", ("y",))
            cur.execute("SELECT session_id FROM test_sessions")
            rows = cur.fetchall()
        assert rows[0][0] != rows[1][0]
