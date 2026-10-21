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


@pytest.fixture
def invisible_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE OR REPLACE TABLE invisible_pytest (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100)
            )
            """
        )
        cur.execute(
            "ALTER TABLE invisible_pytest ADD COLUMN added_column VARCHAR(100) INVISIBLE"
        )
    conn.commit()
    yield "invisible_pytest"
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS invisible_pytest")
    conn.commit()


class TestInvisibleColumnHiddenFromSelectStar:
    def test_select_star_excludes_invisible_column(self, conn, invisible_table):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO invisible_pytest (name) VALUES (%s)", ("Yosief",)
            )
            cur.execute("SELECT * FROM invisible_pytest")
            row = cur.fetchone()
        assert len(row) == 2  # id, name -- added_column not included

    def test_select_star_shape_unchanged_after_insert(self, conn, invisible_table):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO invisible_pytest (name) VALUES (%s)", ("Dinu",)
            )
            cur.execute(
                "INSERT INTO invisible_pytest (name, added_column) VALUES (%s, %s)",
                ("Timofey", "flagged"),
            )
            cur.execute("SELECT * FROM invisible_pytest")
            rows = cur.fetchall()
        assert all(len(row) == 2 for row in rows)


class TestInvisibleColumnAccessibleByName:
    def test_explicit_select_includes_invisible_column(self, conn, invisible_table):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO invisible_pytest (name, added_column) VALUES (%s, %s)",
                ("Mekelle", "a city"),
            )
            cur.execute(
                "SELECT id, name, added_column FROM invisible_pytest"
            )
            row = cur.fetchone()
        assert row[2] == "a city"

    def test_invisible_column_defaults_to_null_when_not_named(self, conn, invisible_table):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO invisible_pytest (name) VALUES (%s)", ("Anna",)
            )
            cur.execute(
                "SELECT added_column FROM invisible_pytest WHERE name = %s", ("Anna",)
            )
            row = cur.fetchone()
        assert row[0] is None


class TestColumnLessInsertStillWorks:
    def test_insert_without_column_list_does_not_error(self, conn, invisible_table):
        with conn.cursor() as cur:
            # id is AUTO_INCREMENT, so pass NULL for it; name is the
            # only other visible column -- added_column is skipped
            # entirely since it is INVISIBLE.
            cur.execute(
                "INSERT INTO invisible_pytest (name) VALUES (%s)", ("Adwa",)
            )
            cur.execute("SELECT COUNT(*) FROM invisible_pytest")
            count = cur.fetchone()[0]
        assert count == 1

    def test_plain_column_breaks_when_not_invisible(self, conn):
        # Contrast case: a column WITHOUT INVISIBLE changes what
        # SELECT * returns as soon as it is added.
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE OR REPLACE TABLE visible_pytest (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100)
                )
                """
            )
            cur.execute(
                "INSERT INTO visible_pytest (name) VALUES (%s)", ("Yosief",)
            )
            cur.execute("SELECT * FROM visible_pytest")
            before_row = cur.fetchone()

            cur.execute(
                "ALTER TABLE visible_pytest ADD COLUMN added_column VARCHAR(100)"
            )
            cur.execute("SELECT * FROM visible_pytest")
            after_row = cur.fetchone()

            cur.execute("DROP TABLE visible_pytest")

        assert len(before_row) == 2
        assert len(after_row) == 3  # shape changed -- this is the problem INVISIBLE avoids