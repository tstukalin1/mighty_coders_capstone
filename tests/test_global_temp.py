import os

import pymysql
import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def conn():
    connection = pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        autocommit=False,
    )
    yield connection
    connection.rollback()
    connection.close()


class TestGlobalTemporaryTableNotSupported:
    def test_create_global_temporary_table_raises_syntax_error(self, conn):
        with conn.cursor() as cur:
            with pytest.raises(pymysql.err.ProgrammingError) as exc_info:
                cur.execute(
                    """
                    CREATE GLOBAL TEMPORARY TABLE scratch_global_pytest (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        note VARCHAR(100)
                    ) ON COMMIT PRESERVE ROWS
                    """
                )
        # MariaDB error 1064: syntax error -- confirms the keyword
        # GLOBAL TEMPORARY is not recognised by the parser at all.
        assert exc_info.value.args[0] == 1064


class TestRegularTemporaryTableIsSessionPrivate:
    def test_temporary_table_visible_within_same_session(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TEMPORARY TABLE scratch_pytest (id INT, note VARCHAR(100))"
            )
            cur.execute(
                "INSERT INTO scratch_pytest (id, note) VALUES (%s, %s)", (1, "hello")
            )
            cur.execute("SELECT * FROM scratch_pytest")
            row = cur.fetchone()
        assert row == (1, "hello")

    def test_temporary_table_not_visible_in_a_different_session(self, conn):
        # Create and populate the table in this session...
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TEMPORARY TABLE scratch_pytest_2 (id INT, note VARCHAR(100))"
            )
            cur.execute(
                "INSERT INTO scratch_pytest_2 (id, note) VALUES (%s, %s)", (1, "hi")
            )

        # ...then open a second, independent connection and try to see it.
        other_connection = pymysql.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            autocommit=False,
        )
        try:
            with other_connection.cursor() as other_cur:
                with pytest.raises(pymysql.err.ProgrammingError) as exc_info:
                    other_cur.execute("SELECT * FROM scratch_pytest_2")
            # MariaDB error 1146: table doesn't exist -- confirms the
            # temporary table's definition is private to the session
            # that created it.
            assert exc_info.value.args[0] == 1146
        finally:
            other_connection.close()