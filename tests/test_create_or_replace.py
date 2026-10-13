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


@pytest.fixture(autouse=True)
def cleanup(conn):
    yield
    with conn.cursor() as cur:
        cur.execute("DROP VIEW IF EXISTS cor_view")
        cur.execute("DROP TABLE IF EXISTS cor_child")
        cur.execute("DROP TABLE IF EXISTS cor_parent")
        cur.execute("DROP TABLE IF EXISTS cor_table")
    conn.commit()


def table_exists(conn, name):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = %s",
            (name,),
        )
        return cur.fetchone()[0] == 1


class TestCreateOrReplaceTable:
    def test_creates_table_when_missing(self, conn):
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS cor_table")
            cur.execute("CREATE OR REPLACE TABLE cor_table (id INT PRIMARY KEY)")
        assert table_exists(conn, "cor_table")

    def test_replaces_existing_table_and_drops_data(self, conn):
        with conn.cursor() as cur:
            cur.execute("CREATE OR REPLACE TABLE cor_table (id INT PRIMARY KEY)")
            cur.execute("INSERT INTO cor_table (id) VALUES (1), (2)")
            cur.execute(
                "CREATE OR REPLACE TABLE cor_table (id INT PRIMARY KEY, extra VARCHAR(10))"
            )
            cur.execute("SELECT COUNT(*) FROM cor_table")
            count = cur.fetchone()[0]
            cur.execute("SHOW COLUMNS FROM cor_table")
            columns = [row[0] for row in cur.fetchall()]
        assert count == 0
        assert columns == ["id", "extra"]

    def test_plain_create_fails_when_table_exists(self, conn):
        with conn.cursor() as cur:
            cur.execute("CREATE OR REPLACE TABLE cor_table (id INT PRIMARY KEY)")
            with pytest.raises(pymysql.err.MySQLError) as exc_info:
                cur.execute("CREATE TABLE cor_table (id INT PRIMARY KEY)")
        assert exc_info.value.args[0] == 1050


class TestCreateOrReplaceView:
    def test_view_can_be_replaced_with_new_definition(self, conn):
        with conn.cursor() as cur:
            cur.execute("CREATE OR REPLACE TABLE cor_table (id INT PRIMARY KEY, age INT)")
            cur.execute("INSERT INTO cor_table (id, age) VALUES (1, 26), (2, 24), (3, 22)")
            cur.execute("CREATE OR REPLACE VIEW cor_view AS SELECT id FROM cor_table WHERE age < 30")
            cur.execute("SELECT COUNT(*) FROM cor_view")
            first = cur.fetchone()[0]
            cur.execute("CREATE OR REPLACE VIEW cor_view AS SELECT id FROM cor_table WHERE age < 25")
            cur.execute("SELECT COUNT(*) FROM cor_view")
            second = cur.fetchone()[0]
        assert first == 3
        assert second == 2

    def test_plain_create_view_fails_when_view_exists(self, conn):
        with conn.cursor() as cur:
            cur.execute("CREATE OR REPLACE TABLE cor_table (id INT PRIMARY KEY)")
            cur.execute("CREATE OR REPLACE VIEW cor_view AS SELECT id FROM cor_table")
            with pytest.raises(pymysql.err.MySQLError) as exc_info:
                cur.execute("CREATE VIEW cor_view AS SELECT id FROM cor_table")
        assert exc_info.value.args[0] == 1050


class TestCreateOrReplaceForeignKeyLimit:
    def test_cannot_replace_table_referenced_by_foreign_key(self, conn):
        with conn.cursor() as cur:
            cur.execute("CREATE OR REPLACE TABLE cor_parent (id INT PRIMARY KEY)")
            cur.execute("INSERT INTO cor_parent (id) VALUES (1)")
            cur.execute(
                "CREATE OR REPLACE TABLE cor_child ("
                "id INT PRIMARY KEY, parent_id INT, "
                "FOREIGN KEY (parent_id) REFERENCES cor_parent(id))"
            )
            cur.execute("INSERT INTO cor_child (id, parent_id) VALUES (1, 1)")
            with pytest.raises(pymysql.err.MySQLError) as exc_info:
                cur.execute("CREATE OR REPLACE TABLE cor_parent (id INT PRIMARY KEY)")
        assert exc_info.value.args[0] == 1451