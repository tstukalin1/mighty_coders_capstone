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
def table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE OR REPLACE TABLE returning_pytest (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                matriculation_number VARCHAR(20) NOT NULL,
                age INT
            )
            """
        )
    conn.commit()
    yield "returning_pytest"
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS returning_pytest")
    conn.commit()


class TestInsertReturning:
    def test_returns_inserted_columns(self, conn, table):
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {table} (name, matriculation_number, age) "
                "VALUES (%s, %s, %s) RETURNING id, name, age",
                ("Anna", "1", 23),
            )
            row = cur.fetchone()
        assert isinstance(row[0], int)
        assert row[1:] == ("Anna", 23)

    def test_returning_matches_classic_insert_then_select(self, conn, table):
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {table} (name, matriculation_number, age) VALUES (%s, %s, %s)",
                ("Classic", "1", 23),
            )
            cur.execute(f"SELECT name, age FROM {table} WHERE id = %s", (cur.lastrowid,))
            classic = cur.fetchone()
            cur.execute(
                f"INSERT INTO {table} (name, matriculation_number, age) "
                "VALUES (%s, %s, %s) RETURNING name, age",
                ("Classic", "2", 23),
            )
            returning = cur.fetchone()
        assert classic == returning

    def test_returning_can_compute_expressions(self, conn, table):
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {table} (name, matriculation_number, age) "
                "VALUES (%s, %s, %s) RETURNING age, age + 1 AS age_next_year",
                ("Anna", "1", 23),
            )
            row = cur.fetchone()
        assert row == (23, 24)

    def test_returning_star_returns_every_column(self, conn, table):
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {table} (name, matriculation_number, age) "
                "VALUES (%s, %s, %s) RETURNING *",
                ("Anna", "1", 23),
            )
            row = cur.fetchone()
        assert len(row) == 4

    def test_multi_row_insert_returns_all_rows(self, conn, table):
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {table} (name, matriculation_number, age) "
                "VALUES (%s, %s, %s), (%s, %s, %s) RETURNING name",
                ("Anna", "1", 23, "Berhe", "2", 24),
            )
            rows = cur.fetchall()
        assert sorted(r[0] for r in rows) == ["Anna", "Berhe"]

    def test_second_insert_does_not_return_first_row(self, conn, table):
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {table} (name, matriculation_number, age) "
                "VALUES (%s, %s, %s) RETURNING name",
                ("Anna", "1", 23),
            )
            cur.fetchall()
            cur.execute(
                f"INSERT INTO {table} (name, matriculation_number, age) "
                "VALUES (%s, %s, %s) RETURNING name",
                ("Berhe", "2", 24),
            )
            rows = cur.fetchall()
        assert rows == (("Berhe",),)


class TestDeleteReturning:
    def test_delete_returns_deleted_rows(self, conn, table):
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {table} (name, matriculation_number, age) "
                "VALUES (%s, %s, %s), (%s, %s, %s)",
                ("Anna", "1", 23, "Berhe", "2", 24),
            )
            cur.execute(
                f"DELETE FROM {table} WHERE matriculation_number IN (%s, %s) RETURNING name",
                ("1", "2"),
            )
            rows = cur.fetchall()
        assert sorted(r[0] for r in rows) == ["Anna", "Berhe"]

    def test_deleted_rows_are_gone(self, conn, table):
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {table} (name, matriculation_number, age) VALUES (%s, %s, %s)",
                ("Anna", "1", 23),
            )
            cur.execute(f"DELETE FROM {table} WHERE matriculation_number = %s RETURNING id", ("1",))
            cur.fetchall()
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            assert cur.fetchone()[0] == 0


class TestUpdateReturningLimit:
    def test_update_returning_is_a_syntax_error_before_13(self, conn, table):
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            major = int(cur.fetchone()[0].split(".")[0])
            if major >= 13:
                pytest.skip("UPDATE ... RETURNING is available from MariaDB 13.0")
            with pytest.raises(pymysql.err.ProgrammingError) as exc_info:
                cur.execute(f"UPDATE {table} SET age = age + 1 RETURNING id")
        assert exc_info.value.args[0] == 1064