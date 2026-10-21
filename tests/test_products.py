import json
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


class TestIsJsonConstraint:
    def test_valid_json_object(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO products (name, metadata) VALUES (%s, %s)",
                ("Product A", '{"color": "red", "weight": 1.5}'),
            )
        conn.rollback()

    def test_valid_empty_object(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO products (name, metadata) VALUES (%s, %s)",
                ("Product B", '{}'),
            )
        conn.rollback()

    def test_valid_json_array(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO products (name, metadata) VALUES (%s, %s)",
                ("Product C", '[1, 2, 3]'),
            )
        conn.rollback()

    def test_invalid_json_plain_string(self, conn):
        with pytest.raises(pymysql.err.OperationalError):  #MariaDB raises error 4025
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO products (name, metadata) VALUES (%s, %s)",
                    ("Bad Product", 'not valid json'),
                )

    def test_invalid_json_missing_brace(self, conn):
        with pytest.raises(pymysql.err.OperationalError):
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO products (name, metadata) VALUES (%s, %s)",
                    ("Bad Product", '{"key": "value"'),
                )

    def test_invalid_json_bare_number_string(self, conn):
        with pytest.raises(pymysql.err.OperationalError):
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO products (name, metadata) VALUES (%s, %s)",
                    ("Bad Product", 'hello'),
                )


class TestInsertReturning:
    def test_returning_row_is_not_none(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO products (name, metadata) VALUES (%s, %s)"
                " RETURNING id, name, metadata",
                ("Widget", '{"key": "val"}'),
            )
            row = cur.fetchone()
        assert row is not None

    def test_returning_id_is_integer(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO products (name, metadata) VALUES (%s, %s)"
                " RETURNING id, name, metadata",
                ("Widget", '{"key": "val"}'),
            )
            row = cur.fetchone()
        assert isinstance(row[0], int)

    def test_returning_data_matches_inserted(self, conn):
        metadata = {"category": "electronics", "price": 99.9}
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO products (name, metadata) VALUES (%s, %s)"
                " RETURNING id, name, metadata",
                ("Gadget", json.dumps(metadata)),
            )
            row = cur.fetchone()
        assert row[1] == "Gadget"
        assert json.loads(row[2]) == metadata

    def test_returning_vs_select_same_data(self, conn):
        metadata = {"color": "blue", "weight": 2.0}
        with conn.cursor() as cur:
            cur.execute(  #classic: INSERT then SELECT
                "INSERT INTO products (name, metadata) VALUES (%s, %s)",
                ("Classic", json.dumps(metadata)),
            )
            classic_id = cur.lastrowid
            cur.execute(
                "SELECT id, name, metadata FROM products WHERE id = %s",
                (classic_id,),
            )
            classic_row = cur.fetchone()
            cur.execute(  #modern: single INSERT RETURNING
                "INSERT INTO products (name, metadata) VALUES (%s, %s)"
                " RETURNING id, name, metadata",
                ("Modern", json.dumps(metadata)),
            )
            returning_row = cur.fetchone()
        assert json.loads(classic_row[2]) == json.loads(returning_row[2])
        assert classic_row[1] == "Classic"
        assert returning_row[1] == "Modern"
