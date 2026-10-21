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


class TestInsertReturning:
    def test_returning_row_is_not_none(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO airlines (id, name, country) VALUES (%s, %s, %s)"
                " RETURNING id, name, country",
                (800001, "Test Airline", "TestLand"),
            )
            row = cur.fetchone()
        assert row is not None

    def test_returning_id_matches_inserted(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO airlines (id, name, country) VALUES (%s, %s, %s)"
                " RETURNING id, name, country",
                (800002, "Test Airline 2", "TestLand"),
            )
            row = cur.fetchone()
        assert row[0] == 800002

    def test_returning_data_matches_inserted(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO airlines (id, name, country) VALUES (%s, %s, %s)"
                " RETURNING id, name, country",
                (800003, "Gadget Air", "TestLand"),
            )
            row = cur.fetchone()
        assert row[1] == "Gadget Air"
        assert row[2] == "TestLand"

    def test_returning_vs_select_same_data(self, conn):
        with conn.cursor() as cur:
            # classic: INSERT then SELECT
            cur.execute(
                "INSERT INTO airlines (id, name, country) VALUES (%s, %s, %s)",
                (800004, "Classic Air", "TestLand"),
            )
            cur.execute(
                "SELECT id, name, country FROM airlines WHERE id = %s", (800004,)
            )
            classic_row = cur.fetchone()

            # modern: single INSERT RETURNING
            cur.execute(
                "INSERT INTO airlines (id, name, country) VALUES (%s, %s, %s)"
                " RETURNING id, name, country",
                (800005, "Modern Air", "TestLand"),
            )
            returning_row = cur.fetchone()

        assert classic_row[2] == returning_row[2] == "TestLand"
        assert classic_row[1] == "Classic Air"
        assert returning_row[1] == "Modern Air"


class TestDeleteReturning:
    def test_delete_returning_row_is_not_none(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO airlines (id, name, country) VALUES (%s, %s, %s)",
                (800006, "To Delete", "TestLand"),
            )
            cur.execute(
                "DELETE FROM airlines WHERE id = %s RETURNING id, name", (800006,)
            )
            row = cur.fetchone()
        assert row is not None
        assert row == (800006, "To Delete")

    def test_delete_returning_removes_row(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO airlines (id, name, country) VALUES (%s, %s, %s)",
                (800007, "Will Be Gone", "TestLand"),
            )
            cur.execute(
                "DELETE FROM airlines WHERE id = %s RETURNING id, name", (800007,)
            )
            cur.fetchone()
            cur.execute("SELECT * FROM airlines WHERE id = %s", (800007,))
            remaining = cur.fetchone()
        assert remaining is None


class TestReturningLimits:
    def test_second_insert_returning_does_not_include_first_row(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO airlines (id, name, country) VALUES (%s, %s, %s)"
                " RETURNING id, name",
                (800008, "First Air", "TestLand"),
            )
            first_rows = cur.fetchall()

            cur.execute(
                "INSERT INTO airlines (id, name, country) VALUES (%s, %s, %s)"
                " RETURNING id, name",
                (800009, "Second Air", "TestLand"),
            )
            second_rows = cur.fetchall()

        assert list(first_rows) == [(800008, "First Air")]
        # RETURNING covers only its own statement: the second insert
        # returns just its own row, not the first one.
        assert list(second_rows) == [(800009, "Second Air")]
        assert all(row[0] != 800008 for row in second_rows)